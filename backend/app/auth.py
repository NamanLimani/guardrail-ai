from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from google.oauth2 import id_token
from google.auth.transport import requests
import os
from app.core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES # <--- IMPORT SHARED CONFIG

# Google Client ID
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

# Password Hashing Tool
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# --- PASSWORD FUNCTIONS ---
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# --- JWT FUNCTIONS ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- GOOGLE VERIFICATION ---
def verify_google_token(token: str):
    try:
        # Ask Google: "Is this token valid?"
        id_info = id_token.verify_oauth2_token(token, requests.Request(), GOOGLE_CLIENT_ID)

        # Security Check: Ensure token was issued for OUR app
        if id_info['aud'] != GOOGLE_CLIENT_ID:
            raise ValueError('Could not verify audience.')

        # Return the user info from Google
        return {
            "email": id_info['email'],
            "name": id_info.get('name'),
            "picture": id_info.get('picture')
        }
    except ValueError:
        return None
    except Exception as e:
        print(f"Google Token Verification Error: {e}")
        return None