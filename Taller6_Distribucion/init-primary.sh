#!/bin/bash
set -e

# 1. Crear usuario de replicación
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE ROLE replicator WITH REPLICATION PASSWORD 'rep_password' LOGIN;
    SELECT pg_create_physical_replication_slot('replication_slot_1');
EOSQL

# 2. Actualizar pg_hba.conf para permitir replicación desde cualquier lugar (Docker network)
echo "host replication replicator all md5" >> "$PGDATA/pg_hba.conf"

# 3. Crear tablas necesarias para las pruebas
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Tabla para pruebas de replicación (write_load)
    CREATE TABLE IF NOT EXISTS orders (
        id SERIAL PRIMARY KEY,
        user_id VARCHAR(50),
        product VARCHAR(100),
        amount DECIMAL(10,2),
        created_at TIMESTAMP DEFAULT NOW()
    );
    
    -- Tabla para pruebas de sharding (ShardRouter)
    CREATE TABLE IF NOT EXISTS users (
        user_id VARCHAR(50) PRIMARY KEY,
        name VARCHAR(100),
        email VARCHAR(100),
        created_at TIMESTAMP DEFAULT NOW()
    );
    
    -- Indices
    CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
EOSQL

echo "✅ Tablas orders y users creadas exitosamente"
