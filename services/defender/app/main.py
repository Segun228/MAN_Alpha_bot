from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
import asyncio
import os
import logging
from dotenv import load_dotenv
from fastapi import Response
from prometheus_client import generate_latest, REGISTRY
from .kafka_producer import ensure_topic_exists, build_log_message
import json
from prometheus_client import Counter, Histogram, generate_latest, REGISTRY
from fastapi import Request
from .recomendations import check_prompt
from .app_requests import get_summary
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse


load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

KAFKA_LOGS_TOPIC = os.getenv("KAFKA_LOGS_TOPIC")


REQUEST_COUNT = Counter('bot_http_requests_total', 'Total Bot HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('bot_http_request_duration_seconds', 'Bot HTTP request duration')
BOT_KAFKA_MESSAGES = Counter('bot_kafka_messages_processed_total', 'Total Bot Kafka messages processed', ['topic', 'status'])

@asynccontextmanager
async def lifespan(app: FastAPI):
    await ensure_topic_exists()
    try:
        yield
    finally:
        logging.info("Shutting down defender...")



app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    start_time = asyncio.get_event_loop().time()
    
    response = await call_next(request)
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    duration = asyncio.get_event_loop().time() - start_time
    REQUEST_DURATION.observe(duration)
    
    return response




@app.post("/defend")
async def defend_prompt(request: Request):
    try:
        data = await request.json()
        telegram_id = data.get("telegram_id", "undefined")
        prompt = data.get("prompt")
        
        if not telegram_id:
            raise HTTPException(status_code=400, detail="telegram_id is required")
        if not prompt:
            raise HTTPException(status_code=400, detail="prompt is required")
        words_count = data.get("words_count")

        await build_log_message(
            telegram_id=telegram_id,
            action="analyze_prompt",
            source="defender_endpoint", 
            payload={"has_prompt": bool(prompt)},
            platform="mixed",
            level="INFO",
            env="prod",
            request_method="POST",
            request_body=str(data)[:500],
            response_code=200,
            user_id=telegram_id,
            is_authenticated=True
        )

        result = await check_prompt( 
            prompt=prompt,
            words_count=words_count
        )
        logging.info(f"Request {prompt} is {'safe' if result.get('is_safe') else 'NOT safe'}")
        logging.info(f"{result.get('is_safe')}")
        return JSONResponse(
            content=result,
            status_code=200
        )

    except HTTPException:
        raise
    except Exception as e:
        logging.exception(f"Error in defender endpoint: {e}")
        return JSONResponse(
            content={"error": "Internal server error"},
            status_code=500
        )



@app.post("/defend/multiple")
async def defend_prompt_multiple(request: Request):
    try:
        data = await request.json()
        telegram_id = data.get("telegram_id", "undefined")
        prompt = data.get("prompt")
        
        if not telegram_id:
            raise HTTPException(status_code=400, detail="telegram_id is required")
        if not prompt:
            raise HTTPException(status_code=400, detail="prompt is required")
        words_count = data.get("words_count")
        if isinstance(prompt, str):
            result = await check_prompt( 
                prompt=prompt,
                words_count=words_count
            )
            return JSONResponse(
                content=result,
                status_code=200
            )
        elif isinstance(prompt, list):
            tasks = []
            prompt_map = {} 
            
            for i, pro in enumerate(prompt):
                if isinstance(pro, str):
                    task = check_prompt(
                        prompt=pro,
                        words_count=words_count
                    )
                    tasks.append(task)
                    prompt_map[len(tasks) - 1] = {"original_prompt": pro, "index": i}
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            resp = []
            for i, result in enumerate(results):
                original_data = prompt_map.get(i, {})
                
                if isinstance(result, Exception):
                    resp.append({
                        "index": original_data.get("index", i),
                        "original_prompt": original_data.get("original_prompt", ""),
                        "is_safe": False,
                        "error": str(result),
                        "success": False
                    })
                elif result:
                    resp.append({
                        "index": original_data.get("index", i),
                        "original_prompt": original_data.get("original_prompt", ""),
                        "is_safe": result.get("is_safe", False),
                        "response": result.get("response", ""),
                        "success": result.get("success", False)
                    })
                else:
                    resp.append({
                        "index": original_data.get("index", i),
                        "original_prompt": original_data.get("original_prompt", ""),
                        "is_safe": False,
                        "error": "Empty response",
                        "success": False
                    })
            resp.sort(key=lambda x: x["index"])
            
            return JSONResponse(
                content={
                    "success": True,
                    "results": resp,
                    "total_count": len(resp),
                    "safe_count": len([r for r in resp if r.get("is_safe")]),
                    "unsafe_count": len([r for r in resp if not r.get("is_safe")])
                },
                status_code=200
            )
        
        return JSONResponse(
            content={"error": "Invalid request field types"},
            status_code=400
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.exception(f"Error in defender endpoint: {e}")
        return JSONResponse(
            content={"error": "Internal server error"},
            status_code=500
        )




@app.get("/metrics")
async def metrics():
    return Response(
        content=generate_latest(REGISTRY),
        media_type="text/plain"
    )



@app.get("/health")
async def ping(request: Request):
    return {"status": "ok"}