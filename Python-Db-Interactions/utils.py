from dotenv import load_dotenv
import os
import psycopg2
import asyncpg
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base, mapped_column
from sqlalchemy import Integer, String, select

load_dotenv('../.env')

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

class SyncDatabaseOperations:

    def __init__(self):
        self.sync_conn = psycopg2.connect(DB_URL)
        self.sync_conn.autocommit = True
    
    def get_by_id(self, id: int):
        with self.sync_conn.cursor() as cur:
            cur.execute("SELECT id, name, email from users WHERE id = %s", (id,))
            row = cur.fetchone()
            if not row:
                raise UserNotFound("User not found with given ID")
            return {"id": row[0], "name": row[1], "email": row[2]}

class AsyncDatabaseOperations:

    def __init__(self):
        self.pool: asyncpg.Pool = None

    async def startup(self):
        self.pool = await asyncpg.create_pool(
            dsn=DB_URL,
            min_size=5,
            max_size=10
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

class ORMDatabaseOperations:

    def __init__(self):
        self.engine = None
        self.session_maker: async_sessionmaker[AsyncSession] = None

    async def startup(self):
        self.engine = create_async_engine(
            ASYNC_DB_URL,
            echo=False,
            pool_size=5,
            max_overflow=10
        )

        self.session_maker = async_sessionmaker(
            bind=self.engine,
            expire_on_commit=False
        )

    async def shutdown(self):
        await self.engine.dispose()

    async def get_by_id(self, user_id: int):
        async with self.session_maker() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()

            if not user:
                raise UserNotFound("User not found with given ID")

            return {
                "id": user.id,
                "name": user.name,
                "email": user.email
            }