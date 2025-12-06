FROM python:3.11-slim

WORKDIR /conversation_model

RUN pip install --no-cache-dir \
    requests==2.32.5 \
    uvicorn==0.38.0 \
    fastapi==0.121.1 \
    pydantic==2.12.4 \
    dotenv==0.9.9 \
    aiohttp

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY . .

RUN adduser --disabled-password --gecos 'Conversation Model' conversationmodel
USER conversationmodel

EXPOSE 8090

CMD ["uvicorn", "conversation_model:app", "--host", "0.0.0.0", "--port", "8090", "--timeout-keep-alive", "160", "--log-level", "info"]