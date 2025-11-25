import httpx
import asyncio
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime, timedelta
from enum import Enum

app = FastAPI(title="EcoMarket Sucursal 1 (Taller 3)")

# Configuración
CENTRAL_URL = "http://localhost:8000"
BRANCH_ID = "SUCURSAL_NORTE"

# --- PATRÓN CIRCUIT BREAKER (Implementación Manual) ---
class CircuitState(Enum):
    CLOSED = "closed"     # Todo bien, pasan las peticiones
    OPEN = "open"         # Fallo detectado, no intentar conectar
    HALF_OPEN = "half_open" # Probando si ya se arregló

class SimpleCircuitBreaker:
    def __init__(self):
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.threshold = 3          # Fallar 3 veces abre el circuito
        self.recovery_timeout = 10  # Esperar 10s antes de reintentar
        self.last_failure_time = None

    def can_request(self):
        if self.state == CircuitState.OPEN:
            # Si pasó el tiempo de espera, probamos de nuevo (Half-Open)
            if datetime.now() > self.last_failure_time + timedelta(seconds=self.recovery_timeout):
                self.state = CircuitState.HALF_OPEN
                print("🔄 [CB] Intentando reconexión (Half-Open)...")
                return True
            return False
        return True

    def record_success(self):
        if self.state != CircuitState.CLOSED:
            print("✅ [CB] Conexión restablecida. Circuito CERRADO.")
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        print(f"⚠️ [CB] Fallo de conexión ({self.failure_count}/{self.threshold})")
        if self.failure_count >= self.threshold:
            self.state = CircuitState.OPEN
            print("❌ [CB] Circuito ABIERTO. Se detienen notificaciones temporales.")

cb = SimpleCircuitBreaker()

# --- LÓGICA DE NEGOCIO ---

# Inventario Local (Autonomía / Offline-First)
# La sucursal tiene su propia copia de los datos para vender sin internet
local_inventory = {
    1: {"name": "Manzanas Orgánicas", "price": 2.50, "stock": 50},
    2: {"name": "Pan Integral", "price": 1.80, "stock": 20},
    3: {"name": "Leche Deslactosada", "price": 3.20, "stock": 10}
}

class SaleRequest(BaseModel):
    product_id: int
    quantity: int

async def notify_central_task(product_id: int, quantity: int):
    """Tarea en segundo plano: Intenta avisar a la central sin bloquear al cliente"""
    
    # 1. Verificar Circuit Breaker
    if not cb.can_request():
        print("⏹️ [SUCURSAL] Notificación omitida (Circuit Breaker Abierto). Se guardará en cola local (simulado).")
        return

    payload = {
        "branch_id": BRANCH_ID, 
        "product_id": product_id, 
        "quantity": quantity
    }
    
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            # Intentamos notificar
            resp = await client.post(f"{CENTRAL_URL}/sale-notification", json=payload)
            
            if resp.status_code == 200:
                cb.record_success()
                print("📤 [SUCURSAL] Notificación enviada con éxito a la Central.")
            else:
                print(f"⚠️ [SUCURSAL] La central respondió con error: {resp.status_code}")
                cb.record_failure()
                
    except Exception as e:
        print(f"🔥 [SUCURSAL] Error de conexión con Central: {e}")
        cb.record_failure()

@app.post("/sell")
async def process_sale(sale: SaleRequest, background_tasks: BackgroundTasks):
    # 1. Validación Local (Autonomía)
    p_id = sale.product_id
    
    if p_id not in local_inventory:
        raise HTTPException(status_code=404, detail="Producto no existe en inventario local")
    
    if local_inventory[p_id]["stock"] < sale.quantity:
        raise HTTPException(status_code=400, detail="Stock insuficiente en sucursal")

    # 2. Actualizar localmente (Inmediato - Baja Latencia)
    local_inventory[p_id]["stock"] -= sale.quantity
    total = local_inventory[p_id]["price"] * sale.quantity

    # 3. Notificación Asíncrona (Background Task)
    # Esto se ejecuta DESPUÉS de enviar el "return" al cliente
    background_tasks.add_task(notify_central_task, p_id, sale.quantity)

    return {
        "status": "success",
        "message": "Venta procesada localmente",
        "product": local_inventory[p_id]["name"],
        "total_price": total,
        "remaining_local_stock": local_inventory[p_id]["stock"],
        "sync_status": "Enviada a cola de notificaciones (Async)"
    }

if __name__ == "__main__":
    import uvicorn
    # Corremos en puerto 8001 para no chocar con la central
    uvicorn.run(app, host="0.0.0.0", port=8001)
