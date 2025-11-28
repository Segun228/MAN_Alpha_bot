FROM python:3.11-slim

# --- Системные зависимости ---
RUN apt-get update && apt-get install -y git && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# --- Обновление pip ---
RUN pip install --upgrade pip

# --- Установка зависимостей ---
RUN pip install \
    fastapi \
    uvicorn \
    torch \
    transformers \
    accelerate \
    sentencepiece \
    protobuf

WORKDIR /app

COPY . /app

EXPOSE 8085

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8085"]
