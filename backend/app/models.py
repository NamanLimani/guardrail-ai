from typing import Optional
from sqlmodel import Field, SQLModel
import uuid
from datetime import datetime
from sqlalchemy import Column
from sqlmodel import Field, SQLModel, JSON # Import JSON

class User(SQLModel, table=True):
    # 'id' is the Primary Key. We use UUIDs because they are unique across distributed systems.
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    
    # 'index=True' makes searching by email faster
    email: str = Field(index=True, unique=True)
    
    # In a real app, we would hash this. For Day 3, we store it raw (we will fix this later).
    password_hash: Optional[str] = Field(default=None)
    
    full_name: Optional[str] = None
    role: str = Field(default="user")  # 'user' or 'admin'
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    auth_provider: str = Field(default='email')


class Document(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    filename: str
    file_size: int
    content_type: str
    file_path: str
    status: str = Field(default="pending")
    user_id: uuid.UUID = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    text_content: Optional[str] = Field(default=None, nullable=True)
    
    # NEW: Store the 384 numbers here
    # We use sa_column to tell Postgres "This is a JSON list"
    vector: Optional[list[float]] = Field(default=None, sa_column=Column(JSON)) 

    risk_score: int = Field(default=0)
  