FROM python:3.11-slim

WORKDIR /chat_model

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN adduser --disabled-password --gecos '' appuser
USER appuser

EXPOSE 3000
CMD ["uvicorn", "chat_model:app", "--host", "0.0.0.0", "--port", "3000"]