# 📝 Conclusión del Informe Técnico Hito 2

## Garantía de la Tríada CIA
La implementación conjunta de JWT y HTTPS asegura los tres pilares de la seguridad de la información:

1.  **Confidencialidad:** Garantizada por el túnel **TLS 1.3**. Los datos de negocio y credenciales son ilegibles para terceros.
2.  **Integridad:** Garantizada por las firmas digitales **HMAC-SHA256** de los tokens. Cualquier modificación anula el acceso.
3.  **Disponibilidad:** La arquitectura distribuida con Nginx protege contra sobrecargas simples y permite escalabilidad horizontal.

## Impacto en el Ciclo DevOps
Externalizar la configuración (`.env`) ha transformado nuestro flujo de trabajo:
* **CI/CD Seguro:** Podemos usar repositorios públicos sin riesgo.
* **Rotación sin Downtime:** Cambiar una contraseña de base de datos ya no requiere recompilar ni modificar código, solo reiniciar el contenedor con nuevas variables.
* **Onboarding:** Los nuevos desarrolladores pueden levantar el entorno en minutos usando `.env.example` sin necesidad de solicitar accesos críticos.

## Desafíos y Soluciones
El principal desafío fue la configuración de **Nginx como Proxy Inverso con SSL**, especialmente la gestión de certificados autofirmados y la redirección de puertos en Docker. Se solucionó mediante el uso de volúmenes montados para inyectar los certificados en tiempo de ejecución.

## Próximos Pasos
La evolución natural del sistema apunta hacia la implementación de **mTLS (Mutual TLS)** para una arquitectura Zero Trust dentro del clúster, y la adopción de **HashiCorp Vault** para una gestión de secretos dinámica y auditada en tiempo real.

---
