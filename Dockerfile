# Usar Python 3.11 como base
FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Copiar primero los archivos de dependencias para aprovechar la caché de Docker
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el resto de los archivos del proyecto al contenedor
COPY . .

# Establecer permisos (opcional, dependiendo de la configuración)
RUN chmod -R 755 /app

# Exponer el puerto que usará la aplicación
EXPOSE 8000

# Comando de inicio
CMD ["gunicorn", "dashboard:server", "--workers=4", "--bind=0.0.0.0:8000", "--timeout=120"]







