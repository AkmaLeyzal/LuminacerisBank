FROM python:3.10.12-slim-bullseye AS build

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /LuminacerisBank/microservices/services/transaction_service

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install wheel && \
    pip install -r requirements.txt

RUN pip install --force-reinstall gunicorn

COPY . .

RUN python manage.py collectstatic --noinput

FROM python:3.10.12-slim-bullseye

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ENV PYTHONPATH=/LuminacerisBank/microservices/services/transaction_service

WORKDIR /LuminacerisBank/microservices/services/transaction_service

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev \
    curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install wheel && \
    pip install -r requirements.txt && \
    pip install --force-reinstall gunicorn && \
    ln -s /usr/local/bin/gunicorn /usr/bin/gunicorn

COPY --from=build /LuminacerisBank/microservices/services/transaction_service /LuminacerisBank/microservices/services/transaction_service
COPY --from=build /LuminacerisBank/kafka_cloud /LuminacerisBank/kafka_cloud

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8004", "transaction_service.wsgi:application", "--workers", "3", "--timeout", "60"]