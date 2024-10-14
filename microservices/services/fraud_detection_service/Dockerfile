# Stage 1: Build Frontend React
FROM node:14-alpine AS frontend

WORKDIR /usr/src/fraud_detection_service/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm install

COPY frontend/ .
RUN npm run build

# Stage 2: Build Backend Django
FROM python:3.9-slim AS backend

WORKDIR /usr/src/fraud_detection_service/backend

COPY backend/requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY backend/ .

# Copy frontend build ke dalam backend static files
COPY --from=frontend /usr/src/fraud_detection_service/frontend/build /usr/src/fraud_detection_service/backend/static

# Django menggunakan port 8000
EXPOSE 8000

# Jalankan server Django menggunakan Gunicorn
CMD ["gunicorn", "--workers=3", "--bind=0.0.0.0:8000", "fraud_detection_service.wsgi:application"]
