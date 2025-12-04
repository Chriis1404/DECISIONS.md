# 🏗️ **EcoMarket - Taller 1: Arquitectura Monolítica**
![Python](https://img.shields.io/badge/Python-3.9-yellow?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-REST-009688?style=flat&logo=fastapi&logoColor=white)
![HTTP](https://img.shields.io/badge/HTTP-Protocol-red?style=flat&logo=http)

### 🎯 *Fundamentos de HTTP y Diseño de APIs REST*

📅 **Fecha:** 10 de Octubre de 2025 (Reconstrucción Histórica)  
👤 **Autores:** Christofer Roberto Esparza Chavero, Brian Garcia y Juan Cordova  
📂 **Proyecto:** EcoMarket - Versión 1.0 (Monolito)

---

## 🚀 **Descripción del Proyecto**

Este taller marca el inicio de EcoMarket. El objetivo fue comprender los fundamentos de la comunicación web construyendo una **API REST Monolítica** desde cero. 

En esta etapa, no utilizamos bases de datos reales ni contenedores complejos. Todo el estado se maneja en memoria (listas de Python) para enfocarnos puramente en el diseño de URLs, verbos HTTP y códigos de estado.

---

## 🕵️‍♂️ **Actividad 1: Detective de APIs (Análisis)**

Antes de codificar, analizamos el comportamiento de una API real (`jsonplaceholder`) para entender los patrones de comunicación estándar.

### 📊 Tabla de Observaciones
| Acción | URL | Método HTTP | Código Respuesta | ¿Qué devolvió? |
|:---|:---|:---:|:---:|:---|
| **Listar** | `/posts` | `GET` | **200 OK** | Un arreglo JSON con 100 objetos. |
| **Obtener uno** | `/posts/1` | `GET` | **200 OK** | Un solo objeto JSON con ID 1. |
| **Crear** | `/posts` | `POST` | **201 Created** | El objeto creado con un nuevo ID (101). |
| **No existe** | `/posts/999`| `GET` | **404 Not Found**| Un objeto vacío `{}` o error. |

> **Conclusión Teórica:** Aprendimos que REST se basa en **Recursos** (sustantivos en la URL) y **Representaciones** (JSON devuelto), manipulados a través de verbos HTTP estandarizados.

---

## 📐 **Actividad 2: Diseño de la API EcoMarket**

Como equipo, diseñamos la interfaz para gestionar el inventario de EcoMarket.

### 📝 Decisiones de Diseño
* **Recurso Principal:** `products` (en plural, siguiendo convención REST).
* **Estructura de URL:** `/products/{id}`.

### 🗺️ Mapa de Endpoints
| Verbo | Endpoint | Acción de Negocio | Status Éxito | Status Error |
|:---|:---|:---|:---:|:---:|
| `GET` | `/products` | Listar todo el catálogo | `200` | - |
| `GET` | `/products/{id}` | Ver detalle de producto | `200` | `404` |
| `POST` | `/products` | Agregar nuevo producto | `201` | `400` |
| `PUT` | `/products/{id}` | Actualizar stock/precio | `200` | `404` |
| `DELETE`| `/products/{id}` | Eliminar del catálogo | `204` | `404` |

### ⚖️ Dilemas de Diseño Resueltos
Durante el diseño, el equipo tomó las siguientes decisiones arquitectónicas:
1.  **PUT en recurso inexistente:** Decidimos devolver `404 Not Found` en lugar de crearlo automáticamente, para evitar inconsistencias de IDs.
2.  **DELETE idempotente:** Si se intenta borrar un producto que ya no existe, devolvemos `404` para informar al cliente que el recurso ya no está disponible.

---

## 💻 **Actividad 3 y 4: Implementación y Robustez**

Se desarrolló la API utilizando **FastAPI**. A continuación se detallan las instrucciones para ejecutarla y probarla.

### 🛠️ Instalación y Ejecución

1.  **Instalar dependencias:**
    ```bash
    pip install fastapi uvicorn requests
    ```

2.  **Correr el servidor:**
    ```bash
    uvicorn main:app --reload --port 8000
    ```

3.  **Verificar estado:**
    Visitar `http://localhost:8000/docs` para ver la documentación interactiva (Swagger UI).

### 🧪 Pruebas Manuales (Curl)

**1. Crear un Producto:**
```bash
curl -X POST "http://localhost:8000/products"      -H "Content-Type: application/json"      -d '{"id": 3, "name": "Café", "price": 12.5, "stock": 50}'
```
Resultado esperado: **201 Created**

**2. Consultar Producto Inexistente:**
```bash
curl -X GET "http://localhost:8000/products/999"
```
Resultado esperado: **404 Not Found**
```json
{"detail": "Producto no encontrado"}
```

---

## ⚡ Actividad 5: Análisis de Performance

Realizamos pruebas de latencia simulada para entender el impacto en la experiencia de usuario.

### 📊 Resultados de Medición

| Escenario | Tiempo Promedio | Observación |
|:---|:---:|:---|
| Baseline (Local) | 15ms | Respuesta instantánea. |
| Latencia Simulada | 515ms | Se percibe un retraso notable ("lag"). |
| Carga (50 reqs) | 1.2s (Total) | Python manejó la concurrencia básica bien. |

> **Experimento:** Al agregar `time.sleep(0.5)` en el endpoint GET, notamos que la UI se sentía "trabada", validando la importancia de la optimización en el backend.

---

## 🔮 Actividad 6: Propuesta de Mejoras (Futuro)

Pensando en una escala real (10,000 productos), el equipo propuso:

- **Mejora de Performance:** Implementar Paginación en `GET /products` (ej. `?limit=20&page=1`) para no enviar 10k items de golpe.
- **Experiencia de Usuario:** Agregar filtros de búsqueda (ej. `?name=manzana`) para encontrar productos rápido.
- **Confiabilidad:** Migrar de la lista en memoria a una Base de Datos Real (PostgreSQL) para persistencia de datos (Implementado en Taller 6).

---

## 🧠 Actividad 7: Reflexión Individual

> "Antes de este taller, pensaba que una API era solo una URL web. Ahora entiendo que es un contrato estricto de comunicación. El mayor desafío fue manejar correctamente los códigos de error (400 vs 404 vs 500), pero usar FastAPI facilitó mucho la validación de datos."
>
> — Equipo de Desarrollo EcoMarket

# 📂 Código Fuente
- [main.py](/https://github.com/Chriis1404/DECISIONS.md/blob/main/Taller1_Arquitectura%20Monol%C3%ADtica/main.py)
---

### 🎯 Estado del Taller: **✅ Completado**
