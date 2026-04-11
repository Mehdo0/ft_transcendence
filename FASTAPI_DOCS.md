## FastAPI first steps :

### install

first you'll have to run this command to install fastapi :

```sh
pip install fastapi && pip install fastapi[standard]
```

### init

```py
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}
```

this code is the initialization of the fastapi framework .
first it initiate the app , then define the return value thanks to an async function when the client access the "/" location with the get methods

### launch 

 using this command :
```sh
fastapi dev
```
you can start and run the server ! ╰(*°▽°*)╯


### Different Path

```py
@app.get("/items/{item_id}")
async def read_item(item_id):
    return {"item_id": item_id}
```

Here we can define this location "http://127.0.0.1:8000/items/foo" in the way that it returns "{"item_id": foo}" 

This technique can be used when you want a variable returned by the url like a username or else ; 

> [!TIP]
> The declaration ordering have it's importance in *fastapi* ; the first function declared has the priority and is going to be selected first by the program !

### Forms 

A form can be used to log users or register them 

```py
from typing import Annotated

from fastapi import FastAPI, Form

app = FastAPI()


@app.post("/login/")
async def login(username: Annotated[str, Form()], password: Annotated[str, Form()]):
    return {"username": username}
```

this will bind the login page url to send an html form to the client 

### docs

when you open your browser at http://127.0.0.1:8000/docs, you will see an automatic, interactive, API documentation

