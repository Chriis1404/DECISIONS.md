# 🆘 Guía de Solución de Problemas (Troubleshooting)

### 1. Error: "Address already in use"
**Síntoma:** Al iniciar el servidor, sale un error diciendo que la dirección ya se está usando.
**Causa:** Dejaste el servidor corriendo en otra terminal o el puerto 5000 está ocupado por otro programa.
**Solución:**
* Mata el proceso anterior (`Ctrl+C`).
* O cambia el puerto en el código:
  ```python
  PORT = 5050  # Cambiar 5000 a 5050
2. Firewall Bloqueando Conexión (LAN)
Síntoma: El cliente no conecta si está en otra computadora de la red. Solución:

Windows: Abrir "Firewall de Windows con seguridad avanzada" -> Reglas de entrada -> Nueva Regla -> Puerto -> 5000 -> Permitir conexión.

Linux:

Bash

sudo ufw allow 5000/tcp
sudo ufw allow 5001/udp
3. Caracteres Extraños
Síntoma: Al recibir el mensaje se ven símbolos raros ``. Solución: Asegurar que ambos extremos usen la misma codificación. En nuestros scripts forzamos UTF-8:

Python

data.decode('utf-8')
