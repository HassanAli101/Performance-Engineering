from fastapi import FastAPI, HTTPException
from utils import ORMDatabaseOperations, UserNotFound

app = FastAPI()
orm_ops = ORMDatabaseOperations()


@app.on_event("startup")
async def startup():
    await orm_ops.startup()


@app.on_event("shutdown")
async def shutdown():
    await orm_ops.shutdown()


@app.get("/user/{user_id}")
async def get_user(user_id: int):
    try:
        return await orm_ops.get_by_id(user_id)
    except UserNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))