from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import SQL

app = FastAPI()

app.mount("/", StaticFiles(directory="frontend_dist", html=True), name="frontend")

@app.get("/api/user/{user_id}/stats")
async def get_data():

@app.exception_handler(404)
async def not_found_exception_handler(request, exc):
    return FileResponse("frontend_dist/index.html")