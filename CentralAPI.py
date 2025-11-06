from fastapi import FastAPI, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse 
from pydantic import BaseModel, field_validator
from typing import Dict, List, Union, Optional
from datetime import datetime
import os
import logging
import httpx
import asyncio
import json
import uuid
import time
import pika
import redis 
from threading import Thread

# --- CONFIGURACIÓN Y MODELOS ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# [CONFIGURACIÓN REDIS]
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
TOTAL_USERS_KEY = "global_user_count" 
USERS_HASH_KEY = "global_user_data" 

# [NUEVO] Claves de Redis para el estado compartido
INVENTORY_HASH_KEY = "central_inventory"
SALES_LIST_KEY = "central_sales_history"
TEST_PRODUCT_ID = 999

def get_redis_client():
    """Retorna el cliente Redis, decodificando respuestas para obtener strings."""
    try:
        r = redis.StrictRedis(
            host=REDIS_HOST, 
            port=REDIS_PORT, 
            decode_responses=True, # Decodifica automáticamente de bytes a string
            socket_connect_timeout=1
        )
        r.ping() 
        return r
    except Exception as e:
        logger.error(f"❌ Fallo al conectar a Redis: {e}")
        return None 

SERVER_NAME = os.getenv("SERVER_NAME", "CENTRAL_UNNAMED")

app = FastAPI(
    title=f"🌿 EcoMarket Central API ({SERVER_NAME})",
    description="Servidor central que gestiona inventario maestro y recibe notificaciones de sucursales.",
    version="5.4.0 (Independent Stock)", # Versión actualizada
    docs_url="/docs",
    redoc_url="/redoc"
)

# --- Modelos Pydantic ---
class Product(BaseModel):
    id: int
    name: str
    price: float
    stock: int

class SaleNotification(BaseModel):
    sale_id: Optional[str] = None 
    branch_id: str
    product_id: int
    quantity_sold: int
    timestamp: Union[datetime, str]
    money_received: Optional[float] = None
    total_amount: float
    change: Optional[float] = None

    @field_validator("timestamp", mode="before")
    def parse_timestamp(cls, v):
        if isinstance(v, str):
            # Añadir 'Z' si no tiene zona horaria para compatibilidad ISO
            if not v.endswith('Z') and '+' not in v and '-' not in v[10:]:
                 v += 'Z'
            try:
                # Intenta parsear el formato ISO estándar
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                try:
                    # Fallback para formatos con microsegundos variables
                    return datetime.strptime(v, '%Y-%m-%dT%H:%M:%S.%f%z')
                except Exception:
                    logger.warning(f"Timestamp no ISO, usando now(): {v}")
                    return datetime.now() # O maneja el error como prefieras
        return v
    
    class Config:
        extra = "ignore" 

# [MODIFICADO] Esto es ahora solo el inventario *inicial*
initial_inventory: Dict[int, Product] = {
    1: Product(id=1, name="Manzanas Orgánicas", price=2.50, stock=100),
    2: Product(id=2, name="Pan Integral", price=1.80, stock=50),
    3: Product(id=3, name="Leche Deslactosada", price=3.20, stock=30),
    4: Product(id=4, name="Café Premium", price=8.90, stock=25),
    5: Product(id=5, name="Quinoa", price=12.50, stock=15),
    TEST_PRODUCT_ID: Product(id=TEST_PRODUCT_ID, name="PRODUCTO DE TEST (NO CONTABILIZA)", price=0.00, stock=0) 
}

# =================================================================
# === FUNCIONES DE ACCESO A DATOS (REDIS) ========================
# =================================================================

def initialize_redis_data():
    """Inicializa contadores y el inventario central en Redis si no existen."""
    r = get_redis_client()
    if not r:
        logger.error(f"❌ [{SERVER_NAME}] Redis no disponible. No se puede inicializar el estado.")
        return

    try:
        if r.get(TOTAL_USERS_KEY) is None:
             r.set(TOTAL_USERS_KEY, 0)
        
        if not r.exists(INVENTORY_HASH_KEY):
            logger.info(f"ℹ️ [{SERVER_NAME}] Inventario vacío en Redis. Poblando con datos iniciales...")
            pipeline = r.pipeline()
            for prod_id, product in initial_inventory.items():
                pipeline.hset(INVENTORY_HASH_KEY, str(prod_id), product.model_dump_json())
            pipeline.execute()
            logger.info(f"✅ [{SERVER_NAME}] Inventario central poblado en Redis con {len(initial_inventory)} productos.")
        else:
            logger.info(f"✅ [{SERVER_NAME}] Inventario central ya existe en Redis. Omitiendo población.")
            
    except Exception as e:
        logger.error(f"❌ [{SERVER_NAME}] Fallo al inicializar data en Redis: {e}")

async def get_all_products_from_redis() -> List[Product]:
    """Obtiene todos los productos del Hash de Redis."""
    r = get_redis_client()
    if not r: return []
    try:
        products_json = await asyncio.to_thread(r.hvals, INVENTORY_HASH_KEY)
        products = [Product(**json.loads(p_json)) for p_json in products_json]
        return products
    except Exception as e:
        logger.error(f"Error al leer inventario de Redis: {e}")
        return []

async def get_product_from_redis(product_id: int) -> Optional[Product]:
    """Obtiene un solo producto de Redis."""
    r = get_redis_client()
    if not r: return None
    try:
        product_json = await asyncio.to_thread(r.hget, INVENTORY_HASH_KEY, str(product_id))
        if product_json:
            return Product(**json.loads(product_json))
    except Exception as e:
        logger.error(f"Error al leer producto {product_id} de Redis: {e}")
    return None

async def save_product_to_redis(product: Product) -> bool:
    """Guarda/Actualiza un producto en el Hash de Redis."""
    r = get_redis_client()
    if not r: return False
    try:
        await asyncio.to_thread(r.hset, INVENTORY_HASH_KEY, str(product.id), product.model_dump_json())
        return True
    except Exception as e:
        logger.error(f"Error al guardar producto {product.id} en Redis: {e}")
        return False

async def delete_product_from_redis(product_id: int) -> bool:
    """Elimina un producto del Hash de Redis."""
    r = get_redis_client()
    if not r: return False
    try:
        await asyncio.to_thread(r.hdel, INVENTORY_HASH_KEY, str(product_id))
        return True
    except Exception as e:
        logger.error(f"Error al eliminar producto {product_id} de Redis: {e}")
        return False

async def get_sales_from_redis(limit: int = 50) -> List[SaleNotification]:
    """Obtiene las últimas 'limit' ventas de la Lista de Redis."""
    r = get_redis_client()
    if not r: return []
    try:
        sales_json = await asyncio.to_thread(r.lrange, SALES_LIST_KEY, -limit, -1)
        sales = [SaleNotification(**json.loads(s_json)) for s_json in sales_json]
        return sales
    except Exception as e:
        logger.error(f"Error al leer ventas de Redis: {e}")
        return []

async def save_sale_to_redis(notification: SaleNotification):
    """Guarda una notificación de venta en la Lista de Redis."""
    r = get_redis_client()
    if not r: return False
    try:
        pipeline = r.pipeline()
        
        # [CORRECCIÓN V5.2] .model_dump_json() no acepta 'mode'. 
        pipeline.rpush(SALES_LIST_KEY, notification.model_dump_json()) 
        
        pipeline.ltrim(SALES_LIST_KEY, -1000, -1) 
        await asyncio.to_thread(pipeline.execute)
        return True
    except Exception as e:
        logger.error(f"Error al guardar venta {notification.sale_id} en Redis: {e}")
        return False

