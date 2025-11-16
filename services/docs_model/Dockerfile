FROM python:3.11-slim

WORKDIR /docs_model

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
COPY . .

RUN adduser --disabled-password --gecos 'Docs generation' docsbot
USER docsbot

EXPOSE 8084
CMD ["uvicorn", "docs_model:app", "--host", "0.0.0.0", "--port", "8084", "--timeout-keep-alive", "60"]