from api.api import router as api_router
from core.setup import setup_database
from fastapi import FastAPI
from ws.websocket import router as websocket_router

app = FastAPI()

app.include_router(websocket_router)
app.include_router(api_router)

setup_database()
