FROM python:3.10-slim

RUN apt-get update && apt-get install -y ffmpeg

RUN pip install --no-cache-dir faster-whisper fastapi uvicorn[standard] python-multipart

WORKDIR /app
COPY services/stt /app

EXPOSE 8096

CMD ["uvicorn", "speech:app", "--host", "0.0.0.0", "--port", "8096"]
