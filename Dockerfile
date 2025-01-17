# Usa una imagen base de Python
FROM python:3.10

# Establece el directorio de trabajo
WORKDIR /app

# Copia los archivos necesarios
COPY . /app/

# Actualiza pip e instala dependencias
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expone el puerto dinámico
EXPOSE $PORT

# Define un puerto predeterminado si $PORT no está definido
CMD ["gunicorn", "dashboard_corrected:app.server", "--workers=4", "--bind", "0.0.0.0:${PORT:-8000}"]






