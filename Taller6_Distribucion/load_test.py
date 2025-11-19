import psycopg2
import time
import random
from concurrent.futures import ThreadPoolExecutor

# Configuración de los contenedores
PRIMARY = {'host': 'localhost', 'port': 5432, 'database': 'ecomarket', 'user': 'postgres', 'password': 'postgres_pass'}
SECONDARY_1 = {'host': 'localhost', 'port': 5433, 'database': 'ecomarket', 'user': 'postgres', 'password': 'postgres_pass'}
SECONDARY_2 = {'host': 'localhost', 'port': 5434, 'database': 'ecomarket', 'user': 'postgres', 'password': 'postgres_pass'}

def write_load():
    print("\n--- Iniciando Carga de Escritura (PRIMARY) ---")
    try:
        conn = psycopg2.connect(**PRIMARY)
        cursor = conn.cursor()
        for i in range(50):
            cursor.execute("INSERT INTO orders (user_id, product, amount) VALUES (%s, %s, %s)", 
                           (f"user_{i}", "Manzana", random.uniform(10, 100)))
        conn.commit()
        print("✅ 50 Órdenes insertadas en el Primario")
        conn.close()
    except Exception as e:
        print(f"❌ Error escribiendo: {e}")

def check_replication(config, name):
    print(f"\n--- Verificando Replicación en {name} ---")
    try:
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM orders")
        count = cursor.fetchone()[0]
        print(f"✅ {name}: Ve {count} órdenes (Sincronizado)")
        conn.close()
    except Exception as e:
        print(f"❌ Error leyendo de {name}: {e}")

def test_sharding():
    print("\n--- Probando Sharding ---")
    try:
        from shard_router import SimpleHashShardRouter
        # Usamos el puerto 5432 y 5433 simulando dos shards primarios distintos
        shards = [PRIMARY, SECONDARY_1] 
        router = SimpleHashShardRouter(shards)
        
        ids = [f"user_{i}" for i in range(100)]
        dist = router.get_shard_distribution(ids)
        print("📊 Distribución de usuarios:")
        for shard, count in dist.items():
            print(f"   Shard {shard}: {count} usuarios")
    except ImportError:
        print("❌ No se encontró shard_router.py")

if __name__ == "__main__":
    # 1. Esperar a que Docker arranque
    print("⏳ Esperando 5s para asegurar inicio de DBs...")
    time.sleep(5)
    
    # 2. Escribir en el Master
    write_load()
    
    # 3. Esperar replicación
    time.sleep(2)
    
    # 4. Leer de los Esclavos
    check_replication(SECONDARY_1, "Secundario 1")
    check_replication(SECONDARY_2, "Secundario 2")
    
    # 5. Probar lógica de Sharding
    test_sharding()
