FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    libstdc++6 \
    libgomp1 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

RUN pip install "openvino>=2024.4.0"
RUN pip install "optimum-intel>=1.17.0"
RUN pip install "nncf>=2.8.0"

RUN pip install \
    fastapi \
    uvicorn[standard] \
    transformers \
    sentencepiece \
    protobuf \
    python-dotenv

WORKDIR /app
COPY services/model /app

EXPOSE 8088

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8095"]
