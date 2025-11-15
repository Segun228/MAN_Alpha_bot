FROM python:3.11-slim

WORKDIR /chat_model

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
COPY . .

RUN adduser --disabled-password --gecos 'Message generation' chatbot
USER chatbot

EXPOSE 8082
CMD ["uvicorn", "chat_model:app", "--host", "0.0.0.0", "--port", "8082"]