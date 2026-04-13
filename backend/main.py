from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()

@app.get("/api/data")
async def get_data():
    return {"message": "Data from the Python backend"}

app.mount("/", StaticFiles(directory="frontend_dist", html=True), name="frontend")

@app.exception_handler(404)
async def not_found_exception_handler(request, exc):
    return FileResponse("frontend_dist/index.html")