# ft_transcendence

## FastAPI first steps :

```
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}
```

this code is the initialization of the fastapi framework . using this command :
```
fastapi dev
```
you can start and run the server ! ╰(*°▽°*)╯