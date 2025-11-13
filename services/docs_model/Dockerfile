FROM python:3.11-slim

WORKDIR /docs_model

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN adduser --disabled-password --gecos 'Docs generation' docsbot
USER docsbot

EXPOSE 8084
CMD ["uvicorn", "docs_model:app", "--host", "0.0.0.0", "--port", "8084"]