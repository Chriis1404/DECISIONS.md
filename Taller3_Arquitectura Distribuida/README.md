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

## 📝 **Contexto y Desafío de Negocio**

EcoMarket ha tenido un éxito rotundo y planea abrir **3 nuevas
sucursales**. Sin embargo, el sistema centralizado actual representa un
riesgo crítico para esta expansión. Si no evolucionamos la arquitectura,
enfrentamos tres problemas graves:

1.  **Mala experiencia del cliente:** Consultas lentas de stock debido a
    la latencia de red hacia la central.
2.  **Parálisis operativa:** Si falla el internet en una sucursal, no se
    puede vender nada (Punto único de fallo).
3.  **Inconsistencia de datos:** Riesgo de vender productos agotados si
    la sincronización no es robusta.

**Nuestra Misión:** Transformar el sistema monolítico en una solución
distribuida que priorice la **Autonomía** y la **Velocidad** en el punto
de venta.

------------------------------------------------------------------------

## 🧠 **Principios de Diseño (ADN de la Arquitectura)**

Basado en nuestra investigación de casos reales y desafíos técnicos,
definimos los siguientes principios rectores en nuestro `DECISIONS.md`:

### 1. Autonomía Local (Offline-First)

-   **Principio:** Cada sucursal operará de forma autónoma, manteniendo
    su propio inventario en memoria (Caché Local).
-   **Justificación:** Aprendimos de casos de éxito en retail que
    depender de la red central para cada transacción es un error. La
    operación comercial no puede detenerse por una caída de internet.
-   **Riesgo Mitigado:** "Parálisis Operativa" y pérdida de ventas por
    fallos de infraestructura.

### 2. Comunicación Asíncrona

-   **Principio:** Sincronización de inventarios mediante notificaciones
    en segundo plano (*Fire and Forget*).
-   **Justificación:** Las consultas síncronas (esperar respuesta de la
    central) bloquean el punto de venta. Al desacoplar la venta de la
    notificación, reducimos el tiempo de cobro de segundos a
    milisegundos.
-   **Riesgo Mitigado:** Latencia alta afectando la Experiencia de
    Usuario (UX).

### 3. Resiliencia (Circuit Breaker)

-   **Principio:** Implementación del patrón *Circuit Breaker* para
    manejar fallos repetitivos.
-   **Justificación:** Si la Central está caída, seguir intentando
    conectar satura la red y desperdicia recursos. El sistema debe
    "cortar" la conexión temporalmente y reintentar solo cuando sea
    prudente.

------------------------------------------------------------------------

## 🧭 **Diagrama de Arquitectura**

Esta nueva arquitectura separa la responsabilidad en dos nodos
principales, permitiendo que la sucursal opere incluso si el enlace con
la central se rompe.

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

        B -- "Lectura/Escritura Inmediata" --- C
        B -- "1. Intento de Notificación" --> CB
    end

    CB -- "2. HTTP POST (Async)" --> A
    A -.->|"3. Confirmación (Eventual)"| B

    style Central_Node fill:#f9f,stroke:#333,stroke-width:2px
    style Branch_Node fill:#bbf,stroke:#333,stroke-width:2px
```

Flujo de Datos Detallado:

-   **Venta Local:** La Sucursal procesa la venta contra su caché local
    (C). La respuesta al cliente es inmediata.
-   **Notificación:** En segundo plano (Background Task), la Sucursal
    intenta notificar a la Central (A).
-   **Protección:** Si la Central no responde, el Circuit Breaker (CB)
    se abre, evitando que la sucursal se quede "colgada" esperando.

------------------------------------------------------------------------

## 💻 Implementación Técnica y Consistencia

**Estrategia de Consistencia:** Eventual (AP)

En el Teorema CAP, elegimos Disponibilidad (A) y Tolerancia a
Particiones (P) sobre la Consistencia Inmediata (C).

-   ✅ *Ganamos:* Velocidad y continuidad de negocio. La tienda siempre
    vende.\
-   ⚠️ *Aceptamos:* Retraso temporal en el inventario de la Central.

### **Componentes del Código**

-   [`central_t3.py` --- Servidor maestro y fuente de la "Verdad
    Global".](https://github.com/Chriis1404/DECISIONS.md/blob/main/Taller3_Arquitectura%20Distribuida/Central_t3.py)
-   [`sucursal_t3.py`](https://github.com/Chriis1404/DECISIONS.md/blob/main/Taller3_Arquitectura%20Distribuida/Sucursal_t3.py) --- Cliente autónomo con lógica de Circuit Breaker
    implementando los estados `CLOSED`, `OPEN`, `HALF_OPEN`.

------------------------------------------------------------------------

## 🛠️ Cómo Ejecutar la Simulación

### Terminal 1 -- Levantar Central

``` bash
uvicorn central_t3:app --port 8000
```

### Terminal 2 -- Levantar Sucursal

``` bash
uvicorn sucursal_t3:app --port 8001
```

### Terminal 3 -- Simular Venta

``` bash
curl -X POST "http://localhost:8001/sell"      -H "Content-Type: application/json"      -d '{"product_id": 1, "quantity": 5}'
```

------------------------------------------------------------------------

## 🎤 Elevator Pitch (Valor para el Negocio)

"Señor Director, la infraestructura actual es un riesgo: si se corta el
cable de internet en la oficina central, todas las nuevas sucursales
dejarían de vender. Eso es dinero perdido y clientes molestos.

Nuestra nueva arquitectura 'EcoMarket Distribuido' dota a cada tienda de
un cerebro propio. Esto se traduce en:

-   **Velocidad:** Cobros instantáneos.
-   **Confiabilidad:** Operación continua incluso sin internet.
-   **Crecimiento:** Capacidad de escalar a 100 sucursales sin saturar
    la central.

Es la diferencia entre un sistema frágil y uno robusto preparado para
escalar."

------------------------------------------------------------------------

## 🛡️ Investigación de Resiliencia (Fase 4)

### 1. ¿Qué es el patrón Circuit Breaker?

Actúa como un fusible: si hay fallos continuos al llamar a la Central,
se pasa a estado **OPEN** y deja de intentar conexiones hasta que sea
seguro reintentar.

### 2. ¿Por qué un simple Timeout no es suficiente?

Con muchos clientes en espera, un timeout de 5s colapsaría el sistema.\
El Circuit Breaker permite **Fail-Fast**, respondiendo al cliente sin
esperas innecesarias.

------------------------------------------------------------------------

## 🎯 Estado del Taller: **✅ Completado**
