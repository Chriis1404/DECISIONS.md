```markdown
# 🔬 Registro de Experimentos Comparativos (TCP vs UDP)

Este documento detalla las pruebas de estrés y comportamiento realizadas sobre los sockets para entender sus límites.

---

## 🧪 Experimento A: Conexión Caída (TCP)
**Hipótesis:** Si TCP mantiene una sesión activa, apagar el servidor debería generar un error inmediato en el cliente.

**Procedimiento:**
1. Conectar `tcp_client.py` al servidor.
2. Detener el servidor con `Ctrl+C`.
3. Intentar enviar un mensaje desde el cliente.

**Resultado (Log):**
```text
🔄 [TCP] Enviando: Mensaje de prueba...
❌ Error: ConnectionResetError: [WinError 10054] Se ha forzado la interrupción de una conexión existente.
Conclusión: TCP garantiza la integridad del canal. Si un extremo cae, el otro se entera inmediatamente (Connection Reset).🧪 Experimento B: Sin Servidor (UDP)Hipótesis: Como UDP no tiene "handshake", el cliente debería poder enviar datos al vacío sin error.Procedimiento:Asegurar que udp_server.py esté APAGADO.Ejecutar udp_client.py.Resultado (Log):Plaintext🚀 [UDP] Cliente listo. Enviando a 127.0.0.1:5001
📤 [UDP] Enviando: Mensaje 1 UDP
⚠️ [UDP] Timeout: No hubo respuesta (Eco), pero el envío fue exitoso.
Conclusión: UDP es "Fire and Forget". El envío no falló, simplemente nadie escuchó. Esto es ideal para streaming donde no queremos detener el video si se pierde un paquete.🧪 Experimento C: Tamaño de Buffer (Fragmentación)Procedimiento: Se modificó el tamaño del buffer de lectura de 1024 a 8 bytes en el servidor.Entrada: "Hola Mundo, esto es una prueba de buffer pequeño" (43 bytes).Resultado:El servidor tuvo que ejecutar el ciclo recv(8) múltiples veces:recv(8) -> "Hola Mun"recv(8) -> "do, esto"recv(8) -> " es una "...Conclusión: En TCP, los datos son un "stream" (flujo). No hay garantía de que un send corresponda a un solo recv. La aplicación debe saber reconstruir el mensaje.📊 Resumen ComparativoCaracterísticaTCPUDPGarantía de Entrega✅ Sí (ACKs)❌ NoOrden✅ Garantizado (Secuencial)❌ Puede llegar desordenadoPeso/Overhead🔴 Alto (Cabeceras grandes)🟢 Bajo (Cabeceras mínimas)Comportamiento ante FalloExcepción/BloqueoSilencio/Pérdida
