from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
import jwt
from app.core.config import SECRET_KEY, ALGORITHM

# 1. Setup the Hashing Config
# We tell Passlib to use "bcrypt" as our hashing algorithm.
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# 2. Function to Hash a Password (Registration)
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# 3. Function to Verify a Password (Login)
# We will use this later when we build the Login API.
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    # "sub" is a standard JWT field for "Subject" (the user ID/email)
    to_encode.update({"exp": expire})
    
    # Create the JWT
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt