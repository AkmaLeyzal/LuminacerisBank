# Stage 1: Build the application
FROM python:3.10.12-slim-bullseye AS build

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /LuminacerisBank/microservices/services/auth_service

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy application code
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Stage 2: Production-ready image
FROM python:3.10.12-slim-bullseye

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /LuminacerisBank/microservices/services/auth_service

# Copy dependencies from the build stage
COPY --from=build /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages

# Copy the app files from the build stage
COPY --from=build /LuminacerisBank/microservices/services/auth_service /LuminacerisBank/microservices/services/auth_service

# Expose the port for the app
EXPOSE 8000

# Command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "auth_service.wsgi:application"]
