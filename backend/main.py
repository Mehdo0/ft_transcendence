from ws.websocket import router as websocket_router
from api.api import router as api_router
from fastapi import FastAPI
from core.setup import setup_database

app = FastAPI()

app.include_router(websocket_router)
app.include_router(api_router)

setup_database()
