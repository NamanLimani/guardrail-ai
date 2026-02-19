from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from app.db import init_db, get_session
from app.models import User  
# from app.core.security import get_password_hash
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import select
# from app.core.security import verify_password, create_access_token
from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import timedelta
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import PyJWTError
import jwt
from app.core.config import SECRET_KEY, ALGORITHM
import shutil
import os
from fastapi import UploadFile, File
import uuid
from app.models import Document # Make sure Document is imported!
from fastapi import BackgroundTasks
from app.core.parser import extract_text_from_pdf
from app.db import async_session
# from app.core.redactor import redact_text
from app.core.rag import embedding_engine
import numpy as np
from fastapi.middleware.cors import CORSMiddleware
from app.core.chat import chat_engine
from pydantic import BaseModel
from typing import List, Dict
from fastapi.responses import StreamingResponse
from app.core.ner import ner_redactor
import os
from pydantic import BaseModel
from app.auth import (
    get_password_hash, 
    verify_password, 
    create_access_token, 
    verify_google_token  # <--- The new function!
)


class GoogleAuthRequest(BaseModel):
    token: str


app = FastAPI()

# Get allowed origins from Env (Default to localhost for dev)
origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
origins = origins_str.split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # Uses the variable now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# This tells FastAPI: "The client should send the token in the Header as 'Bearer <token>'"
# The tokenUrl="token" tells Swagger UI where to go to get the token.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 1. Decode the Token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except PyJWTError:
        raise credentials_exception
    
    # 2. Find the User in DB
    query = select(User).where(User.email == email)
    result = await session.exec(query)
    user = result.first()
    
    if user is None:
        raise credentials_exception
        
    return user

# async def process_document(doc_id: uuid.UUID, file_path: str, session_factory):
#     print(f"Processing document {doc_id}...")
    
#     # 1. Extract
#     raw_text = extract_text_from_pdf(file_path)
    
#     status = "failed"
#     clean_text = ""
#     doc_vector = None
    
#     if raw_text:
#         # 2. Redact
#         clean_text = ner_redactor.redact(raw_text)
#         status = "completed"
        
#         # 3. Vectorize (The New Step)
#         try:
#             # Vectorize the FIRST 1000 characters (Context Window)
#             doc_vector = embedding_engine.generate_embedding(clean_text[:1000])
#         except Exception as e:
#             print(f"--- RAG ERROR: {e} ---")
    
#     # 4. Update DB
#     async with session_factory() as session:
#         doc = await session.get(Document, doc_id)
#         if doc:
#             doc.text_content = clean_text
#             doc.status = status
#             doc.vector = doc_vector
#             session.add(doc)
#             await session.commit()
#             print(f"Document {doc_id} processed, redacted & vectorized.")

async def process_document(doc_id: uuid.UUID, file_path: str, session_factory):
    print(f"Processing document {doc_id}...")
    
    # 1. Extract
    raw_text = extract_text_from_pdf(file_path)
    
    status = "failed"
    clean_text = ""
    doc_vector = None
    risk_score = 0  # <--- Initialize Risk Score
    
    if raw_text:
        try:
            # 2. Redact & Count Stats (The NER Update)
            # ner_redactor.redact now returns (text, stats_dict)
            clean_text, stats = ner_redactor.redact(raw_text) 
            
            status = "completed"
            
            # 3. Calculate Risk Score
            # High Risk (10 pts): SSN, Credit Cards
            # Low Risk (1 pt): Names, Emails, Orgs
            # 3. Calculate Risk Score
            # CRITICAL (Instant High Risk)
            critical_score = (stats.get("SSN", 0) * 100) + \
                             (stats.get("CREDIT_CARD", 0) * 100)
            
            # SENSITIVE (Medium Risk)
            sensitive_score = (stats.get("EMAIL", 0) * 10) + \
                              (stats.get("PHONE", 0) * 10) # If you add phone later
            
            # CONTEXT (Low Risk - weighted very low)
            context_score = (stats.get("PER", 0) * 1) + \
                            (stats.get("ORG", 0) * 0.5) + \
                            (stats.get("LOC", 0) * 0.5)
                            
            risk_score = int(critical_score + sensitive_score + context_score)
            
            # 4. Vectorize
            # Vectorize the FIRST 1000 characters (Context Window)
            doc_vector = embedding_engine.generate_embedding(clean_text[:1000])
            
        except Exception as e:
            print(f"--- PROCESSING ERROR: {e} ---")
            status = "failed"
    
    # 5. Update DB
    async with session_factory() as session:
        # Re-fetch the doc using the new session
        doc = await session.get(Document, doc_id)
        if doc:
            doc.text_content = clean_text
            doc.status = status
            doc.vector = doc_vector
            doc.risk_score = risk_score  # <--- Save the Score
            
            session.add(doc)
            await session.commit()
            print(f"Document {doc_id} processed. Risk Score: {risk_score}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Startup: Connecting to Database...")
    await init_db()
    yield
    print("Shutdown: Closing connections...")

app = FastAPI(title="GuardRail AI API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], # The URL of your Frontend
    allow_credentials=True,
    allow_methods=["*"], # Allow all types of requests (GET, POST, etc.)
    allow_headers=["*"], # Allow all headers (Authentication, etc.)
)

class ChatRequest(BaseModel):
    query: str
    history: List[Dict[str, str]] = [] # List of {"role": "user", "content": "..."}


@app.get("/")
async def health_check():
    return {"status": "active", "message": "GuardRail AI is online"}

# 2. POST endpoint to create a user
@app.post("/users/")
async def create_user(user: User, session: AsyncSession = Depends(get_session)):
    """
    Creates a new user. 
    Hashes the password before saving to DB.
    """
    # 1. Hash the password (The most important line)
    # We take the plain text 'secret123' the user sent, and overwrite it with the hash.
    user.password_hash = get_password_hash(user.password_hash)
    
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

