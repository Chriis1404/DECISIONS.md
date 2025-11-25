from fastapi import FastAPI, HTTPException, BackgroundTasks, Form
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, field_validator
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta
import os
import httpx
import logging
import redis
from enum import Enum
import asyncio
import uuid
import pika
import json
import time
from threading import Thread

# ===== LOGGING =====
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="EcoMarket Sucursal API",
    description="Gestión de inventario, ventas y registro de usuarios",
    version="7.1.0 (Fix UI)",
    docs_url="/docs",
    redoc_url=None
)

# ===== CONFIGURACIÓN (MODIFICADA para Modos 5 y 6) =====
BRANCH_ID = os.getenv("BRANCH_ID", "sucursal-demo")
CENTRAL_API_URL = os.getenv("CENTRAL_API_URL", "http://central:8000")

### Modo de notificación global (1-3: HTTP, 4: Redis, 5: RabbitMQ Directo, 6: RabbitMQ Fanout)
NOTIF_MODE = int(os.getenv("NOTIF_MODE", "6")) 

# Configuración Redis
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_QUEUE = os.getenv("REDIS_QUEUE", "sales_queue_redis")

# Constante del Producto Falso (Debe ser idéntica a la Central)
TEST_PRODUCT_ID = 999 # <<-- ¡DEFINICIÓN AGREGADA/CONFIRMADA!

def get_redis_client():
    return redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# Configuración RabbitMQ (Distinción Modo 5 y Modo 6)
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq") 
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "ecomarket_user") 
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "ecomarket_password") 

# Modo 5: Directo/Punto-a-Punto (P2P)
RABBITMQ_QUEUE_DIRECT = os.getenv("RABBITMQ_QUEUE_DIRECT", "ventas_central_direct") 
RABBITMQ_EXCHANGE_DIRECT = os.getenv("RABBITMQ_EXCHANGE_DIRECT", "notificaciones_direct") 

# Modo 6: Fanout/Pub/Sub (Ventas)
RABBITMQ_EXCHANGE_FANOUT = os.getenv("RABBITMQ_EXCHANGE_FANOUT", "ventas_global_fanout") 

# --- NUEVA CONFIGURACIÓN PARA USUARIOS (Taller 4) ---
EXCHANGE_USER_EVENTS = os.getenv("RABBITMQ_EXCHANGE_USERS", "user_events_fanout")

# ===== MODELOS (Añadimos el modelo de Notificación de la Central) =====
class Product(BaseModel):
    id: int
    name: str
    price: float
    stock: int

class SaleRequest(BaseModel):
    product_id: int
    quantity: int
    money_received: float

class SaleNotificationFromCentral(BaseModel):
    # Usamos este modelo para recibir la notificación completa de la Central
    sale_id: Optional[str] = None 
    branch_id: str
    product_id: int
    quantity_sold: int
    timestamp: Union[datetime, str]
    money_received: Optional[float] = None
    total_amount: float
    change: Optional[float] = None

    # --- INICIO DE LA CORRECCIÓN (Error 422) ---
    # El validador se actualiza para ser robusto (igual al de CentralAPI)
    @field_validator("timestamp", mode="before")
    def parse_timestamp(cls, v):
        if isinstance(v, str):
            # Añadir 'Z' si no tiene zona horaria para compatibilidad ISO
            if not v.endswith('Z') and '+' not in v and '-' not in v[10:]:
                 v += 'Z'
            try:
                # Intenta parsear el formato ISO estándar (con offset)
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                try:
                    # Fallback para formatos con microsegundos variables
                    return datetime.strptime(v, '%Y-%m-%dT%H:%M:%S.%f%z')
                except Exception:
                    # Fallback si todo lo demás falla
                    logger.warning(f"Timestamp no ISO recibido de Central, usando now(): {v}")
                    return datetime.now()
        return v
    # --- FIN DE LA CORRECCIÓN ---
    
    class Config:
        extra = "ignore" 

class SaleResponse(BaseModel):
    sale_id: str
    product_id: int
    product_name: str
    quantity_sold: int
    total_amount: float
    money_received: float
    change: float
    timestamp: datetime
    status: str
    
class UserCreate(BaseModel):
    nombre: str
    email: str

# ===== CIRCUIT BREAKER (se mantiene) =====
class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, failure_threshold=3, recovery_timeout=30):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitState.CLOSED
    
    async def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info("🔄 Circuito HALF_OPEN: probando llamada")
            else:
                raise Exception("Circuit breaker abierto")
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.error(f"❌ Circuito OPEN: alcanzado límite de fallos ({self.failure_threshold})")
    
    def _should_attempt_reset(self):
        if not self.last_failure_time:
            return False
        return datetime.now() >= self.last_failure_time + timedelta(seconds=self.recovery_timeout)

circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60)

# ===== INVENTARIO LOCAL Y HISTORIAL DE VENTAS (se mantiene) =====
local_inventory: Dict[int, Product] = {
    1: Product(id=1, name="Manzanas Orgánicas", price=2.50, stock=25),
    2: Product(id=2, name="Pan Integral", price=1.80, stock=15),
    3: Product(id=3, name="Leche Deslactosada", price=3.20, stock=8)
}
sales_history: List[SaleResponse] = []
user_db: Dict[str, UserCreate] = {} # Base de datos de usuarios simulada

