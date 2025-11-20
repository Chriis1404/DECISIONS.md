FROM python:3.10-slim

# 1. ESTABLECER WORKDIR en el directorio padre
WORKDIR /app

# 2. Copiar los requisitos (el punto es la raíz del contexto de build)
# Esto garantiza que el archivo se encuentra si está en C:\Users\user\Documents\Eligardo\requirements.txt
COPY requirements.txt .

# 3. Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copiar la carpeta Ecomarket completa
COPY Ecomarket /app/Ecomarket
