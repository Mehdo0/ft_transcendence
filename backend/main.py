from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware

import state.config
from state.config import limiter

from api.api import router as api_router
from ws.websocket import router as websocket_router

# CRITICAL FIX: Import directly from database, NOT from setup
from core.database import setup_database

app = FastAPI()

app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.include_router(websocket_router)
app.include_router(api_router)

# Safely create the database tables at the very end of the boot sequence
setup_database()