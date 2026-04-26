from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.database import setup_database, fetch_user_stats, add_user, reset_database
import random
import os

# setup variables
setup_database()
app = FastAPI()

# allow SvelteKit dev server
# we might want to switch to using SvelteKit as a proxy to avoid giving direct acces to API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# default route
@app.get("/")
async def root():
    return {"message": "Hello World"}


# get user stats
@app.get("/api/users/{user_id}/stats")
async def get_user_stats(user_id: int):
    # Ask the database file to do the heavy lifting
    row = fetch_user_stats(user_id)
    if row is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"username": row["username"], "wins": row["wins"], "losses": row["losses"]}


@app.get("/api/users/add_user/")
async def db_add(username: str = "drawer"):
    new_user_id = add_user(username)
    row = fetch_user_stats(new_user_id)
    if row is None:
        raise HTTPException(status_code=500, detail="User not added")
    return {"user_id": row["id"], "username": row["username"], "added": "yes"}


@app.get("/destroy")
async def destroy_db():
    reset_database()
    return {"data": "erased"}


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.join(BASE_DIR, "list.txt")


@app.get("/api/word_list/get_word/")
async def get_random_word(num: int = 1):
    if not os.path.exists(FILE_PATH):
        raise HTTPException(
            status_code=500, detail="Word list file not found on server."
        )
    with open(FILE_PATH) as inp:
        data = inp.read().split()
    if not data:
        raise HTTPException(status_code=500, detail="Word list is empty.")
    word = random.choice(data)
    return {"word": word}


# ce code est censer etre fonctionnel lorsque le frontend sera operationnel
# app.mount("/", StaticFiles(directory="backend/frontend_dist", html=True), name="frontend")
# @app.exception_handler(404)
# async def not_found_exception_handler(request, exc):
#    return FileResponse("frontend_dist/index.html")
