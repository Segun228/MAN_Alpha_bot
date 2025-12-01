from fastapi import FastAPI, UploadFile, File, HTTPException
from faster_whisper import WhisperModel
import tempfile
import os
import base64
import httpx

STT_ROUTE = os.getenv("STT_ROUTE", "local")
if STT_ROUTE != "local":
    STT_API_KEY = os.getenv("STT_API_KEY")
else:
    model = WhisperModel("small", device="cpu")

app = FastAPI()

async def local_stt(filepath: str) -> str:
    segments, info = model.transcribe(filepath, beam_size=5)
    return " ".join([s.text for s in segments])


async def remote_stt(filepath: str, file_format: str) -> str:
    if not STT_API_KEY:
        raise HTTPException(status_code=500, detail="Missing key")
    with open(filepath, "rb") as f:
        encoded_audio = base64.b64encode(f.read()).decode("utf-8")
    payload = {
        "model": "mistralai/voxtral-small-24b-2507",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Рапознай текст. Будь точен и ничего не придумывай.."
                    },
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": encoded_audio,
                            "format": file_format
                        }
                    }
                ]
            }
        ]
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            STT_ROUTE,
            headers={
                "Authorization": f"Bearer {STT_API_KEY}",
                "Content-Type": "application/json"
            },
            json=payload
        )

    if resp.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Model error: {resp.text}")

    data = resp.json()
    try:
        text = data["choices"][0]["message"]["content"][0]["text"]
        return text.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Invalid response format: {e}")


@app.post("/stt")
async def speech_to_text(file: UploadFile = File(...)):
    ext = (file.filename.split(".")[-1] or "wav").lower()
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    if STT_ROUTE.lower() == "local":
        text = await local_stt(tmp_path)
    else:
        text = await remote_stt(tmp_path, ext)
    return {"text": text}


@app.get("/")
async def root():
    return {"message": f"STT service running", "mode": STT_ROUTE}


@app.get("/health")
async def health_check():
    return {"status": "ok", "mode": STT_ROUTE}
