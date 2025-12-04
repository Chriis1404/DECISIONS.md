```markdown
# 🤔 Reflexión: Análisis de Seguridad Profundo

### 1. Vulnerabilidad de GitHub
**Pregunta:** Si un atacante obtiene tu `JWT_SECRET` de GitHub, ¿puede generar tokens para usuarios que nunca han hecho login?
**Respuesta:** **SÍ.** Al tener la llave maestra de firma, el atacante puede forjar un token (Token Forgery) con cualquier `sub` (ID de usuario) y cualquier `role` (ej. admin), sin necesidad de conocer la contraseña del usuario. Por eso proteger el secreto es vital.

### 2. Robo de Token vs Robo de Secreto
* **Robo de Token:** Afecta a un solo usuario por un tiempo limitado (hasta que expire).
* **Robo de Secreto:** Compromete a **toda la plataforma** indefinidamente. Permite suplantar a cualquiera.

### 3. HTTPS vs JWT_SECRET
**Pregunta:** Si implementas HTTPS pero tu `JWT_SECRET` está en GitHub, ¿sigues vulnerable?
**Respuesta:** **SÍ.** HTTPS protege el tránsito (nadie ve el token viajar), pero si el secreto es público, no necesitas interceptar el tráfico; puedes crear tus propios pases VIP desde casa.

### 4. Certificados Autofirmados
**Pregunta:** ¿Por qué no es suficiente un certificado autofirmado en producción?
**Respuesta:** Porque no garantiza **Autenticidad**. Un atacante podría interceptar la conexión y presentar *su propio* certificado autofirmado. Sin una Autoridad Certificadora (CA) confiable (como Let's Encrypt) que valide la identidad del dominio, el usuario no tiene garantía de estar hablando con el servidor real.

---
*Respuestas elaboradas durante la Fase de Análisis.*
