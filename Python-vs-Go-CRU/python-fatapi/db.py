from dotenv import load_dotenv
import os
import psycopg2
import asyncpg
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base, mapped_column
from sqlalchemy import Integer, String, select

load_dotenv('../../.env')

DB_URL = os.getenv('DB_URL')
ASYNC_DB_URL = os.getenv('ASYNC_DB_URL')
Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String)
    email = mapped_column(String)

class UserNotFound(Exception):
    pass


class AsyncDatabaseOperations:

    def __init__(self):
        self.pool: asyncpg.Pool = None

    async def startup(self):
        self.pool = await asyncpg.create_pool(
            dsn=DB_URL
        )
    async def shutdown(self):
        await self.pool.close()
    
    async def get_by_id(self, id: int):
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, name, email FROM users WHERE id = $1", id
            )
            if not row:
                raise UserNotFound("User not found with given ID")
            return {"id": row["id"], "name": row["name"], "email": row["email"]}
