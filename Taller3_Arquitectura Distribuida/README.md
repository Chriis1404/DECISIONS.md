# 🌐 **EcoMarket - Taller 3: Arquitectura Distribuida**

![Python](https://img.shields.io/badge/Python-FastAPI-yellow?logo=python)
![Architecture](https://img.shields.io/badge/Architecture-Distributed-blue?logo=diagrams.net)
![Resilience](https://img.shields.io/badge/Resilience-Circuit_Breaker-green)

### 🚀 *Expansión: De Monolito a Sistema Distribuido*

📅 **Fecha:** 22 de Octubre de 2025 (Reconstrucción Histórica)\
👤 **Autores:** Christofer Roberto Esparza Chavero, Brian Garcia y Juan
Cordova\
📂 **Proyecto:** EcoMarket - Versión 3.0 (Central + Sucursal Autónoma)

------------------------------------------------------------------------

## 🎯 **Objetivo del Taller**

Transformar el sistema centralizado de EcoMarket en una **solución
distribuida** capaz de soportar la apertura de nuevas sucursales. El
reto principal fue mitigar la latencia de red y garantizar que las
ventas continúen incluso si la conexión con la Central falla
("Offline-First").

------------------------------------------------------------------------

## 🧠 **Principios de Diseño (ADN de la Arquitectura)**

### 1. Autonomía Local (Offline-First)

-   Cada sucursal opera con su propio inventario en memoria.
-   Garantiza continuidad operativa incluso sin internet.

### 2. Comunicación Asíncrona

-   Notificaciones en segundo plano.
-   Evita bloquear proceso de venta.

### 3. Resiliencia (Circuit Breaker)

-   Protege de fallos repetidos.
-   Reintenta solo en intervalos controlados.

------------------------------------------------------------------------

## 🧭 **Diagrama de Arquitectura**

``` mermaid
flowchart LR
    subgraph Central_Node ["🏢 Nodo Central (Puerto 8000)"]
        A[API Central]
        DB[(Inventario Global)]
        A --- DB
    end

    subgraph Branch_Node ["🏪 Sucursal 1 (Puerto 8001)"]
        B[API Sucursal]
        C[(Caché Local)]
        CB{Circuit Breaker}

        B --- C
        B -- Intento de Notificación --> CB
    end

    CB -- "HTTP POST (Async)" --> A
```

------------------------------------------------------------------------

## 💻 **Implementación Técnica**

Consistencia Eventual:\
✔ Sucursales siempre disponibles\
⚠ Retraso natural en sincronización con Central

Scripts incluidos:\
- [`central_t3.py`](https://github.com/Chriis1404/DECISIONS.md/blob/main/Taller3_Arquitectura%20Distribuida/Central_t3.py)\
- [`sucursal_t3.py`](https://github.com/Chriis1404/DECISIONS.md/blob/main/Taller3_Arquitectura%20Distribuida/Sucursal_t3.py)

------------------------------------------------------------------------

## 🛠️ **Cómo Ejecutarlo**

**Terminal 1 -- Central**

``` bash
uvicorn central_t3:app --port 8000
```

**Terminal 2 -- Sucursal**

``` bash
uvicorn sucursal_t3:app --port 8001
```

**Terminal 3 -- Venta**

``` bash
curl -X POST "http://localhost:8001/sell"      -H "Content-Type: application/json"      -d '{"product_id": 1, "quantity": 5}'
```

------------------------------------------------------------------------

## 🎤 **Elevator Pitch**

"EcoMarket Distribuido permite que cada tienda siga vendiendo incluso
sin internet, opera más rápido y escala hasta 100 sucursales sin
volverse frágil."

------------------------------------------------------------------------

## 🛡️ **Investigación de Resiliencia**

**¿Qué es Circuit Breaker?**\
Un fusible digital que corta llamadas a un servicio caído.

**¿Por qué no basta Timeout?**\
Timeout = esperar lento.\
Circuit Breaker = falla instantánea (fail-fast).

------------------------------------------------------------------------

## 🎯 Estado del Taller: ✅ Completado
