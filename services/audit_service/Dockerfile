FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

CMD ["gunicorn", "--workers=3", "auth_service.wsgi:application", "--bind", "0.0.0.0:8000"]
