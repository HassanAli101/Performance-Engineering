from fastapi import FastAPI
from db import UserNotFound, AsyncDatabaseOperations
import random

app = FastAPI()
async_ops = AsyncDatabaseOperations()

@app.get("/hello")
async def world():
    return {"hello": "world"}

@app.on_event("startup")
async def startup():
    await async_ops.startup()

@app.on_event("shutdown")
async def shutdown():
    await async_ops.shutdown()

@app.get("/getRandomUser")
async def get_user():
    try:
        user_id = random.randint(1,1000)
        return await async_ops.get_by_id(user_id)
    except UserNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/updateRandomUser")
async def get_user():
    try:
        user_id = random.randint(1,1000)
        return await async_ops.update_by_id(user_id)
    except UserNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
