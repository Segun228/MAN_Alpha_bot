FROM python:3.11-slim

WORKDIR /app

ENV LOG_LEVEL=INFO
ENV LOG_TO_FILE=true
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8086", "--timeout-keep-alive", "160"]