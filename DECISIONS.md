## Principio de Diseño

**Evitar consultas síncronas de inventario en sistemas distribuidos de retail.**  
En su lugar, preferir mecanismos asíncronos, caché local, o eventos desacoplados para la disponibilidad de inventario.

## Justificación

Las consultas síncronas de inventario introducen latencia significativa y riesgo de bloqueo en flujos críticos de venta, especialmente en entornos distribuidos donde la conectividad y la consistencia eventual pueden variar. Al emplear mecanismos asíncronos, EcoMarket asegura una experiencia de cliente ágil y resiliente, reduce la dependencia de la disponibilidad inmediata de servicios remotos, y minimiza el impacto de fallas o demoras en la red sobre la operación de la tienda.
