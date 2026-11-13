# Imagen base ligera con Python 3.12
FROM python:3.12-slim

# No generar .pyc y mostrar los logs al momento
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# 1. Dependencias primero: si solo cambia el código, Docker reutiliza esta capa
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. Código fuente de la aplicación
COPY src/ ./src/

# 3. Usuario sin privilegios propietario del código (no se ejecuta como root)
RUN useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser

WORKDIR /app/src
EXPOSE 8000

# 4. Comando de inicio: arranca la API escuchando en todas las interfaces
CMD ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
