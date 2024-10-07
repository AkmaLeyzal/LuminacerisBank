# Dockerfile for Transaction Service
FROM python:3.9-slim

WORKDIR /transaction_service

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "--workers=3", "--bind=0.0.0.0:8000", "transaction_service.wsgi:application"]
