# 🕵️ Actividad: Auditoría de Código Estática

**Objetivo:** Identificar secretos hardcodeados antes de la
implementación de seguridad.\
**Herramienta:** `grep`

### 1. Ejecución de Búsqueda

Se ejecutó el siguiente comando en la raíz del proyecto para encontrar
fugas de información:

``` bash
grep -rn "password\|secret\|key\|token\|api_key" --include="*.py" --include="*.yml" .
```

### 2. Hallazgos (Vulnerabilidades Detectadas)

  ------------------------------------------------------------------------------------
  Archivo       |       Línea  | Contenido Detectado                    |    Nivel de
                                                                          Riesgo
  -------------------- ------- ------------------------------------------ ------------
  docker-compose.yml  | 120    | POSTGRES_PASSWORD=postgres_pass          |  🔴 Crítico

  docker-compose.yml  | 145   |  RABBITMQ_DEFAULT_PASS=ecomarket_password  | 🔴 Crítico

  CentralAPI.py       | 45   |   SECRET_KEY = "mi_super_clave_secreta..."   |🔴 Crítico
  ------------------------------------------------------------------------------------

### 3. Plan de Acción

-   **Inmediato:** Remover líneas y reemplazar por variables de entorno
    `${VARIABLE}`.\
-   **Saneamiento:** Si este fuese un repositorio público real, se
    debería rotar (cambiar) todas las contraseñas expuestas, ya que
    quedarían en el historial de Git.

------------------------------------------------------------------------

Auditoría realizada por el equipo de DevOps de **EcoMarket**.