# =================================================================
# === FUNCIONES DE NOTIFICACIÓN PARA VENTAS (Paso 1 al 6) =========
# =================================================================

# Nota: dispatch_notify_http no estaba en el código proporcionado, pero es
# una función requerida por circuit_breaker. Se asume su existencia para no romper la lógica.
async def dispatch_notify_http(sale: SaleResponse):
    """Auxiliar para el Circuit Breaker (asumiendo su implementación original)."""
    notification_data = {
        "sale_id": sale.sale_id, "branch_id": BRANCH_ID, "product_id": sale.product_id, 
        "quantity_sold": sale.quantity_sold, "money_received": sale.money_received, 
        "total_amount": sale.total_amount, "change": sale.change, 
        "timestamp": sale.timestamp.isoformat()
    }
    if NOTIF_MODE == 1:
        await notify_direct(notification_data)
    elif NOTIF_MODE == 2:
        await notify_retry_simple(notification_data)
    elif NOTIF_MODE == 3:
        await notify_backoff(notification_data)

# Modo 1, 2, 3: HTTP (Se mantienen)
async def notify_direct(notification: dict):
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.post(f"{CENTRAL_API_URL}/sale-notification", json=notification)
        resp.raise_for_status()
        logger.info("✅ Notificación enviada (HTTP 1/6: Directo)")

async def notify_retry_simple(notification: dict, retries: int = 3, delay_s: float = 1.0):
    async with httpx.AsyncClient(timeout=5.0) as client:
        last_exc = None
        for attempt in range(1, retries + 1):
            try:
                resp = await client.post(f"{CENTRAL_API_URL}/sale-notification", json=notification)
                if resp.status_code == 200:
                    logger.info(f"✅ Notificación enviada (HTTP 2/6) en intento {attempt}")
                    return
                else:
                    last_exc = Exception(f"Central API responded with status {resp.status_code}")
            except Exception as e:
                last_exc = e
                logger.warning(f"Intento {attempt} falló: {e}")
            await asyncio.sleep(delay_s)
        raise last_exc or Exception("Fallo con reintentos simples")

async def notify_backoff(notification: dict, max_retries: int = 5, base_delay: float = 1.0):
    async with httpx.AsyncClient(timeout=5.0) as client:
        last_exc = None
        for attempt in range(max_retries):
            try:
                resp = await client.post(f"{CENTRAL_API_URL}/sale-notification", json=notification)
                if resp.status_code == 200:
                    logger.info(f"✅ Notificación enviada (HTTP 3/6) en intento {attempt+1}")
                    return
                else:
                    last_exc = Exception(f"Central API responded with status {resp.status_code}")
            except Exception as e:
                last_exc = e
                logger.warning(f"Intento {attempt+1} falló: {e}")
            sleep_for = base_delay * (2 ** attempt)
            logger.info(f"⏳ Esperando {sleep_for}s antes del próximo intento")
            await asyncio.sleep(sleep_for)
        raise last_exc or Exception("Fallo con backoff exponencial")

# Modo 4: Redis Queue (Bloqueante ejecutado en hilo)
def send_notification_to_redis(sale: SaleResponse):
    notification = {
        "sale_id": sale.sale_id, "branch_id": BRANCH_ID, "product_id": sale.product_id, 
        "quantity_sold": sale.quantity_sold, "money_received": sale.money_received, 
        "total_amount": sale.total_amount, "change": sale.change, 
        "timestamp": sale.timestamp.isoformat()
    }
    try:
        r = get_redis_client()
        r.rpush(REDIS_QUEUE, json.dumps(notification))
        logger.info(f"✅ Notificación encolada en Redis (4/6): {REDIS_QUEUE}")
        return True
    except Exception as e:
        logger.error(f"❌ Fallo al enviar a Redis: {e}. Venta {sale.sale_id} NO encolada.")
        return False

def _redis_lpop_once():
    """Helper bloqueante: hace LPOP y devuelve el string (o None)."""
    try:
        r = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        raw = r.lpop(REDIS_QUEUE)
        return raw
    except Exception as e:
        logger.error(f"Redis LPOP fallo: {e}")
        return None

def _redis_rpush(value: str):
    """Helper bloqueante: rpush."""
    try:
        r = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        r.rpush(REDIS_QUEUE, value)
        return True
    except Exception as e:
        logger.error(f"Redis RPUSH fallo: {e}")
        return False

