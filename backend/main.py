from fastapi import FastAPI, Form
from typing import Annotated

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/login/")
async def login(username: Annotated[str, Form()], password: Annotated[str, Form()]):
    return {"username": username}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}