# -----------------------------------------------------------------

# --- FUNCIONES ASÍNCRONAS DE SINCRONIZACIÓN ---
async def sync_with_branches(method: str, endpoint: str, data: dict = None):
    branch_urls_str = os.getenv("BRANCHES", "http://sucursal-demo:8002")
    branch_urls = branch_urls_str.split(",")
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        tasks = []
        for branch_url in branch_urls:
            url = f"{branch_url}{endpoint}"
            try:
                if method == "POST":
                    tasks.append(client.post(url, json=data))
                elif method == "PUT":
                    tasks.append(client.put(url, json=data))
                elif method == "DELETE":
                    tasks.append(client.delete(url))
            except Exception as e:
                logger.error(f"❌ [{SERVER_NAME}] Error creando tarea de sincronización para {url}: {e}")
                
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for branch_url, res in zip(branch_urls, results):
            if isinstance(res, Exception):
                logger.error(f"❌ [{SERVER_NAME}] Error al sincronizar con {branch_url}: {res}")
            elif res and res.status_code >= 400:
                logger.error(f"⚠️ [{SERVER_NAME}] Sucursal {branch_url} devolvió {res.status_code}")
            else:
                logger.info(f"✅ [{SERVER_NAME}] Sincronizado con {branch_url} ({endpoint})")


# --- INICIO DE LA CORRECCIÓN (Stock Independiente) ---
async def sync_sale_updates(notification_data: dict, product_to_sync: Optional[dict] = None, old_stock: Optional[int] = None):
    """
    CORREGIDO: Esta función ahora SOLO sincroniza el historial de ventas
    y YA NO sobrescribe el stock de las sucursales.
    """
    notification = SaleNotification(**notification_data)

    # 1. Sincronizar historial (para que la sucursal vea la venta en su dashboard)
    await sync_with_branches("POST", "/sync-sale-history", notification_data)
    logger.info(f"✅ [{SERVER_NAME}] Tarea de sincronización de historial ({notification.sale_id}) ejecutada.")

    # 2. El bloque que enviaba el "PUT /inventory/{product_id}" ha sido eliminado.
    
    is_test_sale = notification.branch_id.startswith("TEST") or notification.product_id == TEST_PRODUCT_ID
    stock_changed = product_to_sync and old_stock is not None and product_to_sync.get('stock') != old_stock

    if product_to_sync and not is_test_sale and stock_changed:
        product_name = product_to_sync.get('name', 'Producto Desconocido')
        logger.info(f"ℹ️ [{SERVER_NAME}] Stock central de {product_name} actualizado. NO se sincroniza stock a sucursales.")
    elif is_test_sale:
        logger.warning(f"⚠️ [{SERVER_NAME}] Es venta de prueba, se omite la sincronización PUT de Stock.")
# --- FIN DE LA CORRECCIÓN ---


# --- LÓGICA DE NEGOCIO (Refactorizada para Redis) ---
# [CORRECCIÓN V5.1] Convertida a 'async def'
async def process_sale_notification(notification_data: dict):
    """
    Procesa la venta y la guarda en Redis.
    Esta función AHORA ES ASÍNCRONA.
    """
    try:
        # --- INICIO DE LA CORRECCIÓN (Triplicación / Idempotencia) ---
        r = get_redis_client()
        sale_id = notification_data.get('sale_id')
        
        if not sale_id:
            logger.warning(f"⚠️ [{SERVER_NAME}] Venta recibida sin sale_id, no se puede garantizar idempotencia. Procesando...")
        elif r:
            lock_key = f"sale_lock:{sale_id}"
            # Intentamos establecer el lock (SET if Not Exists) con 1h de expiración
            try:
                is_first_instance = await asyncio.to_thread(r.set, lock_key, "processed", nx=True, ex=3600)
                if not is_first_instance:
                    logger.info(f"ℹ️ [{SERVER_NAME}] Venta {sale_id} ya está siendo procesada o fue procesada por otra instancia. Omitiendo.")
                    return "skipped" # Devolvemos "skipped" para manejarlo en el endpoint HTTP
            except Exception as e:
                logger.error(f"❌ [{SERVER_NAME}] Error al verificar el lock de Redis para {sale_id}: {e}. Procesando de todas formas (riesgo de duplicado).")
        # --- FIN DE LA CORRECCIÓN ---

        notification = SaleNotification(**notification_data)
        product = await get_product_from_redis(notification.product_id)

        if not product:
            logger.error(f"❌ [{SERVER_NAME}] Venta fallida: Producto ID {notification.product_id} no encontrado en Redis.")
            return None # Devolvemos None para "producto no encontrado"

        old_stock = product.stock
        product_to_sync = None 
        is_test_sale = notification.branch_id.startswith("TEST") or notification.product_id == TEST_PRODUCT_ID
        
        if not is_test_sale:
            product.stock = max(0, product.stock - notification.quantity_sold)
            logger.info(f"🟢 [{SERVER_NAME}] [VENTA PROCESADA] {notification.branch_id} - {notification.quantity_sold}x {product.name} | Stock: {product.stock}")
            
            if product.stock != old_stock:
                 await save_product_to_redis(product)
                 product_to_sync = product.model_dump()
        else:
            logger.warning(f"⚠️ [{SERVER_NAME}] [TEST VENTA] {notification.branch_id} - {notification.quantity_sold}x {product.name} | Stock CENTRAL NO MODIFICADO.")
            if notification.product_id == TEST_PRODUCT_ID:
                 notification.total_amount = 0.0
                 notification.money_received = 0.0
                 notification.change = 0.0
        
        # Guardar la venta en Redis
        await save_sale_to_redis(notification)
        
        # Sincronizar con sucursales
        try:
            # [CORRECCIÓN V5.1] 'await' directo, sin 'asyncio.run()'
            await sync_sale_updates(notification.model_dump(mode='json'), product_to_sync, old_stock)
        except Exception as e:
             logger.error(f"❌ [{SERVER_NAME}] Fallo en la sub-tarea de sincronización: {e}")
        
        return product.stock # Devolvemos el stock (int) en éxito
    except Exception as e:
        logger.error(f"❌ [{SERVER_NAME}] Error al procesar la venta: {e}. Datos: {notification_data}")
        return None # Devolvemos None en error
        
