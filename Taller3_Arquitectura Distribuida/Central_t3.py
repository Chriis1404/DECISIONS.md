from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict

app = FastAPI(title="EcoMarket Central (Taller 3)")

# Modelo de datos para la notificación
class SaleNotification(BaseModel):
    branch_id: str
    product_id: int
    quantity: int

# Inventario Maestro en Memoria (Simulando la base de datos global)
central_inventory = {
    1: {"name": "Manzanas Orgánicas", "stock": 1000, "price": 2.50},
    2: {"name": "Pan Integral", "stock": 500, "price": 1.80},
    3: {"name": "Leche Deslactosada", "stock": 300, "price": 3.20}
}

@app.get("/")
def root():
    return {"service": "Central API v3.0", "status": "online"}

@app.get("/inventory")
def get_inventory():
    return central_inventory

@app.post("/sale-notification")
def receive_notification(notification: SaleNotification):
    """
    Recibe la notificación asíncrona de la sucursal.
    Este endpoint permite que la sucursal avise "ya vendí", sin bloquear al cliente.
    """
    p_id = notification.product_id
    qty = notification.quantity
    
    if p_id in central_inventory:
        # Actualizar Stock Global
        current_stock = central_inventory[p_id]["stock"]
        new_stock = max(0, current_stock - qty)
        central_inventory[p_id]["stock"] = new_stock
        
        print(f"📥 [CENTRAL] Notificación recibida de {notification.branch_id}:")
        print(f"   Vendidos {qty} de {central_inventory[p_id]['name']}. Stock restante: {new_stock}")
        
        return {"status": "synced", "new_global_stock": new_stock}
    
    # Si el producto no existe en la central, registramos el error pero no detenemos la venta ya hecha
    print(f"⚠️ [CENTRAL] Producto {p_id} reportado por sucursal no existe en catálogo central.")
    raise HTTPException(status_code=404, detail="Producto no encontrado en central")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
