from slowapi import _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware

import state.config
from api.api import router as api_router
from core.setup import setup_database
from fastapi import FastAPI
from state.config import limiter
from ws.websocket import router as websocket_router

app = FastAPI()

app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.include_router(websocket_router)
app.include_router(api_router)

setup_database()