# --- LÓGICA DE PROCESAMIENTO DE USUARIOS (Refactorizada para async) ---
async def process_user_created_event_async(message_data: dict, worker_name: str):
    """Versión asíncrona para ser llamada desde el callback de RabbitMQ."""
    if message_data.get('event_type') != 'UsuarioCreado':
        return 
    
    r = get_redis_client()
    
    if worker_name == "Notificaciones":
        logger.info(f"📧 [{SERVER_NAME} - NOTIFICACIONES] Enviando email simulado a {message_data.get('email')}")
        await asyncio.sleep(0.5) 
        logger.info(f"✅ [{SERVER_NAME}] Email simulado completado.")
    
    elif worker_name == "Estadisticas":
        if r:
            # --- INICIO DE LA CORRECCIÓN (Idempotencia de Usuarios) ---
            user_email = message_data.get('email')
            message_id = message_data.get('id') # El 'id' (UUID) del mensaje de usuario
            
            if not message_id:
                logger.warning(f"⚠️ [{SERVER_NAME}] Evento de usuario para {user_email} sin 'id'. No se puede garantizar idempotencia. Procesando...")
            else:
                lock_key = f"user_event_lock:{message_id}"
                try:
                    # Intentamos establecer el lock (SET if Not Exists) con 1h de expiración
                    is_first_instance = await asyncio.to_thread(r.set, lock_key, "processed", nx=True, ex=3600)
                    if not is_first_instance:
                        logger.info(f"ℹ️ [{SERVER_NAME}] Evento de usuario {message_id} ({user_email}) ya fue procesado por otra instancia. Omitiendo estadísticas.")
                        return # No procesar de nuevo
                except Exception as e:
                    logger.error(f"❌ [{SERVER_NAME}] Error al verificar lock de Redis para {message_id}: {e}. Procesando de todas formas (riesgo de duplicado).")
            # --- FIN DE LA CORRECCIÓN ---

            try:
                # Esta lógica ahora solo la corre la primera instancia
                await asyncio.to_thread(r.incr, TOTAL_USERS_KEY)
                current_total = await asyncio.to_thread(r.get, TOTAL_USERS_KEY)
                # HSET es idempotente por naturaleza (sobrescribe la misma clave)
                await asyncio.to_thread(r.hset, USERS_HASH_KEY, user_email, json.dumps(message_data))
                logger.info(f"🎁 [{SERVER_NAME} - ESTADÍSTICAS] Nuevo usuario ({message_data.get('nombre')}) guardado en Redis. Total Global: {current_total}")
            except Exception as e:
                logger.error(f"Error guardando usuario en Redis: {e}")
        else:
            logger.warning(f"⚠️ [{SERVER_NAME} - ESTADÍSTICAS] Redis no disponible. El contador de usuarios no se incrementó.")
    
    else:
        logger.warning(f"Worker desconocido '{worker_name}' procesando evento de usuario.")
# -----------------------------------------------------------------

# --- WORKERS Y AMQP (Modificado para llamar a 'asyncio.run') ---
def callback(ch, method, properties, body):
    try:
        notification_data = json.loads(body.decode())
        exchange = method.exchange
        
        # [CORRECCIÓN V5.1] Usar asyncio.run() para llamar a las funciones async
        if exchange in [EXCHANGE_DIRECT, EXCHANGE_FANOUT]:
            logger.info(f"📥 [{SERVER_NAME}] Mensaje de Venta recibido del exchange {exchange}")
            asyncio.run(process_sale_notification(notification_data))
        
        elif exchange == EXCHANGE_USER_EVENTS:
            queue_name = method.consumer_tag 
            worker_name = "Notificaciones" if QUEUE_USER_NOTIFS in queue_name else "Estadisticas"
            logger.info(f"📥 [{SERVER_NAME} - USUARIOS - {worker_name}] Evento recibido. Procesando acción...")
            asyncio.run(process_user_created_event_async(notification_data, worker_name))

        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as e:
        logger.error(f"❌ [{SERVER_NAME}] Error al procesar mensaje de RabbitMQ: {e}")
        ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False) 


def start_rabbitmq_worker(queue_name: str, exchange_name: str, exchange_type: str, routing_key: str):
    logger.info(f"✨ [{SERVER_NAME}] Iniciando Worker para {exchange_name} ({exchange_type.upper()}). Cola: {queue_name}")
    while True:
        try:
            credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
            params = pika.ConnectionParameters(
                host=RABBITMQ_HOST, 
                port=5672,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300,
            )
            connection = pika.BlockingConnection(params)
            channel = connection.channel()

            channel.exchange_declare(exchange=exchange_name, exchange_type=exchange_type, durable=True)
            
            consumer_tag = queue_name
            queue_name_bound = queue_name

            if exchange_name == EXCHANGE_FANOUT or exchange_name == EXCHANGE_USER_EVENTS:
                result = channel.queue_declare(queue=f"{queue_name}_{SERVER_NAME}_{uuid.uuid4().hex[:6]}", exclusive=True, durable=False)
                queue_name_bound = result.method.queue
                consumer_tag = queue_name_bound 
            elif exchange_name == EXCHANGE_DIRECT:
                channel.queue_declare(queue=queue_name, durable=True)
                queue_name_bound = queue_name
                consumer_tag = queue_name
            
            channel.queue_bind(
                exchange=exchange_name, queue=queue_name_bound, routing_key=routing_key
            )

            channel.basic_consume(
                queue=queue_name_bound, 
                on_message_callback=callback,
                auto_ack=False,
                consumer_tag=consumer_tag
            )

            logger.info(f'✅ [{SERVER_NAME}] Worker {consumer_tag} listo. Consumiendo...')
            channel.start_consuming()

        except pika.exceptions.AMQPConnectionError as e:
            logger.error(f"❌ [{SERVER_NAME}] Fallo en la conexión a RabbitMQ (Worker {queue_name}): {e}. Reintentando en 5s...")
            time.sleep(5)
        except pika.exceptions.ChannelClosedByBroker as e:
            logger.error(f"❌ [{SERVER_NAME}] Canal cerrado por el broker (Worker {queue_name}): {e}. Reintento de reconexión.")
            time.sleep(5)
        except Exception as e:
            logger.error(f"❌ [{SERVER_NAME}] Error crítico en el worker de RabbitMQ ({queue_name}): {e}. Terminando thread.")
            break

@app.on_event("startup")
async def startup_event():
    logger.info(f"🚀 [{SERVER_NAME}] Iniciando Central API con 4 Workers (Ventas y Usuarios)...")
    Thread(target=initialize_redis_data, daemon=True).start()
    
    global BRANCHES, RABBITMQ_HOST, RABBITMQ_USER, RABBITMQ_PASS, QUEUE_DIRECT, EXCHANGE_DIRECT, QUEUE_FANOUT, EXCHANGE_FANOUT, EXCHANGE_USER_EVENTS, QUEUE_USER_NOTIFS, QUEUE_USER_STATS
    BRANCHES = os.getenv("BRANCHES", "http://sucursal-demo:8002").split(",")
    RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
    RABBITMQ_USER = os.getenv("RABBITMQ_USER", "ecomarket_user")
    RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "ecomarket_password")
    QUEUE_DIRECT = os.getenv("RABBITMQ_QUEUE_DIRECT", "ventas_central_direct") 
    EXCHANGE_DIRECT = os.getenv("RABBITMQ_EXCHANGE_DIRECT", "notificaciones_direct") 
    QUEUE_FANOUT = "ventas_central_fanout"
    EXCHANGE_FANOUT = os.getenv("RABBITMQ_EXCHANGE_FANOUT", "ventas_global_fanout") 
    EXCHANGE_USER_EVENTS = os.getenv("RABBITMQ_EXCHANGE_USERS", "user_events_fanout")
    QUEUE_USER_NOTIFS = os.getenv("RABBITMQ_QUEUE_NOTIFS", "user_notifs_central")
    QUEUE_USER_STATS = os.getenv("RABBITMQ_QUEUE_STATS", "user_stats_central")
    
    Thread(target=start_rabbitmq_worker, args=(QUEUE_DIRECT, EXCHANGE_DIRECT, 'direct', QUEUE_DIRECT), daemon=True).start()
    Thread(target=start_rabbitmq_worker, args=(QUEUE_FANOUT, EXCHANGE_FANOUT, 'fanout', ''), daemon=True).start()
    Thread(target=start_rabbitmq_worker, args=(QUEUE_USER_NOTIFS, EXCHANGE_USER_EVENTS, 'fanout', ''), daemon=True).start()
    Thread(target=start_rabbitmq_worker, args=(QUEUE_USER_STATS, EXCHANGE_USER_EVENTS, 'fanout', ''), daemon=True).start()
    logger.info(f"✅ [{SERVER_NAME}] 4 Workers de RabbitMQ (Ventas y Usuarios) iniciados.")
