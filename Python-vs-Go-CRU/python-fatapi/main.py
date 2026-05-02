from fastapi import FastAPI

app = FastAPI()

@app.get("/hello")
async def world():
    return {"hello": "world"}

