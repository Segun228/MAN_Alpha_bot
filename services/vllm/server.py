import logging
import os
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM
from dotenv import load_dotenv
import torch

logging.basicConfig(level=logging.INFO)
load_dotenv()

app = FastAPI()

MODEL_NAME = "Qwen/Qwen2.5-3B-Instruct"
hf_token = os.getenv("HF_AUTH_TOKEN")

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: Optional[str] = MODEL_NAME
    messages: List[ChatMessage]
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    stream: Optional[bool] = False

class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class ChatCompletionChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: Optional[str] = "stop"

class ChatCompletionResponse(BaseModel):
    id: str
    object: str
    model: str
    choices: List[ChatCompletionChoice]
    usage: Usage

try:
    print("Loading tokenizer")
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME,
        trust_remote_code=True,
        use_auth_token=hf_token
    )
    print("Loading model")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        device_map="cpu",
        torch_dtype=torch.float32,
        trust_remote_code=True,
        use_auth_token=hf_token
    )

    model.eval()
    print("Model loaded successfully")

except Exception as e:
    logging.error(f"Model load error: {e}")
    raise


@app.get("/v1/models")
async def list_models():
    return {
        "object": "list",
        "data": [
            {"id": MODEL_NAME, "object": "model", "owned_by": "local", "permission": []}
        ]
    }

@app.get("/v1/models/{model_id}")
async def retrieve_model(model_id: str):
    if model_id != MODEL_NAME:
        raise HTTPException(status_code=404, detail="Model not found")
    return {"id": MODEL_NAME, "object": "model", "owned_by": "local", "permission": []}

@app.post("/api/v1/chat/completions", response_model=ChatCompletionResponse)
async def openai_chat_completions(req: ChatCompletionRequest):
    try:
        messages = [{"role": m.role, "content": m.content} for m in req.messages]
        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        prompt_len = inputs["input_ids"].shape[1]
        with torch.no_grad():
            output = model.generate(
                **inputs,
                max_new_tokens=req.max_tokens,
                temperature=req.temperature,
                top_p=req.top_p,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
        generated_text = tokenizer.decode(
            output[0][prompt_len:], 
            skip_special_tokens=True
        )
        completion_tokens = output[0].shape[0] - prompt_len
        return ChatCompletionResponse(
            id="chatcmpl-local",
            object="chat.completion",
            model=req.model,
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatMessage(role="assistant", content=generated_text),
                    finish_reason="stop"
                )
            ],
            usage=Usage(
                prompt_tokens=prompt_len,
                completion_tokens=completion_tokens,
                total_tokens=prompt_len + completion_tokens
            )
        )
    except Exception as e:
        logging.error(f"Generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    if api_key and URL and hf_token:
        return {"message": "Local OpenAI-Compatible API running", "status": "ok"}
    return {"message": "Business Assistant API key or URL not set", "status": "failed"}

@app.get("/health")
async def health_check():
    if api_key and URL and hf_token:
        return {"message": "Local OpenAI-Compatible API running", "status": "ok"}
    return {"message": "Business Assistant API key or URL not set", "status": "failed"}
