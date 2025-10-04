FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libgl1-mesa-glx \
    libglib2.0-dev \
    libsm6 \
    libxrender1 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml poetry.lock ./
COPY src/ src/
COPY build/ build/

RUN pip install --upgrade pip \
    && pip install poetry \
    && poetry config virtualenvs.create false \
    && poetry install --only main

# Startbefehl für die Anwendung
CMD ["python", "src/cellsepi/main.py"]
