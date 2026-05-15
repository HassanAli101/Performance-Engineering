from fastapi import FastAPI
from utils import UserNotFound, AsyncDatabaseOperations

app = FastAPI()
async_ops = AsyncDatabaseOperations()

@app.on_event("startup")
async def startup():
    await async_ops.startup()

@app.on_event("shutdown")
async def shutdown():
    await async_ops.shutdown()

@app.get("/user/{user_id}")
async def get_user(user_id: int):
    try:
        return await async_ops.get_by_id(user_id)
    except UserNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
