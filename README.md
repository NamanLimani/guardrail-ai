# 🛡️ GuardRail AI

**An Enterprise-Grade Serverless AI Document Intelligence & PII Redaction Pipeline**

GuardRail AI is a full-stack, cloud-native application designed to securely process, redact, and query sensitive documents. It leverages advanced Natural Language Processing (NER) to automatically detect and mask Personally Identifiable Information (PII) before using Retrieval-Augmented Generation (RAG) to allow users to semantically chat with their data.

## 🚀 Key Features

* **Zero-Trust Authentication:** Secure JWT-based sessions with seamless Google OAuth 2.0 integration.
* **Automated PII Redaction:** Deep learning NER pipeline that instantly masks Names, Organizations, Locations, Emails, URLs, SSNs, and Credit Cards.
* **Dynamic Risk Scoring:** Automatically calculates a security "Risk Score" based on the density and type of sensitive data found in a document.
* **Semantic Search (RAG):** Converts documents into high-dimensional vector embeddings for highly accurate, context-aware chatbot responses.
* **Multi-Modal Input:** Talk directly to your documents using voice commands powered by Whisper AI.
* **Serverless Cloud Architecture:** Fully decoupled frontend, backend, and database infrastructure designed to scale to zero.

## 🏗️ Architecture & Tech Stack

* **Frontend:** Next.js (React), Tailwind CSS, Axios, deployed on **Vercel**.
* **Backend:** Python, FastAPI, SQLAlchemy (Async), deployed via Docker on **Render**.
* **Database:** PostgreSQL with `pgvector`, hosted on **Neon Serverless DB**.
* **AI Inference Engine:**
* **LLM & Audio:** Groq API (Llama-3 & Whisper).
* **Embeddings:** Hugging Face Serverless API (`all-MiniLM-L6-v2`).
* **NER (Redaction):** Hugging Face Serverless API (`bert-base-NER`).



---

## 📂 Codebase Map: How the Backend Works

The backend is built using a modern microservice design pattern. Every file has a single, strictly defined responsibility.

### Core Application

* **`main.py` (The Central Nervous System):** The entry point of the FastAPI application. It wires all the microservices together, manages CORS security, initializes the database on boot, and exposes all the REST API endpoints (`/upload/`, `/chat/`, `/auth/`, `/documents/`).
* **`db.py` (The Database Engine):** Manages the asynchronous connection to the PostgreSQL database. It establishes the SQLAlchemy engine and safely intercepts cloud-specific driver variations (like enforcing `ssl=require` for asyncpg).
* **`models.py` (The Blueprint):** Defines the database schemas using SQLModel. It outlines the strict data structures and relational keys for `User` and `Document` entities.
* **`auth.py` (The Security Bouncer):** Centralizes all identity logic. It handles Argon2/Bcrypt password hashing, generates stateless JWT access tokens, and validates incoming Google OAuth ID tokens directly with Google's servers.
* **`config.py` (The Vault):** Safely parses and loads all `.env` secrets and API keys so they are never hardcoded in the logic.

### AI & Data Pipeline (`/core/`)

* **`parser.py` (The Reader):** Handles raw data ingestion. It attempts to extract clean text from PDFs using `pdfplumber`. If it detects an image-based PDF, it automatically falls back to utilizing Tesseract OCR to scan the document pixel-by-pixel.
* **`ner.py` (The Censor):** The Named Entity Recognition engine. It streams text to a BERT deep learning model to locate and classify contextual PII (like Names and Organizations). It also runs an aggressive Regex fallback layer to catch distorted Emails, URLs, and SSNs. Finally, it tallies the findings to calculate the document's overall Risk Score.
* **`rag.py` (The Librarian):** The embedding engine. It communicates with the Hugging Face `v1/embeddings` API to mathematically convert the redacted text into 384-dimensional vectors. This allows the system to calculate cosine similarity and find the exact paragraphs relevant to a user's question.
* **`chat.py` (The Speaker):** The LLM and Voice orchestrator. It connects to Groq's ultra-low-latency Inference Engine. It takes the user's prompt, injects the vectorized context from the database, and streams the AI's response back to the frontend in real-time chunks. It also handles `.wav` audio processing for voice commands.

---

## ⚙️ The Data Flow: What happens when you upload a document?

1. **Ingestion:** The Next.js UI sends the PDF to the FastAPI `/upload/` endpoint. The file is temporarily saved to the server.
2. **Extraction:** A background task is triggered. `parser.py` extracts the raw text (using OCR if necessary).
3. **Sanitization:** The raw text is passed to `ner.py`, which censors all sensitive data and calculates a risk score.
4. **Vectorization:** The sanitized text is passed to `rag.py`, which generates mathematical embeddings of the text.
5. **Storage:** The fully processed, safe text, its vector array, and its risk score are permanently saved to the Neon PostgreSQL database.