# 3. GET endpoint to list all users
@app.get("/users/")
async def read_users(session: AsyncSession = Depends(get_session)):
    result = await session.exec(select(User))
    users = result.all()
    return users


@app.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session)
):
    # 1. Find the user by Email
    # Note: OAuth2 forms use 'username' field, but we treat it as email
    query = select(User).where(User.email == form_data.username)
    result = await session.exec(query)
    user = result.first()

    # 2. Verify User and Password
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Create the Token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    # 4. Return the Token
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/auth/google")
async def google_login(request: GoogleAuthRequest, session: AsyncSession = Depends(get_session)):
    # 1. Verify the token with Google
    google_user = verify_google_token(request.token)
    
    if not google_user:
        raise HTTPException(status_code=400, detail="Invalid Google Token")

    # 2. Check if user exists in DB
    email = google_user["email"]
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    # 3. If user doesn't exist, Create them (Auto-Registration)
    if not user:
        user = User(
            email=email,
            full_name=google_user["name"],
            password_hash=None, # Google users have no password
            role="user",
            auth_provider="google"
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

    # 4. Generate OUR Session Token (JWT)
    # This logs them in just like a password user
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role},
        expires_delta=timedelta(minutes=60)
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Fetches the current logged-in user's profile.
    This route is PROTECTED.
    """
    return current_user

UPLOAD_DIR = "uploads"

@app.post("/upload/")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    # 1. Generate the ID first
    file_id = uuid.uuid4()
    
    # 2. Setup the path (Inside the function is safer!)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")
    
    # 3. Save the file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # --- DEBUG: Print what we just saved ---
    saved_size = os.path.getsize(file_path)
    print(f"--- UPLOAD DEBUG: Saved '{file.filename}' to '{file_path}'")
    print(f"--- UPLOAD DEBUG: File Size on Disk: {saved_size} bytes ---")
    # ---------------------------------------

    # 4. Create DB Record
    doc = Document(
        id=file_id,
        filename=file.filename,
        file_size=saved_size, # Use the actual saved size
        content_type=file.content_type,
        file_path=file_path,
        user_id=current_user.id,
        status="processing"
    )
    
    session.add(doc)
    await session.commit()
    await session.refresh(doc)
    
    # 5. Trigger Background Task
    background_tasks.add_task(process_document, doc.id, file_path, async_session)
    
    return {"message": "Upload started", "document_id": doc.id, "status": "processing"}


@app.get("/documents/")
async def list_documents(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get all documents owned by the logged-in user.
    """
    query = select(Document).where(Document.user_id == current_user.id)
    result = await session.exec(query)
    documents = result.all()
    return documents


@app.get("/documents/{doc_id}")
async def get_document(doc_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    doc = await session.get(Document, doc_id)
    return doc


def cosine_similarity(vec1, vec2):
    """
    Returns a score between 0 (different) and 1 (identical).
    """
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

@app.post("/search/")
async def search_documents(
    query: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Semantic Search: Finds the document most relevant to your question.
    """
    # 1. Convert User's Question to a Vector
    query_vector = embedding_engine.generate_embedding(query)
    
    # 2. Get All User's Documents
    # (In production, we would let the DB do this math, but Python is fine for <1000 docs)
    result = await session.exec(select(Document).where(Document.user_id == current_user.id))
    docs = result.all()
    
    results = []
    for doc in docs:
        if doc.vector:
            # 3. Calculate "Closeness" Score
            score = cosine_similarity(query_vector, doc.vector)
            if score > 0.01: # Filter out irrelevant noise
                results.append({
                    "filename": doc.filename,
                    "score": float(score),
                    "preview": doc.text_content[:200] + "..."
                })
    
    # 4. Sort by Highest Score
    results.sort(key=lambda x: x["score"], reverse=True)
    
    return results


@app.post("/chat/")
async def chat_with_documents(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    # 1. Vector Search
    query_vector = embedding_engine.generate_embedding(request.query)
    result = await session.exec(select(Document).where(Document.user_id == current_user.id))
    docs = result.all()
    
    # Calculate Scores
    scored_docs = []
    for doc in docs:
        if doc.vector:
            score = cosine_similarity(query_vector, doc.vector)
            if score > 0.01:
                scored_docs.append({
                    "filename": doc.filename,
                    "score": round(score, 4),
                    "text": doc.text_content
                })
    
    # Sort by Score
    scored_docs.sort(key=lambda x: x["score"], reverse=True)
    
    # 2. Select Top 3
    top_docs = scored_docs[:3]
    context_text = "\n\n---\n\n".join([d["text"] for d in top_docs]) if top_docs else ""
    
    # 3. Prepare Debug Data (This is what we will show in the UI)
    debug_payload = {
        "context_sent_to_llm": context_text,
        "vector_matches": [{"filename": d["filename"], "score": d["score"]} for d in top_docs]
    }
    
    # 4. Return Streaming Response (Passing the debug data!)
    return StreamingResponse(
        chat_engine.generate_streaming_answer(request.query, context_text, request.history, debug_payload),
        media_type="application/x-ndjson" # New Line Delimited JSON
    )

@app.post("/transcribe/")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Receives an audio blob, saves it temporarily, and returns the text.
    """
    # 1. Save the temp file
    temp_filename = f"temp_{file.filename}"
    with open(temp_filename, "wb") as buffer:
        buffer.write(await file.read())

    # 2. Send to Groq
    text = chat_engine.transcribe_audio(temp_filename)

    # 3. Cleanup (Delete the temp file)
    if os.path.exists(temp_filename):
        os.remove(temp_filename)

    return {"text": text}