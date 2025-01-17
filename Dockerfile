# Usar Python 3.11 como base
FROM python:3.11-slim

# Configurar directorio de trabajo
WORKDIR /app

# Copiar archivos necesarios al contenedor
COPY . .

# Instalar dependencias
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Exponer el puerto para el contenedor
EXPOSE 8000

# Comando de inicio
CMD ["gunicorn", "dashboard:app.server", "--workers=4", "--bind=0.0.0.0:8000"]







