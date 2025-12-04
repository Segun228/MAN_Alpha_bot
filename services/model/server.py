import logging
import os
from typing import List, Optional
import gc
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM
from dotenv import load_dotenv
from optimum.intel.openvino import OVModelForCausalLM
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
    logging.info("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME,
        trust_remote_code=True,
        token=hf_token
    )
    torch.set_grad_enabled(False)
    model = OVModelForCausalLM.from_pretrained(
        MODEL_NAME,
        export=True,
        load_in_8bit=True,
        trust_remote_code=True,
        token=hf_token,
        ov_config={
            "NUM_STREAMS": 1,          
            "INFERENCE_NUM_THREADS": 4,
            "INFERENCE_PRECISION_HINT": "int8"
        }
    )
    model.eval()
    logging.info("Model loaded successfully.")
except Exception as e:
    logging.error(f"Model load error: {e}")
    raise


@app.post("/api/v1/chat/completions", response_model=ChatCompletionResponse)
async def openai_chat_completions(req: ChatCompletionRequest):
    try:
        messages = [{"role": m.role, "content": m.content} for m in req.messages]
        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        inputs = tokenizer(prompt, return_tensors="pt").to("cpu")
        prompt_len = inputs["input_ids"].shape[1]
        with torch.inference_mode():
            output = model.generate(
                **inputs,
                max_new_tokens=req.max_tokens,
                temperature=req.temperature,
                top_p=req.top_p,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
        generated_text = tokenizer.decode(output[0][prompt_len:], skip_special_tokens=True)
        completion_tokens = output[0].shape[0] - prompt_len
        del inputs
        del output
        gc.collect()
        return ChatCompletionResponse(
            id="chatcmpl-local",
            object="chat.completion",
            model=req.model,
            choices=[ChatCompletionChoice(
                index=0,
                message=ChatMessage(role="assistant", content=generated_text),
                finish_reason="stop"
            )],
            usage=Usage(
                prompt_tokens=prompt_len,
                completion_tokens=completion_tokens,
                total_tokens=prompt_len + completion_tokens
            )
        )
    except Exception as e:
        logging.error(f"Generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "ok"}