# -----------------------------------------------------------------

# --- ENDPOINTS (Refactorizados para Redis) ---

@app.get("/", tags=["General"])
async def root():
    inventory = await get_all_products_from_redis()
    sales_count = get_redis_client().llen(SALES_LIST_KEY) if get_redis_client() else 0
    return {
        "service": "🌿 EcoMarket Central API",
        "server_name": SERVER_NAME, 
        "status": "operational",
        "total_products": len(inventory),
        "total_notifications": sales_count
    }

@app.get("/inventory", response_model=List[Product], tags=["Inventario"])
async def get_inventory():
    return await get_all_products_from_redis()

@app.post("/inventory", response_model=Product, tags=["Inventario"])
async def add_product(product: Product):
    existing_product = await get_product_from_redis(product.id)
    if existing_product:
        raise HTTPException(status_code=400, detail="El producto ya existe")
    
    await save_product_to_redis(product)
    asyncio.create_task(sync_with_branches("POST", "/inventory", product.model_dump())) 
    return product

@app.put("/inventory/{product_id}", response_model=Product, tags=["Inventario"])
async def update_product(product_id: int, product: Product):
    if product_id != product.id:
        raise HTTPException(status_code=400, detail="El ID del producto en la URL y en el cuerpo no coinciden.")
    
    existing_product = await get_product_from_redis(product_id)
    if not existing_product:
        logger.warning(f"Producto {product_id} no encontrado para PUT, se creará.")
    
    await save_product_to_redis(product)
    asyncio.create_task(sync_with_branches("PUT", f"/inventory/{product_id}", product.model_dump()))
    return product

