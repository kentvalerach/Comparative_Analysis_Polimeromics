
# Usa una imagen base completa de Python que incluye pip
FROM python:3.10

# Establece el directorio de trabajo
WORKDIR /app

# Copia todos los archivos al contenedor
COPY . /app/

# Actualiza pip e instala dependencias
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Exponer el puerto dinámico
EXPOSE $PORT

# Comando para iniciar el servidor
CMD ["gunicorn", "dashboard_corrected:app.server", "--workers=4", "--bind", "0.0.0.0:$PORT"]



