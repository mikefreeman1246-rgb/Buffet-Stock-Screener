import asyncio
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS
from app.database import init_db
from app.websocket import manager
from app.routers import screener, stocks, assumptions, pipeline, meta, tags

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Stock Value Screener", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(screener.router)
app.include_router(stocks.router)
app.include_router(assumptions.router)
app.include_router(pipeline.router)
app.include_router(meta.router)
app.include_router(tags.router)


@app.on_event("startup")
async def startup():
    init_db()
    asyncio.create_task(manager.start_heartbeat())


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.websocket("/ws/pipeline")
async def websocket_pipeline(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
