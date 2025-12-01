from fastapi import FastAPI, UploadFile, File
from faster_whisper import WhisperModel
import tempfile

app = FastAPI()

model = WhisperModel("small", device="cpu")

@app.post("/stt")
async def speech_to_text(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    segments, info = model.transcribe(tmp_path, beam_size=5)
    text = " ".join([segment.text for segment in segments])
    return {"text": text}

@app.get("/")
async def root():
    return {"message": "STT model is running", "status": "ok"}

@app.get("/health")
async def health_check():
    return {"message": "STT model is running", "status": "ok"}
