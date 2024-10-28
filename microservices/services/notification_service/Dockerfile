# Stage 1: Build the application
FROM python:3.10.12-slim-bullseye AS build

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /LuminacerisBank/microservices/services/notification_service

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the project
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Stage 2: Run the application
FROM python:3.10.12-slim-bullseye

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /LuminacerisBank/microservices/services/notification_service

# Install dependencies
COPY --from=build /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=build /LuminacerisBank/microservices/services/notification_service /LuminacerisBank/microservices/services/notification_service

# Expose port
EXPOSE 8000

# Start Gunicorn
CMD ["gunicorn", "notification_service.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--worker-class", "gevent"]
