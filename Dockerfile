# ==============================================================================
# Kyberna IA - Contenedor de Despliegue Multiplataforma
# ==============================================================================
FROM python:3.12-slim

# Metadatos del proyecto
LABEL maintainer="Kyberna IA Team"
LABEL description="Centro de Mando Predictivo y Desvío Vial Humanitario ante El Niño"

# Variables de entorno para Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Directorio de trabajo en el contenedor
WORKDIR /app

# Instalar dependencias del sistema mínimas requeridas
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar manifiesto de dependencias e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código fuente del proyecto (incluye frontend/dist precompilado)
COPY . .

# Exponer el puerto del servidor HTTP FastAPI
EXPOSE 8000

# Healthcheck nativo para verificar disponibilidad del servicio
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/surveillance || exit 1

# Comando de arranque por defecto: enlazar a 0.0.0.0 para acceso multired/móvil
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
