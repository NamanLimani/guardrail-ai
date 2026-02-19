from sqlmodel import SQLModel, create_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
import os

# 1. The Connection String
# Format: postgresql+asyncpg://user:password@host:port/database_name
# DATABASE_URL = "postgresql+asyncpg://naman:securepassword123@localhost:5432/guardrail"
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/guardrail")


# 2. Create the Async Engine
# echo=True means it will print every SQL query to the terminal (great for debugging)
engine = create_async_engine(DATABASE_URL, echo=True, future=True)

# 3. Create the Session Factory
# This generates a "Session" for each request to talk to the DB
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# 4. Dependency Injection
# This function will be used in our API routes to get a DB connection
async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session

# 5. Initialization Function
# We will call this when the app starts to create tables automatically
async def init_db():
    async with engine.begin() as conn:
        # await conn.run_sync(SQLModel.metadata.drop_all) # Uncomment to reset DB
        await conn.run_sync(SQLModel.metadata.create_all)