async def redis_queue_worker(poll_interval: float = 2.0):
    logger.info("🔁 Redis worker iniciado")
    while True:
        try:
            raw = await asyncio.to_thread(_redis_lpop_once)
            if raw:
                try:
                    notif = json.loads(raw)
                except Exception:
                    logger.error("❌ Mensaje Redis no decodable, saltando")
                    continue

                logger.info(f"🔄 Reintentando notificación desde Redis: sale_id={notif.get('sale_id')}")
                try:
                    await notify_backoff(notif)
                    logger.info(f"✅ Reenvío exitoso desde Redis: {notif.get('sale_id')}")
                except Exception as e:
                    logger.error(f"❌ Falló reenvío desde Redis: {e}. Re-enqueueando")
                    await asyncio.to_thread(_redis_rpush, json.dumps(notif))
                    await asyncio.sleep(5.0)
            else:
                await asyncio.sleep(poll_interval)
        except Exception as e:
            logger.error(f"Redis worker encontró error: {e}")
            await asyncio.sleep(5.0)

# Modo 5: RabbitMQ Publisher (Directo/Punto-a-Punto)
def publish_sale_direct(sale_data: dict, max_retries: int = 3):
    message = {
        **sale_data, "message_id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(), "source": BRANCH_ID, "mode": "Direct"
    }
    
    for attempt in range(max_retries):
        try:
            params = pika.ConnectionParameters(
                host=RABBITMQ_HOST, port=RABBITMQ_PORT, 
                credentials=pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS),
                heartbeat=600, blocked_connection_timeout=300,
            )
            
            with pika.BlockingConnection(params) as connection:
                channel = connection.channel()
                channel.exchange_declare(exchange=RABBITMQ_EXCHANGE_DIRECT, exchange_type='direct', durable=True)
                channel.basic_publish(
                    exchange=RABBITMQ_EXCHANGE_DIRECT, routing_key=RABBITMQ_QUEUE_DIRECT, 
                    body=json.dumps(message, default=str),
                    properties=pika.BasicProperties(delivery_mode=2), mandatory=True
                )
                logger.info(f"✅ Mensaje RabbitMQ Directo (5/6) publicado.")
                return True 

        except Exception as e:
            logger.error(f"❌ Intento {attempt + 1} falló (RabbitMQ Directo): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    logger.error(f"❌ Falló publicar a RabbitMQ Directo después de {max_retries} intentos. Venta: {sale_data.get('sale_id')}")
    return False

def send_notification_to_rabbitmq_direct(sale: SaleResponse):
    notification_data = {
        "sale_id": sale.sale_id, "branch_id": BRANCH_ID, "product_id": sale.product_id, 
        "quantity_sold": sale.quantity_sold, "money_received": sale.money_received, 
        "total_amount": sale.total_amount, "change": sale.change, 
        "timestamp": sale.timestamp.isoformat()
    }
    publish_sale_direct(notification_data)

# MODO 6: RabbitMQ Publisher (Pub/Sub Fanout - Ventas)
def publish_sale_fanout(sale_data: dict, max_retries: int = 3):
    message = {
        **sale_data, "message_id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(), "source": BRANCH_ID, "mode": "Fanout"
    }

    for attempt in range(max_retries):
        try:
            params = pika.ConnectionParameters(
                host=RABBITMQ_HOST, port=RABBITMQ_PORT, 
                credentials=pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS),
                heartbeat=600, blocked_connection_timeout=300,
            )
            
            with pika.BlockingConnection(params) as connection:
                channel = connection.channel()
                channel.exchange_declare(exchange=RABBITMQ_EXCHANGE_FANOUT, exchange_type='fanout', durable=True)
                channel.basic_publish(
                    exchange=RABBITMQ_EXCHANGE_FANOUT, routing_key='', 
                    body=json.dumps(message, default=str),
                    properties=pika.BasicProperties(delivery_mode=2), mandatory=True
                )
                logger.info(f"✅ Mensaje RabbitMQ Fanout (6/6) publicado.")
                return True 

        except Exception as e:
            logger.error(f"❌ Intento {attempt + 1} falló (RabbitMQ Fanout): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)

    logger.error(f"❌ Falló publicar a RabbitMQ Fanout después de {max_retries} intentos. Venta: {sale_data.get('sale_id')}")
    return False

def send_notification_to_fanout(sale: SaleResponse):
    notification_data = {
        "sale_id": sale.sale_id, "branch_id": BRANCH_ID, "product_id": sale.product_id, 
        "quantity_sold": sale.quantity_sold, "money_received": sale.money_received, 
        "total_amount": sale.total_amount, "change": sale.change, 
        "timestamp": sale.timestamp.isoformat()
    }
    publish_sale_fanout(notification_data)

# =================================================================
# === NUEVA FUNCIÓN: PUBLICACIÓN DE EVENTO USUARIOCREADO (Taller 4) ===
# =================================================================

def publish_user_created(user_data: dict):
    """Publica el evento UsuarioCreado a un Fanout Exchange dedicado."""
    message = {
        "id": str(uuid.uuid4()), # ID de usuario simulado
        "nombre": user_data['nombre'],
        "email": user_data['email'],
        "timestamp": datetime.now().isoformat(),
        "event_type": "UsuarioCreado",
        "source": BRANCH_ID
    }

    try:
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
        params = pika.ConnectionParameters(
            host=RABBITMQ_HOST, port=RABBITMQ_PORT, 
            credentials=credentials, heartbeat=600
        )
        
        with pika.BlockingConnection(params) as connection:
            channel = connection.channel()
            # Declarar el Exchange Fanout para USUARIOS
            channel.exchange_declare(
                exchange=EXCHANGE_USER_EVENTS, 
                exchange_type='fanout', 
                durable=True
            )
            
            channel.basic_publish(
                exchange=EXCHANGE_USER_EVENTS, 
                routing_key='', 
                body=json.dumps(message, default=str),
                properties=pika.BasicProperties(delivery_mode=2)
            )
            
            logger.info(f"✅ EVENTO PUBLICADO: UsuarioCreado para {user_data['email']} en exchange {EXCHANGE_USER_EVENTS}")
            return True 

    except Exception as e:
        logger.error(f"❌ Falló la publicación de UsuarioCreado: {e}")
        return False


# === Función principal de envío (ACTUALIZADA) ===
async def send_sale_notification(sale: SaleResponse):
    """
    Esta función decide la estrategia según NOTIF_MODE (para ventas).
    """
    if NOTIF_MODE in [1, 2, 3]:
        # Modos HTTP: usamos Circuit Breaker
        try:
            # Nota: dispatch_notify_http debe estar definida o importada para este bloque
            await circuit_breaker.call(dispatch_notify_http, sale)
        except Exception as e:
            logger.error(f"⚠️ Notificación HTTP fallida (CircuitBreaker): {e}")
    elif NOTIF_MODE == 4:
        # Redis: encolamos usando thread (no bloqueamos loop)
        await asyncio.to_thread(send_notification_to_redis, sale)
    elif NOTIF_MODE == 5:
        # RabbitMQ Directo (Punto-a-Punto)
        await asyncio.to_thread(send_notification_to_rabbitmq_direct, sale)
    elif NOTIF_MODE == 6:
        # RabbitMQ Fanout (Pub/Sub) - ¡NUEVO!
        await asyncio.to_thread(send_notification_to_fanout, sale)
    else:
        logger.error(f"⚠️ Modo de notificación {NOTIF_MODE} inválido.")

# =================================================================
# === RUTAS API (INTERFAZ MANTENIDA) ==============================
# =================================================================

# ===== VENTAS API (La interfaz de ruta y su cuerpo se mantiene) =====
@app.post("/sales", response_model=SaleResponse, tags=["Ventas"])
async def process_sale(sale_request: SaleRequest):
    if sale_request.product_id not in local_inventory:
        raise HTTPException(status_code=404, detail="Producto no disponible")
    product = local_inventory[sale_request.product_id]
    if product.stock < sale_request.quantity:
        raise HTTPException(status_code=400, detail=f"Stock insuficiente. Disponible: {product.stock}")
    
    product.stock -= sale_request.quantity
    sale_timestamp = datetime.now()
    total_amount = product.price * sale_request.quantity
    change = sale_request.money_received - total_amount

    sale_response = SaleResponse(
        sale_id=f"{BRANCH_ID}_{sale_timestamp.isoformat()}",
        product_id=product.id,
        product_name=product.name,
        quantity_sold=sale_request.quantity,
        total_amount=total_amount,
        money_received=sale_request.money_received,
        change=change,
        timestamp=sale_timestamp,
        status="completed"
    )
    sales_history.append(sale_response)

    # Ejecutar envío como tarea asíncrona (no blocking)
    asyncio.create_task(send_sale_notification(sale_response))

    return sale_response

# =======================================================
# === ENDPOINT DE SINCRONIZACIÓN DE HISTORIAL (CORREGIDO) === TALLER 7 APLICADO
# =======================================================
@app.post("/sync-sale-history", tags=["Sincronización"])
async def sync_sale_history(notification: SaleNotificationFromCentral):
    """
    Recibe la notificación de venta de la Central API (incluyendo las ventas de prueba)
    y la agrega al historial de ventas local para que aparezca en el dashboard.
    """
    
    # [CORRECCIÓN 1: FILTRO ANTI-DUPLICADOS]
    # Si la venta se originó en esta misma sucursal, ya la tenemos. No la duplicamos.
    if notification.branch_id == BRANCH_ID:
        logger.info(f"ℹ️ Historial: Venta propia ({notification.sale_id}) omitida. Ya está registrada.")
        return {"status": "success", "message": "Venta propia omitida."}
    
    # Buscamos el nombre del producto en el inventario local. Si no existe, usamos un nombre genérico.
    product_name = local_inventory.get(
        notification.product_id, 
        Product(id=0, name="PRODUCTO_EXTERNO", price=0, stock=0)
    ).name
    
    # Si es el producto falso (ID 999), ajustamos el nombre y la lógica de valores.
    if notification.product_id == TEST_PRODUCT_ID:
        product_name = "TEST VENTA"
        logger.info(f"🔄 Historial: Venta de prueba {notification.sale_id} registrada.")

    # Convertimos la notificación de Central a un SaleResponse para el historial local
    sale_response = SaleResponse(
        sale_id=notification.sale_id or f"SYNC-{uuid.uuid4().hex[:8]}",
        product_id=notification.product_id,
        product_name=product_name,
        quantity_sold=notification.quantity_sold,
        total_amount=notification.total_amount,
        money_received=notification.money_received,
        change=notification.change,
        timestamp=notification.timestamp,
        status="synced"
    )
    
    # Agregamos al historial
    sales_history.append(sale_response)
    
    # [CORRECCIÓN 2: ARREGLO DEL CRASH]
    # Usamos 'notification.branch_id' (que sí existe) en lugar de 'sale_response.branch_id'
    logger.info(f"✅ Historial sincronizado: {sale_response.sale_id} ({notification.branch_id})")
    return {"status": "success", "message": "Historial de venta sincronizado."}


# ===== NUEVA RUTA DE REGISTRO DE USUARIO (Taller 4) =====
@app.post("/users/register", tags=["Usuarios (Taller 4)"])
async def register_user_and_publish(
    # CRÍTICO: Recibe los campos del formulario con Form(...)
    nombre: str = Form(...),
    email: str = Form(...)
):
    """Endpoint para registrar un usuario y publicar el evento UsuarioCreado."""
    
    # Crea el objeto UserCreate internamente
    user = UserCreate(nombre=nombre, email=email)
    
    # 1. Simular registro en DB
    user_db[user.email] = user
    logger.info(f"👤 Usuario registrado localmente: {user.email}")
    
    # 2. Publicar el evento de usuario en background
    # Usamos asyncio.to_thread para correr la función bloqueante de RabbitMQ
    await asyncio.to_thread(publish_user_created, user.model_dump())
    
    # Retorna una respuesta HTML de éxito
    return HTMLResponse(content=f"""
        <h3>Usuario registrado!</h3>
        <p><b>{user.nombre} ({user.email})</b>. Evento UsuarioCreado publicado.</p>
        <a href="/dashboard">Volver al Dashboard</a>
    """)

@app.get("/register-user", response_class=HTMLResponse, tags=["Usuarios (Taller 4)"])
async def register_user_form():
    """Formulario para la interfaz del usuario."""
    return f"""
<html>
<head>
    <title>Registro de Usuario</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>body {{ padding: 20px; }}</style>
</head>
<body>
    <div class="container">
        <h1>Registro de Nuevo Usuario</h1>
        <p>Creación de un usuario. (Evento Pub/Sub independiente de las ventas)</p>
        <form action="/users/register" method="post">
            <div class="mb-3">
                <label for="nombre" class="form-label">Nombre:</label>
                <input type="text" id="nombre" name="nombre" class="form-control" required>
            </div>
            <div class="mb-3">
                <label for="email" class="form-label">Email:</label>
                <input type="email" id="email" name="email" class="form-control" required>
            </div>
            <button type="submit" class="btn btn-primary">Registrar y Publicar Evento</button>
        </form>
        <hr>
        <a href="/dashboard">Volver al Dashboard</a>
    </div>
</body>
</html>
"""

# ===== DASHBOARD (ESTABLE Y COMPLETO - Se mantiene) =====
@app.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard"])
async def dashboard():
    # Cálculo de métricas
    # Filtramos las ventas de prueba (ID 999) o sincronizadas (branch_id TEST) para la recaudación y el conteo.
    real_sales = [
        s for s in sales_history 
        if s.product_id != TEST_PRODUCT_ID and not s.sale_id.startswith("TEST") and not s.sale_id.startswith("SYNC")
    ]
    
    # Usamos len(real_sales) para el conteo de ventas.
    total_sales_count = len(real_sales) 
    total_products_count = sum(p.stock for p in local_inventory.values())
    total_revenue = sum(s.total_amount for s in real_sales)
    
    # Opciones del selector de producto para el modal
    options_html = "".join([f"<option value='{p.id}'>{p.name}</option>" for p in local_inventory.values()])

    # Tabla de inventario
    inventory_html = "".join([
        f"<tr><td>{p.id}</td><td>{p.name}</td><td>${p.price:.2f}</td><td>{p.stock}</td></tr>"
        for p in local_inventory.values()
    ])

    # Historial de ventas (Lógica Corregida y Optimizada)
    sales_html = "".join([
        (
            lambda s_id: 
            f"""
<tr class='{"table-info" if s.product_id == TEST_PRODUCT_ID or s.sale_id.startswith("TEST") or s.sale_id.startswith("SYNC") else ""}'>
    <td>{s.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</td>
    <td>{s_id.split('_')[0] if '_' in s_id else s_id}</td>
    <td>{s.product_name}</td>
    <td>{s.quantity_sold}</td>
    <td>${s.total_amount:.2f}</td>
    <td>${s.money_received:.2f}</td>
    <td>${s.change:.2f}</td>
    <td class='text-muted small'>{s_id[-12:]}</td>
</tr>
"""
        )(str(s.sale_id)) 
        
        for s in reversed(sales_history) # [CORRECCIÓN] Invertido para mostrar nuevos primero
    ])

    # Estado del Circuit Breaker
    cb_state = f"{circuit_breaker.state.value.upper()} (Fallos: {circuit_breaker.failure_count})" if NOTIF_MODE in [1,2,3] else "N/A"

    # --- INICIO DEL CÓDIGO HTML (Estructura de Layout Corregida) ---
    return f"""
<html>
<head>
<meta charset="utf-8">
<title>🟢EcoMarket Sucursal - {BRANCH_ID}</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
<style>
/* ... (CSS para Sucursal) ... */
body {{
    background-color: #FAFAFA;
    font-family: 'Segoe UI', sans-serif;
}}
.navbar {{
    background-color: #3BAF5D;
    color: white;
    padding: 0.8rem 1.5rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}}
.navbar-brand {{
    font-weight: 600;
    color: white !important;
}}
.metric-item {{
    text-align: center;
    background: rgba(255, 255, 255, 0.15);
    border-radius: 8px;
    padding: 0.4rem 0.8rem;
    font-size: 0.85rem;
    color: #fff;
    margin-right: 0.4rem;
    min-width: 90px;
    box-shadow: inset 0 0 6px rgba(255, 255, 255, 0.2);
}}
.metric-item h6 {{
    margin: 0;
    font-size: 0.75rem;
    font-weight: 500;
    opacity: 0.9;
}}
.metric-item p {{
    margin: 0;
    font-size: 1rem;
    font-weight: 600;
    color: rgba(255,255,255,0.9);
    text-shadow: 0 0 6px rgba(255,255,255,0.3);
}}

.mode-container {{
    display: flex;
    align-items: center;
    background: rgba(255,255,255,0.12);
    border-radius: 8px;
    padding: 4px 8px;
    margin-left: 1rem;
}}
.mode-label {{
    color: #fff;
    font-size: 0.8rem;
    margin-right: 4px;
}}
.mode-select {{
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.3);
    color: #fff;
    border-radius: 6px;
    padding: 2px 6px;
    font-size: 0.8rem;
    height: 28px;
}}

/* --- INICIO CORRECCIÓN 1: Color de Opciones --- */
.mode-select option {{
    color: #000;
    background: #fff;
}}
/* --- FIN CORRECCIÓN 1 --- */

.btn-main, .btn-sale {{
    border: 1px solid rgba(255,255,255,0.35);
    border-radius: 8px;
    font-weight: 600;
    padding: 6px 14px;
    color: #fff;
    transition: all 0.25s ease;
    font-size: 0.9rem;
}}
.btn-main {{ background-color: #2E8C4A; }}
.btn-sale {{ background-color: #1f6c36; }}
.btn-main:hover, .btn-sale:hover {{
    box-shadow: 0 0 14px rgba(255,255,255,0.6);
    transform: scale(1.03);
}}
#toast {{
    position: fixed;
    top: 20px;
    right: 20px;
    background: #3BAF5D;
    color: #fff;
    padding: 10px 20px;
    border-radius: 8px;
    display: none;
    z-index: 9999;
    font-weight: 500;
}}
.card {{
    border: none;
    border-radius: 10px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.05);
}}
.card-header {{
    background-color: #3BAF5D;
    color: white;
    font-weight: 600;
}}
.table thead th {{
    background-color: #2E8C4A;
    color: white;
    border: none;
    font-weight: 500;
}}
.table tbody tr:hover {{ background-color: #F0FFF3; }}
.footer {{
    text-align: center;
    margin-top: 2rem;
    color: #888;
    font-size: 0.85rem;
}}
</style>
</head>
<body>

<nav class="navbar navbar-expand-lg navbar-dark">
    <a class="navbar-brand" href="#">EcoMarket Sucursal: {BRANCH_ID}</a>
        <div class="ms-auto d-flex align-items-center">
        <div class="metrics-expanded d-flex">
            <div class="metric-item"><h6>Stock Total</h6><p>{total_products_count}</p></div>
            <div class="metric-item"><h6>Ventas</h6><p>{total_sales_count}</p></div>
            <div class="metric-item"><h6>Recaudación</h6><p>${total_revenue:.2f}</p></div>
            <div class="metric-item"><h6>Breaker</h6><p>{cb_state}</p></div>
        </div>
    <div class="mode-container">
        <span class="mode-label">Modo Central:</span>
        <form action="/set-mode" method="post" class="m-0">
            <select name="mode" class="mode-select" onchange="this.form.submit()">
            <option value="1" {"selected" if NOTIF_MODE==1 else ""}>1. HTTP Directo</option>
            <option value="2" {"selected" if NOTIF_MODE==2 else ""}>2. HTTP Reintentos</option>
            <option value="3" {"selected" if NOTIF_MODE==3 else ""}>3. HTTP Backoff</option>
            <option value="4" {"selected" if NOTIF_MODE==4 else ""}>4. Redis Queue</option>
            <option value="5" {"selected" if NOTIF_MODE==5 else ""}>5. RabbitMQ Directo (P2P)</option>
            <option value="6" {"selected" if NOTIF_MODE==6 else ""}>6. RabbitMQ Fanout (Pub/Sub)</option>
        </select>
        </form>
    </div>
    
    <button onclick="window.location.href='/register-user'" class="btn btn-main ms-2">Registrar Usuario</button> 
    <button class="btn btn-main ms-2" data-bs-toggle="modal" data-bs-target="#saleModal">Registrar Venta</button>
    <button class="btn btn-sale ms-2" onclick="window.location.reload()">Actualizar</button>
    </div>
</nav>

<div class="container mt-4">
    <div class="row g-4">
        <div class="col-md-5">
            <div class="card">
                <div class="card-header">Inventario Local</div>
                <div class="card-body p-0">
                    <div class="table-responsive" style="max-height:400px;">
                        <table class="table table-hover table-sm mb-0 align-middle">
                        <thead><tr><th>ID</th><th>Producto</th><th>Precio</th><th>Stock</th></tr></thead>
                            <tbody>{inventory_html}</tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
        <div class="col-md-7">
            <div class="card">
                <div class="card-header">Historial de Ventas</div>
                <div class="card-body p-0">
                    <div class="table-responsive" style="max-height:400px;">
                    <table class="table table-striped table-sm mb-0 align-middle">
                        <thead>
                            <tr><th>Fecha</th><th>Sucursal</th><th>Producto</th><th>Cant.</th><th>Total</th><th>Recibido</th><th>Cambio</th><th>ID Venta</th></tr>
                        </thead>
                    <tbody id="sales-body">{sales_html}</tbody>
                </table>
            </div>
        </div>
    </div>
    </div>
</div>

    <div class="footer"></div>
</div>

<div class="modal fade" id="saleModal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
            <div class="modal-header bg-success text-white">
                <h6 class="modal-title">Registrar Venta</h6>
            </div>    
                <form id="saleForm">
                    <div class="modal-body">
                        <div class="mb-2">
                            <label>Producto</label>
                            <select class="form-select" name="product_id" required>{options_html}</select>
                        </div>
                        <div class="mb-2">
                    <label>Cantidad</label>
                    <input type="number" class="form-control" name="quantity" value="1" min="1" required>
                </div>
            <div class="mb-2">  
        <label>Dinero Recibido</label>
        <input type="number" step="0.01" class="form-control" name="money_received" required>
    </div>
    </div>
    <div class="modal-footer">
        <button type="submit" class="btn btn-success w-100">Confirmar Venta</button>
    </div>
    </form>
    </div>
    </div>
</div>

<div id="toast"></div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
<script>
const toast = document.getElementById('toast');
document.getElementById('saleForm').addEventListener('submit', async (e) => {{
    e.preventDefault();
    const form = e.target;
    const data = new FormData(form);
  
    try {{
        const res = await fetch('/submit-sale', {{
            method: 'POST',
            body: data
        }});
    if (res.ok) {{
        showToast('✅ Venta registrada correctamente');
        const modal = bootstrap.Modal.getInstance(document.getElementById('saleModal'));
        modal.hide();
        setTimeout(() => window.location.reload(), 1200);
    }} else {{
        const text = await res.text();
        // Intenta extraer el error de la respuesta HTML si falla la venta
        const errorMatch = text.match(/<h3>❌\s*(.*?)<\/h3>/);
        const errorMessage = errorMatch ? errorMatch[1].trim() : 'Error desconocido';
        showToast(`❌ Error al registrar venta: ${{errorMessage}}`, true);
    }}
    }} catch (error) {{
    showToast('❌ Error de conexión al servidor.', true);
    }}
    }});

function showToast(msg, error=false) {{
    toast.textContent = msg;
    toast.style.background = error ? '#e74c3c' : '#3BAF5D';
    toast.style.display = 'block';
    setTimeout(() => toast.style.display = 'none', 3000);
}}
</script>
</body>
</html>
"""

# ===== CAMBIO DE MODO (Actualizado para incluir el modo 6) =====
@app.post("/set-mode", response_class=HTMLResponse, tags=["Dashboard"])
async def set_mode(mode: int = Form(...)):
    global NOTIF_MODE
    if mode not in [1, 2, 3, 4, 5, 6]:
        return HTMLResponse(f"<p>Modo {mode} no válido.</p><a href='/dashboard'>Volver</a>")
    NOTIF_MODE = mode
    logger.info(f"🔧 Modo cambiado a {NOTIF_MODE}")
    return HTMLResponse(f"<p>Modo cambiado a {NOTIF_MODE}</p><a href='/dashboard'>Volver</a>")


# ===== FORMULARIO DE VENTAS (se mantiene) =====
@app.post("/submit-sale", response_class=HTMLResponse, tags=["Dashboard"])
async def submit_sale_form(
    product_id: int = Form(...),
    quantity: int = Form(...),
    money_received: float = Form(...)
):
    if product_id not in local_inventory:
        return HTMLResponse(content="<h3>❌ Producto no encontrado.</h3><a href='/dashboard'>Volver</a>")

    product = local_inventory[product_id]
    if product.stock < quantity:
        return HTTPException(status_code=400, detail=f"Stock insuficiente. Disponible: {product.stock}")
    
    product.stock -= quantity
    sale_timestamp = datetime.now()
    total_amount = product.price * quantity
    change = money_received - total_amount

    sale = SaleResponse(
        sale_id=f"{BRANCH_ID}_{sale_timestamp.isoformat()}",
        product_id=product.id,
        product_name=product.name,
        quantity_sold=quantity,
        total_amount=total_amount,
        money_received=money_received,
        change=change,
        timestamp=sale_timestamp,
        status="completed"
    )
    sales_history.append(sale)

    # Ejecutar la notificación en background (usa send_sale_notification)
    asyncio.create_task(send_sale_notification(sale))

    return HTMLResponse(content=f"""
        <h3>✅ Venta registrada correctamente!</h3>
        <p>{quantity}x {product.name} vendidos por ${total_amount}</p>
        <p><b>Dinero recibido:</b> ${money_received}</p>
        <p><b>Cambio:</b> ${change}</p>
        <p><b>Modo de Notificación:</b> {NOTIF_MODE}</p>
        <a href="/dashboard">Volver al Dashboard</a>
    """)


# ===== RUTAS RESTANTES (se mantienen) =====
@app.get("/inventory", response_model=List[Product], tags=["Inventario"])
async def get_local_inventory():
    return list(local_inventory.values())

@app.get("/inventory/{product_id}", response_model=Product, tags=["Inventario"])
async def get_product(product_id: int):
    if product_id not in local_inventory:
        raise HTTPException(status_code=44, detail="Producto no encontrado")
    return local_inventory[product_id]
# =======================================================
# === SINCRONIZACIÓN DESDE CENTRAL (Altas y Actualizaciones)
# =======================================================

@app.post("/inventory", tags=["Inventario"])
async def add_product_from_central(product: Product):
    """
    Permite que la Central agregue o actualice un producto en la sucursal.
    """
    if product.id in local_inventory:
        local_inventory[product.id] = product
        logger.info(f"🔄 Producto actualizado desde Central: {product.name}")
        return {"status": "updated", "product": product}
    else:
        local_inventory[product.id] = product
        logger.info(f"🆕 Producto agregado desde Central: {product.name}")
        return {"status": "added", "product": product}


@app.put("/inventory/{product_id}", tags=["Inventario"])
async def update_product_from_central(product_id: int, product: Product):
    """
    Endpoint CRÍTICO: Recibe la actualización del stock desde la Central 
    (esto sucede después de una venta en cualquier sucursal).
    """
    if product_id not in local_inventory:
        # Aunque el producto no exista localmente, la Central quiere que exista/actualice su stock.
        # Lo agregamos o actualizamos de todas formas para mantener la consistencia.
        local_inventory[product_id] = product
        logger.info(f"♻️ Producto forzosamente actualizado/agregado por Central: {product.name}")
    
    local_inventory[product_id] = product
    logger.info(f"♻️ Producto actualizado por Central: {product.name} (Stock: {product.stock})")
    return {"status": "updated", "product": product}


@app.delete("/inventory/{product_id}", tags=["Inventario"])
async def delete_product_from_central(product_id: int):
    if product_id not in local_inventory:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    removed = local_inventory.pop(product_id)
    logger.info(f"🗑️ Producto eliminado por Central: {removed.name}")
    return {"status": "deleted", "product": removed.name}

@app.get("/sales/stats", tags=["Ventas"])
async def sales_stats():
    if not sales_history:
        return {"total_sales": 0, "total_revenue": 0}
    total_revenue = sum(s.total_amount for s in sales_history)
    return {
        "total_sales": len(sales_history),
        "total_revenue": round(total_revenue, 2),
        "average_sale": round(total_revenue / len(sales_history), 2)
    }

@app.get("/submit-sale-form", response_class=HTMLResponse)
async def submit_sale_page():
    options_html = "".join([f"<option value='{p.id}'>{p.name}</option>" for p in local_inventory.values()])
    return f"""
    <h1>Registrar Nueva Venta</h1>
    <form action="/submit-sale" method="post">
        <label>Producto:</label><br>
        <select name="product_id">{options_html}</select><br>
        <label>Cantidad:</label><br><input type="number" name="quantity" value="1" min="1" required><br>
        <label>Dinero Recibido:</label><br><input type="number" step="0.01" name="money_received" value="0.0" required><br><br>
        <button type="submit">Enviar Venta</button>
    </form>
    <a href="/dashboard">Volver</a>
    """

@app.get("/", tags=["General"])
async def root():
    return {
        "service": "🌿 EcoMarket Sucursal API",
        "branch_id": BRANCH_ID,
        "status": "operational",
        "total_products": len(local_inventory),
        "total_sales": len(sales_history),
        "current_notification_mode": NOTIF_MODE,
        "circuit_breaker_state": circuit_breaker.state.value if NOTIF_MODE in [1,2,3] else 'N/A',
        "circuit_failures": circuit_breaker.failure_count if NOTIF_MODE in [1,2,3] else 'N/A'
    }

# ===== STARTUP: lanzar worker de Redis para procesar cola (si Redis disponible) =====
@app.on_event("startup")
async def startup_event():
    # se lanza siempre para estar disponible si el modo cambia a 4
    asyncio.create_task(redis_queue_worker())
    logger.info("Startup completo - Redis worker lanzado (si Redis está accesible).")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