@app.delete("/inventory/{product_id}", tags=["Inventario"])
async def delete_product(product_id: int):
    removed = await get_product_from_redis(product_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    await delete_product_from_redis(product_id)
    asyncio.create_task(sync_with_branches("DELETE", f"/inventory/{product_id}"))
    return {"removed": removed.name, "id": removed.id}

@app.post("/sale-notification", tags=["Ventas"])
async def sale_notification(notification: SaleNotification):
    # --- INICIO DE LA CORRECCIÓN (Manejo de Idempotencia) ---
    result = await process_sale_notification(notification.model_dump())
    
    if result is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    elif result == "skipped":
        # Si la venta ya fue procesada (idempotencia), devolvemos un 409 Conflict
        raise HTTPException(status_code=409, detail="Conflicto: Esta venta (sale_id) ya ha sido registrada.")
    
    # Si no, result es updated_stock (int)
    return {"message": "Venta registrada correctamente", "updated_stock": result}
    # --- FIN DE LA CORRECCIÓN ---
# -----------------------------------------------------------------

# =================================================================
# === SIMULACIÓN DE PLANTILLAS HTML (Modificadas para Redis) ======
# =================================================================

DASHBOARD_HTML_TEMPLATE = """
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>🔴EcoMarket Central - {SERVER_NAME_TITLE}</title> <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
<style>
body {{ background-color: #FAFAFA; font-family: 'Segoe UI', sans-serif; color: #333; }}
.navbar {{ 
    background-color: #ED4040; color: white; padding: 0.8rem 1.5rem; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08); 
}}
.navbar-brand {{ font-weight: 600; font-size: 1.3rem; color: white !important; }}
.metric-item {{ 
    text-align: center; background: rgba(255, 255, 255, 0.15); border-radius: 8px; 
    padding: 0.4rem 0.8rem; font-size: 0.85rem; color: #fff; min-width: 90px; 
    box-shadow: inset 0 0 6px rgba(255, 255, 255, 0.2); 
}}
.metric-item h6 {{ margin: 0; font-size: 0.75rem; font-weight: 500; opacity: 0.9; }}
.metric-item p {{ margin: 0; font-size: 1rem; font-weight: 600; color: rgba(255,255,255,0.9); }}
.btn-main, .btn-sale {{
    border: 1px solid rgba(255,255,255,0.35); border-radius: 8px; font-weight: 600;
    padding: 6px 14px; color: #fff; transition: all 0.25s ease; font-size: 0.9rem;
}}
.btn-main {{ background-color: #F06060; }}
.btn-sale {{ background-color: #ED4040; }}
.btn-main:hover, .btn-sale:hover {{
    box-shadow: 0 0 14px rgba(255,255,255,0.6); transform: scale(1.03);
}}
.card {{ border: none; border-radius: 12px; box-shadow: 0 2px 6px rgba(0,0,0,0.06); background-color: #fff; }}
.card-header.bg-coral {{ background-color: #F06060; color: #fff; font-weight: 600; display: flex; justify-content: space-between; align-items: center; }}
.card-header.bg-intense {{ background-color: #ED4040; color: #fff; font-weight: 600; }}
.table thead th {{ background-color: #ED4040; color: white; border: none; font-weight: 500; }}
.table tbody tr:hover {{ background-color: #FFF0F0; }}
.bg-stats {{ background-color: #007bff; }}
#toast {{
    position: fixed; top: 20px; right: 20px; min-width: 250px; padding: 10px 20px; border-radius: 8px; 
    color: white; font-weight: 600; z-index: 1050; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    display: none; 
}}
#toast.success {{ background-color: #4CAF50; }}
#toast.error {{ background-color: #ED4040; }}
#toast.warning {{ background-color: #FFC107; color: #333; }}
</style>
</head>
<body>
<nav class="navbar navbar-expand-lg navbar-dark">
    <a class="navbar-brand" href="#">EcoMarket Central API - {SERVER_NAME_TITLE}</a> <div class="ms-auto d-flex align-items: center">
        <div class="metrics-expanded d-flex me-4"> 
            <div class="metric-item me-3"><h6>Productos</h6><p>{total_products_count}</p></div>
            <div class="metric-item me-3"><h6>Ventas</h6><p>{total_sales_count}</p></div>
            <div class="metric-item me-3"><h6>Recaudación</h6><p>${total_revenue:.2f}</p></div>
            <a href="/users" style="text-decoration:none; color:inherit;"> <div class="metric-item bg-stats me-3"><h6>Usuarios Creados</h6><p>{TOTAL_USERS_CREATED}</p></div>
            </a>
        </div>
        <div class="nav-separator"></div>
        <a href="/test-sale" class="btn btn-sale ms-2">⚡️ Test Venta Sucursal</a> 
    </div>
</nav>
<div class="main-container container mt-4">
    <div class="row g-4">
        <div class="col-md-5">
            <div class="card">
                <div class="card-header bg-coral">
                    <span>Inventario Central (Compartido en Redis)</span>
                    <div class="dropdown">
                        <button class="btn btn-sm btn-light dropdown-toggle" type="button" data-bs-toggle="dropdown" aria-expanded="false" style="color: #F06060;">
                            <span style="font-size: 1.2rem; font-weight: bold;">+</span>
                        </button>
                        <ul class="dropdown-menu dropdown-menu-end">
                            <li><a class="dropdown-item" data-bs-toggle="modal" data-bs-target="#addProductModal">➕ Añadir Nuevo Producto</a></li>
                            <li><a class="dropdown-item" data-bs-toggle="modal" data-bs-target="#editProductSelectModal">✏️ Editar Producto (por ID)</a></li>
                            <li><a class="dropdown-item" data-bs-toggle="modal" data-bs-target="#deleteProductSelectModal">🗑️ Eliminar Producto (por ID)</a></li>
                        </ul>
                    </div>
                </div>
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
                <div class="card-header bg-intense">Historial de Notificaciones de Ventas (Compartido en Redis)</div>
                <div class="card-body p-0">
                    <div class="table-responsive" style="max-height:400px;">
                        <table class="table table-striped table-sm mb-0 align-middle">
                            <thead><tr><th>Fecha</th><th>Sucursal</th><th>Producto</th><th>Cant.</th><th>Total</th><th>Recibido</th><th>Cambio</th><th>ID Venta</th></tr></thead>
                            <tbody>{notifications_html}</tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{add_product_modal_html}
{edit_product_select_modal_html}
{delete_product_select_modal_html}
<div id="toast"></div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
{dashboard_js}
</body>
</html>
"""
TEST_SALE_FORM_HTML = f"""
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>EcoMarket Central - Test de Venta ({SERVER_NAME})</title> <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ background-color: #FAFAFA; font-family: 'Segoe UI', sans-serif; color: #333; }}
        .card {{ border: none; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); background-color: #fff; max-width: 450px; margin: 50px auto; }}
        .card-header.bg-intense {{ background-color: #ED4040; color: #fff; font-weight: 600; }}
        .btn-danger {{ background-color: #ED4040; border-color: #ED4040; }}
        .btn-danger:hover {{ background-color: #D33030; border-color: #D33030; }}
    </style>
</head>
<body>
    <div class="card">
        <div class="card-header bg-intense">
            <h5>⚡️ Simular Venta de Sucursal (via {SERVER_NAME})</h5> </div>
        <div class="card-body">
            <p>Envía una notificación de venta simulada a la Central. (Producto: ID {TEST_PRODUCT_ID}). 
            <b>El stock central y la recaudación total NO serán afectados.</b></p>
            <div id="test-result-alert"></div>
            <form id="testSaleForm" class="mt-3">
                <div class="mb-3">
                    <label for="branch_id_input" class="form-label fw-semibold">ID Sucursal de Origen (Escribe o Selecciona):</label>
                    <input list="branch_ids" id="branch_id_input" class="form-control" name="branch_id" value="TEST-SUCURSAL" required>
                    <datalist id="branch_ids">
                        <option value="TEST-SUCURSAL">
                        <option value="sucursal-demo">
                    </datalist>
                </div>
                <button type="submit" class="btn btn-danger w-100 mb-3">Ejecutar Test de Venta</button>
                <a href="/dashboard" class="btn btn-outline-secondary w-100">Volver al Dashboard</a>
            </form>
        </div>
    </div>
    <script>
        document.addEventListener('submit', async function(e) {{
            if (e.target.id === 'testSaleForm') {{
                e.preventDefault();
                const form = e.target;
                const formData = new FormData(form);
                const resultAlert = document.getElementById('test-result-alert');
                
                function showAlert(message, type) {{
                    resultAlert.innerHTML = `<div class="alert alert-${{type}} alert-dismissible fade show" role="alert">
                        ${{message}}
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>`;
                }}
                try {{
                    const res = await fetch('/submit-test-sale', {{
                        method: 'POST',
                        body: new URLSearchParams(formData)
                    }});
                    const data = await res.json(); 
                    if (res.ok) {{
                        showAlert(
                            `✅ Éxito! Venta de <b>${{formData.get('branch_id')}}</b> registrada en historial. 
                            Stock actual de Producto Falso: ${{data.updated_stock}}. 
                            <a href="/dashboard" class="alert-link">Ver Dashboard</a>`, 
                            'success');
                    }} else {{
                        showAlert(
                            `❌ Fallo (${{res.status}}): ${{data.detail || 'Fallo de conexión/servidor desconocido.'}}`, 
                            'danger');
                    }}
                }} catch (error) {{
                    showAlert('❌ Error de red: No se pudo conectar al servidor de la Central.', 'danger');
                }}
            }}
        }});
    </script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""
ADD_PRODUCT_MODAL_HTML = """
<div class="modal fade" id="addProductModal" tabindex="-1" aria-hidden="true">
  <div class="modal-dialog modal-dialog-centered">
    <div class="modal-content">
      <div class="modal-header bg-coral text-white"><h6>Nuevo Producto</h6></div>
      <form id="addProductForm">
        <div class="modal-body">
          <input class="form-control mb-2" name="id" type="number" placeholder="ID" required>
          <input class="form-control mb-2" name="name" type="text" placeholder="Nombre" required>
          <input class="form-control mb-2" name="price" type="number" step="0.01" placeholder="Precio" required>
          <input class="form-control mb-2" name="stock" type="number" placeholder="Stock inicial" required>
        </div>
        <div class="modal-footer">
          <button type="submit" class="btn btn-danger w-100">Guardar</button>
        </div>
      </form>
    </div>
  </div>
</div>
"""
EDIT_PRODUCT_SELECT_MODAL_HTML = """
<div class="modal fade" id="editProductSelectModal" tabindex="-1" aria-hidden="true">
  <div class="modal-dialog modal-dialog-centered">
    <div class="modal-content">
      <div class="modal-header bg-coral text-white"><h6>✏️ Editar Producto por ID</h6></div>
      <form id="editProductSelectForm">
        <div class="modal-body">
          <label>ID del Producto a Editar:</label>
          <input class="form-control mb-2" name="product_id" type="number" placeholder="Ej: 1" required>
          <input type="hidden" name="action" value="edit">
        </div>
        <div class="modal-footer">
          <button type="submit" class="btn btn-danger w-100">Abrir Editor</button>
        </div>
      </form>
    </div>
  </div>
</div>
"""
DELETE_PRODUCT_SELECT_MODAL_HTML = """
<div class="modal fade" id="deleteProductSelectModal" tabindex="-1" aria-hidden="true">
  <div class="modal-dialog modal-dialog-centered">
    <div class="modal-content">
      <div class="modal-header bg-intense text-white"><h6>🗑️ Eliminar Producto por ID</h6></div>
      <form id="deleteProductSelectForm">
        <div class="modal-body">
          <label>ID del Producto a Eliminar:</label>
          <input class="form-control mb-2" name="product_id" type="number" placeholder="Ej: 1" required>
          <div class="alert alert-warning mt-2">¡Atención! La eliminación es permanente.</div>
        </div>
        <div class="modal-footer">
          <button type="submit" class="btn btn-danger w-100">Confirmar Eliminación</button>
        </div>
      </form>
    </div>
  </div>
</div>
"""
DASHBOARD_JS_SCRIPT = """
<script>
function showToast(message, type='success') {
  const toast = document.createElement('div');
  const existingToast = document.getElementById('toast');
  if (existingToast) existingToast.remove();
  
  toast.id = 'toast';
  toast.className = type;
  toast.innerHTML = message;
  document.body.appendChild(toast);
  toast.style.display = 'block';
  setTimeout(() => toast.remove(), 3500);
}

document.getElementById('addProductForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);

    const payload = {
        id: parseInt(formData.get("id")),
        name: formData.get("name"),
        price: parseFloat(formData.get("price")),
        stock: parseInt(formData.get("stock"))
    };

    try {
        const res = await fetch("/inventory", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            showToast("✅ Producto agregado y sincronizado correctamente.");
            const modal = bootstrap.Modal.getInstance(document.getElementById('addProductModal'));
            modal.hide();
            setTimeout(() => location.reload(), 1500);
        } else {
            const error = await res.json();
            console.error("Error al agregar producto:", error);
            showToast("❌ Error: " + (error.detail || "Hubo un problema."), "error");
        }
    } catch (err) {
        console.error(err);
        showToast("❌ Error de conexión al agregar producto.", "error");
    }
});

