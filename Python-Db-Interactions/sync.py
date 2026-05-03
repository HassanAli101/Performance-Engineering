from fastapi import FastAPI, HTTPException
from utils import SyncDatabaseOperations, UserNotFound

app = FastAPI()
sync_ops = SyncDatabaseOperations()

@app.get("/hello")
async def world():
    return {"hello": "world"}

@app.get("/user/{user_id}")
def get_user(user_id: int):
    try:
        return sync_ops.get_by_id(user_id)
    except UserNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


