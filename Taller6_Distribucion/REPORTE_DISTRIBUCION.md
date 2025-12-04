# 📊 Reporte Técnico: Estrategias de Distribución de Datos

### 1. Replicación vs Sharding
En este taller exploramos dos formas de escalar datos:

* **Replicación (Lo que implementamos):** Copiar los mismos datos en varios servidores.
    * *Ventaja:* Acelera las lecturas masivamente.
    * *Desventaja:* Las escrituras siguen limitadas a un solo nodo (Primario).
    
* **Sharding (Fragmentación):** Dividir los datos (ej. Usuarios A-M en Servidor 1, N-Z en Servidor 2).
    * *Ventaja:* Escala escrituras infinitamente.
    * *Desventaja:* Complejidad extrema en la aplicación (Joins imposibles).

### 2. Conclusión para EcoMarket
Para el nivel actual de tráfico de EcoMarket, la **Replicación** es la estrategia correcta. El cuello de botella eran las lecturas del catálogo. El Sharding se reserva para una fase futura si alcanzamos millones de usuarios.

### 3. Problemas Encontrados
Durante la implementación, nos enfrentamos al **Replication Lag**.
* *Síntoma:* Un usuario creaba un producto y no lo veía inmediatamente en la lista.
* *Solución:* Forzar lecturas a la Primaria solo para el usuario que acaba de escribir ("Read your own writes").
