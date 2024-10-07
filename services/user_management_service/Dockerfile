# Dockerfile for User Management Service
FROM python:3.9-slim

WORKDIR /user_management_service

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "--workers=3", "--bind=0.0.0.0:8000", "user_management_service.wsgi:application"]
