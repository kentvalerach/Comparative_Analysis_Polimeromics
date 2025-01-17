FROM python:3.10

WORKDIR /app

COPY . /app/

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

EXPOSE $PORT

CMD ["gunicorn", "dashboard_corrected:app.server", "--workers=4", "--bind", "0.0.0.0:8080"]