document.getElementById('editProductSelectForm').addEventListener('submit', (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const id = parseInt(formData.get("product_id"));
    if (id) {
        window.location.href = `/edit-product/${id}`;
    } else {
        showToast("❌ Introduce un ID válido.", "error");
    }
});

document.getElementById('deleteProductSelectForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const id = parseInt(formData.get("product_id"));

    if (id) {
        try {
            const res = await fetch(`/delete-product/${id}`, { method: 'DELETE' });
            
            if (res.ok) {
                showToast("🗑️ Producto eliminado y sincronizado.", "warning");
            } else if (res.status === 404) {
                showToast("❌ Producto no encontrado.", "error");
            } else {
                showToast("❌ Error al eliminar el producto.", "error");
            }
            const modal = bootstrap.Modal.getInstance(document.getElementById('deleteProductSelectModal'));
            modal.hide();
            setTimeout(() => location.reload(), 1500);

        } catch (err) {
            showToast("❌ Error de conexión.", "error");
        }

    } else {
        showToast("❌ Introduce un ID válido.", "error");
    }
});
</script>
"""
CRUD_FORM_BASE_HTML = """
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>EcoMarket Central - {title}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ background-color: #FAFAFA; font-family: 'Segoe UI', sans-serif; color: #333; }}
        .card {{ border: none; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); background-color: #fff; max-width: 400px; margin: 50px auto; }}
        .card-header.bg-coral {{ background-color: #F06060; color: #fff; font-weight: 600; }}
        .btn-danger {{ background-color: #ED4040; border-color: #ED4040; }}
        .btn-danger:hover {{ background-color: #D33030; border-color: #D33030; }}
    </style>
</head>
<body>
    <div class="card">
        <div class="card-header bg-coral">
            <h5>{title}</h5>
        </div>
        <div class="card-body">
            {content}
        </div>
    </div>
</body>
</html>
"""
CRUD_ALERT_HTML = """
<html>
<head>
    <meta charset="utf-8">
    <title>{title}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ background-color: #FAFAFA; text-align: center; padding-top: 50px; }}
        .btn-danger {{ background-color: #ED4040; border-color: #ED4040; }}
        .btn-danger:hover {{ background-color: #D33030; border-color: #D33030; }}
    </style>
</head>
<body>
    <div class="alert alert-{type} mx-auto" style="max-width: 500px;" role="alert">
        {content}
        <a href="/dashboard" class="btn btn-danger mt-3">Volver al Dashboard</a>
    </div>
</body>
</html>
"""
# -----------------------------------------------------------------


# --- ENDPOINT DEL DASHBOARD (Refactorizado para Redis) ---
@app.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard"])
async def dashboard():
    r = get_redis_client()
    total_users_count_str = r.get(TOTAL_USERS_KEY) if r else None
    TOTAL_USERS_CREATED = int(total_users_count_str) if total_users_count_str else 0

    all_sales = await get_sales_from_redis(limit=100)
    central_inventory_list = await get_all_products_from_redis()
    
    inventory_dict_for_lookup = {p.id: p for p in central_inventory_list}
    real_sales = [n for n in all_sales if n.product_id != TEST_PRODUCT_ID]

    total_sales_count = len(all_sales)
    total_products_count = len(central_inventory_list)
    total_revenue = sum(n.total_amount for n in real_sales if n.total_amount is not None) 
    
    inventory_html = "".join([
        f"<tr class='{'table-danger' if p.stock < 10 else ''}'>"
        f"<td>{p.id}</td>"
        f"<td>{p.name}</td>"
        f"<td>${p.price:.2f}</td>"
        f"<td>{p.stock}</td>"
        f"</tr>"
        for p in sorted(central_inventory_list, key=lambda x: x.id) # Ordenar por ID
    ])

    # --- INICIO DE LA CORRECCIÓN (V5.3 / Dashboard Crash) ---
    notifications_html_rows = []
    for n in reversed(all_sales):
        try:
            # Intenta formatear la fecha
            timestamp_str = n.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        except (ValueError, AttributeError):
            # Si falla (ej. es None o un string corrupto), usa un placeholder
            timestamp_str = "Fecha Inválida"
            
        try:
            # Genera la fila
            row = (
                f"<tr class='{'table-info' if n.product_id == TEST_PRODUCT_ID else ''}'>"
                f"<td>{timestamp_str}</td>"
                f"<td>{n.branch_id}</td>"
                f"<td>{inventory_dict_for_lookup.get(n.product_id, Product(id=0,name='❓',price=0,stock=0)).name}</td>"
                f"<td>{n.quantity_sold}</td>"
                f"<td>${n.total_amount:.2f}</td>"
                # CORRECCIÓN DE SINTAXIS: Los paréntesis son necesarios
                f"<td>${(n.money_received if n.money_received is not None else 0.0):.2f}</td>"
                f"<td>${(n.change if n.change is not None else 0.0):.2f}</td>"
                f"<td class='text-muted small'>{n.sale_id[-12:] if n.sale_id else 'N/A'}</td></tr>"
            )
            notifications_html_rows.append(row)
        except Exception as e:
            # Captura cualquier otro error en la fila para que el dashboard no crashee
            logger.error(f"Error renderizando fila de venta {n.sale_id}: {e}")
            notifications_html_rows.append(f"<tr><td colspan='8'>Error al renderizar la venta {n.sale_id}</td></tr>")

    notifications_html = "".join(notifications_html_rows)
    # --- FIN DE LA CORRECCIÓN ---

    return HTMLResponse(DASHBOARD_HTML_TEMPLATE.format(
        total_products_count=total_products_count,
        total_sales_count=total_sales_count,
        total_revenue=total_revenue,
        TOTAL_USERS_CREATED=TOTAL_USERS_CREATED, 
        inventory_html=inventory_html,
        notifications_html=notifications_html,
        add_product_modal_html=ADD_PRODUCT_MODAL_HTML,
        edit_product_select_modal_html=EDIT_PRODUCT_SELECT_MODAL_HTML,
        delete_product_select_modal_html=DELETE_PRODUCT_SELECT_MODAL_HTML,
        SERVER_NAME_TITLE=SERVER_NAME, 
        dashboard_js=DASHBOARD_JS_SCRIPT
    ))
    

# --- ENDPOINTS TEST DE VENTA (Refactorizado para Redis) ---

@app.get("/test-sale", response_class=HTMLResponse, tags=["Dashboard"])
async def test_sale_form():
    return HTMLResponse(TEST_SALE_FORM_HTML)

@app.post("/submit-test-sale", tags=["Dashboard"]) # Retorna JSON para JS
async def submit_test_sale(branch_id: str = Form(...)):
    product_id = TEST_PRODUCT_ID 
    quantity_sold = 1 

    product = await get_product_from_redis(product_id)
    if not product:
        raise HTTPException(status_code=404, detail=f"Producto de test (ID {TEST_PRODUCT_ID}) no encontrado.")

    final_branch_id = branch_id if branch_id.startswith("TEST") else f"TEST-{branch_id}"

    notification_data = {
        "sale_id": f"TEST-{uuid.uuid4().hex[:8]}",
        "branch_id": final_branch_id,
        "product_id": product_id,
        "quantity_sold": quantity_sold,
        "money_received": 0.0,
        "total_amount": 0.0,
        "change": 0.0,
        "timestamp": datetime.now().isoformat()
    }
    
    await process_sale_notification(notification_data)
    updated_stock = product.stock 

    return JSONResponse({
        "status": "success",
        "message": f"Venta simulada de {final_branch_id} registrada.",
        "updated_stock": updated_stock
    })

# --- DEMÁS ENDPOINTS CRUD Y USUARIOS (Refactorizados para Redis) ---
@app.get("/users", response_class=HTMLResponse, tags=["Usuarios"])
async def list_users():
    r = get_redis_client()
    total_users_count_str = r.get(TOTAL_USERS_KEY) if r else None
    TOTAL_USERS_CREATED_CURRENT = int(total_users_count_str) if total_users_count_str else 0
    raw_users_data = await asyncio.to_thread(r.hgetall, USERS_HASH_KEY) if r else {}
    
    users_html = ""
    for key, user_json in raw_users_data.items():
        try:
            u = json.loads(user_json)
            users_html += f"<tr><td>{u.get('nombre')}</td><td>{u.get('email')}</td><td>{u.get('source')}</td><td>{u.get('timestamp').split('.')[0].replace('T', ' ')}</td></tr>"
        except Exception as e:
            logger.error(f"Error deserializando usuario desde Redis: {e}")
            
    html_content = f"""
<html>
<head>
    <meta charset="utf-8">
    <title>EcoMarket Central - Usuarios Registrados (via {SERVER_NAME})</title>     <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ background-color: #FAFAFA; font-family: 'Segoe UI', sans-serif; color: #333; padding: 20px; }}
        .navbar {{ background-color: #ED4040; color: white; padding: 0.8rem 1.5rem; }}
        .table thead th {{ background-color: #ED4040; color: white; border: none; font-weight: 500; }}
        .card {{ border: none; border-radius: 12px; box-shadow: 0 2px 6px rgba(0,0,0,0.06); }}
    </style>
</head>
<body>
    <div class="container">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h1>Usuarios Registrados Globalmente ({TOTAL_USERS_CREATED_CURRENT})</h1>
            <a href="/dashboard" class="btn btn-danger">Volver al Dashboard</a>
        </div>
        <div class="card p-0">
            <div class="table-responsive" style="max-height:600px;">
                <table class="table table-striped table-sm mb-0 align-middle">
                    <thead>
                        <tr><th>Nombre</th><th>Email</th><th>Origen</th><th>Fecha Registro</th></tr>
                    </thead>
                    <tbody>{users_html}</tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>
"""
    return HTMLResponse(html_content)

@app.get("/add-product-form", response_class=HTMLResponse)
async def add_product_form():
    content = f"""
        <form action="/add-product-form" method="post">
            <div class="mb-3">
                <label for="id" class="form-label">ID:</label>
                <input type="number" class="form-control" name="id" required>
            </div>
            <div class="mb-3">
                <label for="name" class="form-label">Nombre:</label>
                <input type="text" class="form-control" name="name" required>
            </div>
            <div class="mb-3">
                <label for="price" class="form-label">Precio:</label>
                <input type="number" step="0.01" class="form-control" name="price" required>
            </div>
            <div class="mb-3">
                <label for="stock" class="form-label">Stock:</label>
                <input type="number" class="form-control" name="stock" required>
            </div>
            <button type="submit" class="btn btn-danger w-100 mb-3">Agregar</button>
            <a href="/dashboard" class="btn btn-outline-secondary w-100">Volver al Dashboard</a>
        </form>
    """
    return HTMLResponse(CRUD_FORM_BASE_HTML.format(title=f"Agregar Producto (via {SERVER_NAME})", content=content)) 

@app.post("/add-product-form", response_class=HTMLResponse)
async def add_product_form_post(id: int = Form(...), name: str = Form(...), price: float = Form(...), stock: int = Form(...)):
    try:
        await add_product(Product(id=id, name=name, price=price, stock=stock))
        content = "<h3>✅ Producto agregado y sincronizado!</h3>"
        return HTMLResponse(CRUD_ALERT_HTML.format(title="Producto Agregado", type="success", content=content))
    except HTTPException as e:
        content = f"<h3>❌ Error: {e.detail}</h3>"
        return HTMLResponse(CRUD_ALERT_HTML.format(title="Error al Agregar", type="danger", content=content))

@app.get("/edit-product/{product_id}", response_class=HTMLResponse)
async def edit_product_form(product_id: int):
    p = await get_product_from_redis(product_id)
    if not p:
        return HTMLResponse(CRUD_ALERT_HTML.format(title="Error", type="danger", content="<h3>❌ Producto no encontrado.</h3>"))
    
    content = f"""
        <form action="/edit-product/{product_id}" method="post">
            <div class="mb-3">
                <label for="name" class="form-label">Nombre:</label>
                <input type="text" class="form-control" name="name" value="{p.name}" required>
            </div>
            <div class="mb-3">
                <label for="price" class="form-label">Precio:</label>
                <input type="number" step="0.01" class="form-control" name="price" value="{p.price}" required>
            </div>
            <div class="mb-3">
                <label for="stock" class="form-label">Stock:</label>
                <input type="number" class="form-control" name="stock" value="{p.stock}" required>
            </div>
            <button type="submit" class="btn btn-danger w-100 mb-3">Guardar Cambios</button>
            <a href="/dashboard" class="btn btn-outline-secondary w-100">Volver al Dashboard</a>
        </form>
    """
    return HTMLResponse(CRUD_FORM_BASE_HTML.format(title=f"Editar Producto ID: {product_id} (via {SERVER_NAME})", content=content)) 

@app.post("/edit-product/{product_id}", response_class=HTMLResponse)
async def edit_product(product_id: int, name: str = Form(...), price: float = Form(...), stock: int = Form(...)):
    try:
        await update_product(product_id, Product(id=product_id, name=name, price=price, stock=stock))
        content = "<h3>✅ Producto actualizado y sincronizado!</h3>"
        return HTMLResponse(CRUD_ALERT_HTML.format(title="Producto Actualizado", type="success", content=content))
    except HTTPException as e:
        content = f"<h3>❌ Error: {e.detail}</h3>"
        return HTMLResponse(CRUD_ALERT_HTML.format(title="Error al Actualizar", type="danger", content=content))

@app.delete("/delete-product/{product_id}", tags=["Inventario"])
async def delete_product_api(product_id: int):
    try:
        removed_data = await delete_product(product_id)
        return {"status": "success", "message": f"Producto {removed_data['removed']} eliminado."}
    except HTTPException as e:
        raise e

@app.get("/new-sale", response_class=HTMLResponse, tags=["Dashboard"])
async def new_sale_form():
    inventory_list = await get_all_products_from_redis()
    options_html = "".join([
        f"<option value='{p.name}' data-id='{p.id}' data-price='{p.price}'>" for p in inventory_list
    ])
    
    NEW_SALE_FORM_HTML = f"""
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>EcoMarket Central - Registrar Venta ({SERVER_NAME})</title>     <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ background-color: #FAFAFA; font-family: 'Segoe UI', sans-serif; color: #333; }}
        .card {{ border: none; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); background-color: #fff; max-width: 450px; margin: 50px auto; }}
        .card-header.bg-intense {{ background-color: #ED4040; color: #fff; font-weight: 600; }}
        .btn-danger {{ background-color: #ED4040; border-color: #ED4040; }}
        .btn-danger:hover {{ background-color: #D33030; border-color: #D33030; }}
    </style>
</head>
<body>
    <div class="card">
        <div class="card-header bg-intense">
            <h5>Registrar Nueva Venta (Test Manual - via {SERVER_NAME})</h5>         </div>
        <div class="card-body">
            <p class="text-muted small">Este formulario solo actualiza el stock central, NO es la sucursal.</p>
            <form action="/submit-sale" method="post" id="saleForm">
                <div class="mb-3">
                    <label for="branch_id" class="form-label fw-semibold">Sucursal (ID de Origen):</label>
                    <input type="text" class="form-control" name="branch_id" value="Central_Manual" required>
                </div>
                <div class="mb-3">
                    <label for="productInput" class="form-label fw-semibold">Producto:</label>
                    <input list="productos" id="productInput" class="form-control" name="product_name" placeholder="Escribe para buscar..." required>
                    <datalist id="productos">
                        {options_html}
                    </datalist>
                    <input type="hidden" name="product_id" id="product_id_hidden">
                    <input type="hidden" name="sale_id" value="Central_Manual_{uuid.uuid4().hex[:8]}">
                </div>
                <div class="mb-3">
                    <label for="quantity_sold" class="form-label fw-semibold">Cantidad:</label>
                    <input type="number" class="form-control" name="quantity_sold" value="1" min="1" required>
                </div>
                <div class="mb-3">
                    <label for="money_received" class="form-label fw-semibold">Dinero Recibido:</label>
                    <input type="number" step="0.01" class="form-control" name="money_received" value="0.0" required>
                </div>
                
                <button type="submit" class="btn btn-danger w-100 mb-3">Enviar Venta</button>
                <a href="/dashboard" class="btn btn-outline-secondary w-100">Volver al Dashboard</a>
            </form>
        </div>
    </div>
    <script>
        const productInput = document.getElementById('productInput');
        const productIdHidden = document.getElementById('product_id_hidden');
        const options = document.querySelectorAll('#productos option');
        productInput.addEventListener('input', function() {{
            const val = this.value;
            const match = Array.from(options).find(o => o.value === val);
            if(match) {{
                productIdHidden.value = match.dataset.id;
            }} else {{
                productIdHidden.value = '';
            }}
        }});
    </script>
</body>
</html>
"""
    return HTMLResponse(NEW_SALE_FORM_HTML) 

@app.post("/submit-sale", response_class=HTMLResponse, tags=["Dashboard"])
async def submit_sale(
    branch_id: str = Form(...),
    product_id: int = Form(...),
    quantity_sold: int = Form(...),
    money_received: float = Form(...),
    sale_id: Optional[str] = Form(None)
):
    product = await get_product_from_redis(product_id)
    if not product:
        content = "<h3>❌ Producto no encontrado.</h3><a href='/new-sale' class='btn btn-danger mt-3'>Volver</a>"
        return HTMLResponse(CRUD_ALERT_HTML.format(title="Error", type="danger", content=content))
    
    total_amount = product.price * quantity_sold
    change = money_received - total_amount
    
    if change < 0:
        content = f"""
            <h3>❌ Dinero insuficiente.</h3>
            <p><b>Total a pagar:</b> ${total_amount:.2f}</p>
            <p><b>Dinero recibido:</b> ${money_received:.2f}</p>
            <p>Faltan: ${abs(change):.2f}</p>
            <a href="/new-sale" class="btn btn-secondary mt-3">Volver al formulario</a>
        """
        return HTMLResponse(CRUD_ALERT_HTML.format(title="Error Venta", type="danger", content=content))

    if not sale_id:
        sale_id = f"Central_Manual_{uuid.uuid4().hex[:8]}"

    notification_data = {
        "sale_id": sale_id,
        "branch_id": branch_id,
        "product_id": product_id,
        "quantity_sold": quantity_sold,
        "money_received": money_received,
        "total_amount": total_amount,
        "change": change,
        "timestamp": datetime.now().isoformat()
    }
    
    await process_sale_notification(notification_data)

    content = f"""
        <h3>✅ Venta registrada correctamente!</h3>
        <p><b>ID Venta:</b> {sale_id}</p>
        <p>{branch_id} vendió {quantity_sold}x {product.name} por <b>${total_amount:.2f}</b></p>
        <p>Dinero recibido: ${money_received:.2f} | Cambio: <b>${change:.2f}</b></p>
        <a href="/new-sale" class="btn btn-danger me-2 mt-3">Registrar otra venta</a>
        <a href="/dashboard" class="btn btn-outline-danger mt-3">Ir al Dashboard</a>
    """
    return HTMLResponse(CRUD_ALERT_HTML.format(title="Venta Exitosa", type="success", content=content))

# --- CORRER SERVIDOR (se mantiene) ---
if __name__ == "__main__":
    import uvicorn
    # Cargar variables de entorno para workers (en caso de correr con python)
    BRANCHES = os.getenv("BRANCHES", "http://sucursal-demo:8002").split(",")
    RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
    RABBITMQ_USER = os.getenv("RABBITMQ_USER", "ecomarket_user")
    RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "ecomarket_password")
    QUEUE_DIRECT = os.getenv("RABBITMQ_QUEUE_DIRECT", "ventas_central_direct") 
    EXCHANGE_DIRECT = os.getenv("RABBITMQ_EXCHANGE_DIRECT", "notificaciones_direct") 
    QUEUE_FANOUT = "ventas_central_fanout"
    EXCHANGE_FANOUT = os.getenv("RABBITMQ_EXCHANGE_FANOUT", "ventas_global_fanout") 
    EXCHANGE_USER_EVENTS = os.getenv("RABBITMQ_EXCHANGE_USERS", "user_events_fanout")
    QUEUE_USER_NOTIFS = os.getenv("RABBITMQ_QUEUE_NOTIFS", "user_notifs_central")
    QUEUE_USER_STATS = os.getenv("RABBITMQ_QUEUE_STATS", "user_stats_central")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
