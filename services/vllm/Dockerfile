FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    libstdc++6 \
    libgomp1 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

RUN pip install torch --index-url https://download.pytorch.org/whl/cpu

RUN pip install \
    fastapi \
    uvicorn[standard] \
    transformers \
    accelerate \
    sentencepiece \
    protobuf

WORKDIR /app

COPY . /app

EXPOSE 8085

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8085"]
