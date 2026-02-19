# GuardRail AI - Engineering Journal

## Day 1: Foundation, Database, and User Management
**Date:** Feb 02, 2026 
**Focus:** Project Setup, Docker Architecture, Async Database Connectivity

### 1. Implementation Progress
* **Architecture:** Established a Monorepo structure separating `backend`, `frontend`, and `ml-engine`.
* **Backend Core:**
    * Initialized FastAPI with Uvicorn (ASGI Server).
    * Implemented `Lifespan` events to handle startup/shutdown logic.
* **Infrastructure (DevOps):**
    * Configured `docker-compose.yml` to spin up a **PostgreSQL 15** container.
    * Ensured data persistence using Docker Volumes (`postgres_data`).
* **Database Integration:**
    * Integrated **SQLModel** (ORM) for Python-to-SQL mapping.
    * Configured **AsyncPG** driver for non-blocking database queries.
    * Created the `User` table with UUID primary keys.
    * Successfully implemented the `POST /users/` endpoint.

### 2. Challenges & Solutions
| Issue | Root Cause | Solution |
| :--- | :--- | :--- |
| **Error: `ValueError: greenlet library is required`** | SQLAlchemy's AsyncIO wrapper requires the `greenlet` library to handle context switching, but it wasn't installed. | Installed `greenlet` via pip (`pip install greenlet`). |
| **Error: `TypeError: expected datetime... got 'str'`** | The API request payload included a raw string (`"2026-02-02..."`) for `created_at`, but the database driver expects a Python Datetime object. | **Fix:** Removed `created_at` and `id` from the request JSON. Allowed the backend to generate these values automatically using `default_factory`. |
| **Log Noise (`echo=True`)** | The terminal was flooded with raw SQL logs. | **Decision:** Kept `echo=True` for development debugging but noted to set it to `False` in production for security/performance. |

### 3. Key Concepts Learned
* **Async/Await:** Used for I/O-bound tasks (Database waiting) vs CPU-bound tasks.
* **Session Refresh:** Learned that `session.refresh(user)` is required after a commit to pull generated data (like IDs and Timestamps) back from the DB into Python memory.
* **Docker Isolation:** Running the DB in a container avoids polluting the local OS and mimics production environments.

### 4. Current System Status
* ✅ **API:** Online (Port 8000)
* ✅ **Database:** Online (Port 5432)
* ✅ **User Creation:** Functional (via Swagger UI)
* ⚠️ **Security:** Passwords are currently stored as plain text (CRITICAL TODO).

### 5. Next Steps
* Implement Password Hashing (Passlib + Bcrypt).
* Create Authentication Endpoints (Login/JWT).


## Day 2: Enterprise Security & File Ingestion
**Date:** Feb 03, 2026 
**Focus:** Authentication, Password Hashing, JWTs, and Big Data Ingestion

### 1. Implementation Progress
* **Security Layer:**
    * Implemented **Argon2id** password hashing (replacing Bcrypt).
    * Created `app/core/security.py` to handle crypto logic.
* **Authentication (AuthN):**
    * Implemented **JWT (JSON Web Token)** generation using `HS256`.
    * Built the `/token` endpoint complying with **OAuth2** standards.
    * Created the `get_current_user` dependency to protect routes (The "Bouncer").
* **File System:**
    * Designed the `Document` database model.
    * Implemented **Streaming File Upload** (`POST /upload/`) to handle large files efficiently without crashing RAM.

### 2. Challenges & Solutions
| Issue | Root Cause | Solution |
| :--- | :--- | :--- |
| **Environment Activation** | `source activate venv` failed because it is Conda syntax, not Python venv syntax. | **Fix:** Used the correct path command: `source backend/venv/bin/activate` and if in backend folder the command is: `source venv/bin/activate`. |
| **Bcrypt Crash** | `passlib` threw `AttributeError: module 'bcrypt' has no attribute '__about__'` due to a version conflict with Python 3.13. | **Fix:** Upgraded algorithm to **Argon2** (`pip install argon2-cffi`) which is more modern and compatible. |
| **OAuth2 Username Field** | FastAPI's `OAuth2PasswordRequestForm` requires a field named `username`, but our DB uses `email`. | **Concept:** Learned that OAuth2 spec mandates `username`, so we map the input `username` -> `email` in the backend logic. |
| **NameError: uuid** | Forgot to import the `uuid` library in `main.py` when implementing file upload. | **Fix:** Added `import uuid` to the top of the file. |
| **HTTP 401 on Upload** | Tried to upload a file without being logged in. | **Fix:** Used the "Authorize" button in Swagger UI to attach the JWT Bearer token to the request. |

### 3. Key Concepts Learned
* **State Validation:** Checking the database inside `get_current_user` ensures banned users are blocked immediately, even if their Token is still valid.
* **Streaming I/O:** Using `shutil.copyfileobj` instead of `file.read()` prevents Memory Errors when uploading large datasets.
* **One-Way Hashing:** Passwords are never stored raw; they are salted and hashed so they cannot be reversed.

### 4. Current System Status
* ✅ **Auth:** Fully functional (Register/Login/Protect).
* ✅ **Security:** Industry-standard (Argon2 + JWT).
* ✅ **Uploads:** Functional (Files saved to local `uploads/` folder).
* ⏳ **Next:** Processing these files (Text Extraction & AI Redaction).


## Day 3: Advanced File Parsing & Background Processing
**Date:** Feb 04, 2026
**Focus:** Background Tasks, PDF/Docx Parsing, and Debugging Data Ingestion

### 1. Implementation Progress
* **Asynchronous Processing:**
    * Integrated `FastAPI.BackgroundTasks` to decouple file uploads from file processing.
    * User gets an immediate `200 OK` while the server crunches data in the background.
* **Universal Parser Engine:**
    * Built `app/core/parser.py` to auto-detect file types.
    * **Strategy 1 (Word):** Used `python-docx` to extract text from `.docx` files.
    * **Strategy 2 (PDF):** Used `pdfplumber` for high-fidelity text extraction.
    * **Strategy 3 (Text):** Fallback for standard `.txt` files.
* **Database Updates:**
    * Added `text_content` column to the `Document` model.
    * Implemented logic to update the DB status (`processing` -> `completed`/`failed`) asynchronously.

### 2. Challenges & Solutions
| Issue | Root Cause | Solution |
| :--- | :--- | :--- |
| **Crash on Word Upload** | `pdfplumber` tried to open a `.docx` file and crashed with `No /Root object`. | **Fix:** Installed `python-docx`. Added an `if file.endswith('.docx')` check to route the file to the correct library. |
| **Silent Failure on PDFs** | Some PDFs (Project Proposal) returned `200 OK` but had empty text content in the DB. | **Debugging:** Added deep logs (`--- PARSER: ...`).<br>**Discovery:** The logs showed `Page 1 has NO text`. This confirmed the PDF was a **Scan (Image)**, not digital text. |
| **Session Closed Error** | Background task tried to use the API's database session after the request finished. | **Fix:** Passed the `session_factory` (not the session itself) to the background task, allowing it to open a fresh connection. |

### 3. Key Concepts Learned
* **Digital vs. Scanned PDFs:** Not all PDFs are equal. "Digital" PDFs (generated by Word) have selectable text. "Scanned" PDFs are just images. Standard parsers cannot read scans (requires OCR).
* **Logging is Vital:** Without the `print(f"--- PARSER: ...")` logs, we would have never known *why* the PDF failed.
* **Defensive Coding:** Using `try/except` blocks in the parser ensures the whole server doesn't crash just because one file is bad.

### 4. Current System Status
* ✅ **Word Support:** Working (Tested with `FederHub.docx`).
* ✅ **Digital PDF Support:** Working (Tested with `NYU_SR_TUNF.pdf`).
* ⚠️ **Scanned PDF Support:** Identified limitation (requires OCR, out of scope for now).
* ⏳ **Next:** **The Redaction Engine**. Now that we have the text, we need to find PII (Names, Emails) and mask them.


## Day 4: The Intelligence Layer (Redaction & RAG)
**Date:** Feb 05, 2026
**Focus:** NLP, PII Redaction, Vector Embeddings, and Semantic Search

### 1. Implementation Progress
* **PII Redaction Engine:**
    * Implemented `app/core/redactor.py` using Regex.
    * Automatically detects and replaces Emails (`<EMAIL>`), Phone Numbers (`<PHONE>`), and Custom Student IDs (`<STUDENT_ID>`).
    * **Result:** Data is scrubbed *before* it is stored permanently in the database.
* **Vector Embedding Engine:**
    * Integrated `sentence-transformers` (`all-MiniLM-L6-v2`) to convert text into 384-dimensional vectors.
    * Updated the Database Schema to store vectors as JSON arrays.
* **Semantic Search (RAG Lite):**
    * Built the `/search/` endpoint.
    * Implemented **Cosine Similarity** logic (`numpy.dot`) to rank documents by meaning, not just keywords.
    * **Outcome:** Users can ask natural language questions ("What are my grades?") and retrieve relevant documents (Transcript) even without exact keyword matches.

### 2. Challenges & Solutions
| Issue | Root Cause | Solution |
| :--- | :--- | :--- |
| **HuggingFace Warnings** | The model loader warned about `position_ids`. | **Analysis:** Verified this is a known, harmless warning when loading specific BERT architectures for embeddings. Ignored it safely. |
| **Database Schema** | Needed to store arrays of floats (Vectors) without a dedicated VectorDB. | **Fix:** Used Postgres `JSON` column type to store the list of numbers as a temporary solution before migrating to `pgvector`. |
| **Search Accuracy** | Need to ensure "GPA" matches "Transcript". | **Fix:** Validated that `all-MiniLM-L6-v2` captures the semantic relationship between "Grades/GPA" and academic transcripts. |

### 3. Key Concepts Learned
* **Embeddings:** Text is just high-dimensional math. "GPA" and "Grades" are close points in vector space.
* **DLP (Data Loss Prevention):** Security isn't just permissions; it's also sanitizing content (Redaction) to prevent accidental leaks.
* **Cosine Similarity:** The mathematical foundation of all modern AI search engines.

### 4. Current System Status
* ✅ **Ingestion:** Uploads PDF/Docx -> Extracts Text.
* ✅ **Security:** Redacts PII automatically.
* ✅ **Intelligence:** Vectorizes text and supports Semantic Search.
* 🚀 **Ready For:** Frontend Integration.


## Day 5: The Frontend Interface
**Date:** Feb 06, 2026
**Focus:** Next.js, React, CORS, and Full-Stack Integration

### 1. Implementation Progress
* **Frontend Initialization:**
    * Created a `Next.js 16` app using TypeScript and App Router.
    * Configured **Tailwind CSS** for rapid UI development.
* **API Integration:**
    * Configured **CORS** in FastAPI to allow `localhost:3000` to talk to `localhost:8000`.
    * Built a **Login Page** that exchanges credentials for a JWT and stores it in `localStorage`.
    * Built a **Secure Dashboard** that checks for the token and redirects unauthorized users.
* **Features:**
    * **Document List:** Fetches and displays user files from Postgres.
    * **File Uploader:** Sends files to the backend and auto-refreshes the list.
    * **Chat Interface:** Connects to the `/search/` endpoint to display Semantic Search results with confidence scores.

### 2. Challenges & Solutions
| Issue | Root Cause | Solution |
| :--- | :--- | :--- |
| **Backend Offline Error** | Browser blocked the request due to CORS policy. | **Fix:** Added `CORSMiddleware` to `main.py` explicitly allowing `localhost:3000`. |
| **Login 404** | Next.js Router couldn't find the page. | **Fix:** Moved `page.tsx` into a dedicated `app/login/` folder to match the URL structure. |
| **Empty Search Results** | Similarity threshold (0.25) was too strict for small test queries. | **Fix:** Lowered threshold to `0.01` to ensure results appear during testing. |

### 3. Key Concepts Learned
* **Full Stack Auth Flow:** Frontend stores Token -> Sends Token in Header (`Authorization: Bearer ...`) -> Backend Validates -> Data Returned.
* **State Management:** Using `useState` and `useEffect` to handle loading states (e.g., "Uploading...", "Searching...").
* **Routing:** How Next.js maps file folders to URLs.

### 4. Current System Status
* ✅ **Full Stack:** Complete.
* ✅ **End-to-End Flow:** User can Login -> Upload -> Wait for AI -> Search -> Get Answers.
* 🚀 **Project Status:** MVP (Minimum Viable Product) Complete.


## Day 6: Containerization & OCR (The "Pro" Upgrade)
**Date:** Feb 07, 2026
**Focus:** Docker, System Architecture, and Optical Character Recognition (OCR)

### 1. Implementation Progress
* **Docker Architecture:**
    * Dockerized **Backend** (Python 3.13 Slim).
    * Dockerized **Frontend** (Node 20 Alpine).
    * Orchestrated entire stack (DB + Backend + Frontend) using `docker-compose`.
    * **Result:** System launches with a single command (`docker-compose up`), creating a reproducible production-like environment.
* **OCR Integration (The "Eyes"):**
    * Installed `tesseract-ocr` and `poppler-utils` inside the Docker container.
    * Upgraded `parser.py` to handle edge cases:
        * **Strategy 1:** Read Text/Word files directly.
        * **Strategy 2:** Read Digital PDFs using `pdfplumber`.
        * **Strategy 3:** Fallback to **OCR** (`pytesseract`) if `pdfplumber` detects empty pages (Scanned PDFs).

### 2. Challenges & Solutions
| Issue | Root Cause | Solution |
| :--- | :--- | :--- |
| **Frontend Build Fail** | Next.js 16 requires Node 20+, but Dockerfile used Node 18. | **Fix:** Upgraded Dockerfile to `FROM node:20-alpine`. |
| **DB Password Error** | Docker volume persisted old DB credentials (`user/password`) mismatching new config. | **Fix:** Ran `docker-compose down -v` to wipe the volume and reset the database. |
| **Scanned PDFs** | `pdfplumber` returned empty strings for image-based PDFs. | **Fix:** Added `pdf2image` + `pytesseract` pipeline to convert pages to images and read text visually. |

### 3. Key Concepts Learned
* **Docker Compose:** Managing multi-container networking (e.g., Backend talking to `db` instead of `localhost`).
* **OCR Pipelines:** Text extraction is a hierarchy (Try cheap/fast methods first, fall back to expensive/slow OCR only when needed).
* **Environment Isolation:** Why `venv` doesn't matter inside Docker.

### 4. Project Status: MVP COMPLETE 🚀
The system is now a fully functional, containerized, AI-powered document analysis platform.


## Day 7: The Chatbot (Project Complete)
**Date:** Feb 10, 2026
**Focus:** RAG (Retrieval Augmented Generation) and Generative AI

### 1. Implementation Progress
* **Groq Integration:**
    * Connected `llama-3.3-70b` to the backend using the Groq API.
    * Built a `ChatEngine` class to handle prompt construction and API calls.
* **RAG Pipeline:**
    * **Retrieve:** Used Vector Search (Cosine Similarity) to find relevant document chunks.
    * **Augment:** Injected those chunks into a System Prompt ("Answer using ONLY this context").
    * **Generate:** Returned the AI's natural language response to the user.
* **Frontend Upgrade:**
    * Switched the "Search" bar to call `/chat/`.
    * Added a UI component to display the AI's answer alongside the source documents.

### 2. Challenges & Solutions
* **Model Deprecation:** The initial model (`llama3-8b`) was retired by Groq. **Fix:** Upgraded to `llama-3.3-70b-versatile`.
* **Strict Thresholds:** The similarity score (0.25) was too high for short queries like "GPA". **Fix:** Lowered to `0.01` to ensure context was passed to the LLM.
* **Docker Staleness:** Code changes weren't appearing because Docker was running old images. **Fix:** Used `docker-compose up --build` to force updates.

### 3. Final Status
* ✅ **Auth:** Secure.
* ✅ **Data:** OCR & Vectorized.
* ✅ **AI:** Generative & Context-Aware.
* ✅ **Deployment:** Dockerized.


## Day 8: Advanced AI Features (Memory, Streaming, Voice)
**Date:** Feb 11, 2026
**Focus:** Chat History, Real-Time Streaming, and Audio Transcription (Whisper)

### 1. Implementation Progress
* **Chat Memory (Context Awareness):**
    * Updated Backend `ChatRequest` model to accept a list of previous messages (`history`).
    * Updated Frontend to maintain `messages` state and send full conversation history to the API.
    * **Result:** The AI now understands follow-up questions like "Is *that* good?" (referring to previous answers).
* **Streaming Response (Typewriter Effect):**
    * Refactored `ChatEngine` to use a Python Generator (`yield`).
    * Updated FastAPI to return a `StreamingResponse` (Server-Sent Events).
    * Updated Frontend to use `TextDecoder` to read chunks of text in real-time.
    * **Result:** The answer types out instantly letter-by-letter instead of waiting 3-5 seconds.
* **Voice Mode (The Ear):**
    * Integrated Groq's **Whisper** model for Speech-to-Text.
    * Added a `MediaRecorder` hook in React to capture microphone input.
    * Added a Microphone button that records audio, sends it to the backend, and auto-fills the input box.
* **UI Polish:**
    * Darkened the input text color for better readability.

### 2. Challenges & Solutions
| Issue | Root Cause | Solution |
| :--- | :--- | :--- |
| **Model Deprecation 1** | Groq retired `llama3-8b`. | **Fix:** Upgraded to `llama-3.3-70b-versatile`. |
| **Strict Logic Failure** | AI refused to answer subjective questions ("Is my GPA good?") because the PDF didn't explicitly say "It is good." | **Fix:** Updated System Prompt to allow "General Knowledge" for opinions/explanations. |
| **Model Deprecation 2** | Groq retired `distil-whisper`. | **Fix:** Upgraded to `whisper-large-v3`. |
| **Language Confusion** | Whisper heard "mere" (Hindi/Urdu for "my") and switched the entire conversation to Urdu script. | **Fix:** Forced `language="en"` in the Whisper API call to ensure English transcription. |

### 3. Key Concepts Learned
* **Stateful vs Stateless AI:** Passing `history` allows the LLM to maintain context across turns.
* **Streaming Generators:** Using Python `yield` to push data to the client immediately improves perceived performance.
* **Audio Blobs:** Handling binary audio data in the browser and sending it via `FormData`.

### 4. Project Status: ADVANCED BETA 🚀
The system is now a conversational voice assistant, not just a document search engine.

## Day 9: The Pivot (Refocusing on Big Data & ML)
**Date:** Feb 12, 2026
**Status:** Strategic Course Correction

### 1. The Realization
We successfully built a functional RAG Chatbot with Voice and Streaming. However, we drifted from the core "Resume-Defining" goals:
* **Missing:** True Big Data scale (we are using <10 docs).
* **Missing:** Deep Learning / Fine-Tuning (we are just calling APIs).
* **Missing:** Kubernetes / Orchestration (we are stuck on Docker Compose).
* **Hidden:** The core "GuardRail" (Redaction) logic is invisible to the user.

### 2. The New "Enterprise" Roadmap
To realign with the original vision of a **Scalable AI Security Platform**, we are pivoting to the following plan:

#### **Phase 1: Big Data & Synthetic Scale (Immediate Next Step)**
* **Action:** Build a `synthetic_data.py` engine to generate 1,000+ fake documents containing realistic PII (SSNs, Credit Cards, Medical Info).
* **Goal:** Stress-test the Vector Database and Embedding Engine. Proof of "Big Data" handling.

#### **Phase 2: Fine-Tuning & Deep Learning**
* **Action:** Instead of relying solely on pre-trained models, we will fine-tune a lightweight BERT/DistilBERT model specifically for **Context-Aware PII Detection** on our synthetic dataset.
* **Goal:** Demonstrate actual NLP model training and evaluation, not just API wrapper work.

#### **Phase 3: The "Glass Box" UI**
* **Action:** Build a "Transparency Mode" in the Dashboard.
* **Goal:** Show the user exactly what the LLM sees vs. what was redacted. Visualize the Vector Search Similarity scores.

#### **Phase 4: Kubernetes & Cloud Auth**
* **Action:** Migrate from Docker Compose to **Kubernetes (Minikube/EKS)**.
* **Action:** Replace custom JWT Auth with **AWS Cognito / Azure AD** simulation to mimic enterprise security standards.

### 3. Immediate Action Plan (Tomorrow)
1.  **Scripting:** Write the Synthetic Data Generator.
2.  **Ingestion:** Pipeline 1,000+ docs into Postgres Vector to test latency.
3.  **Visualization:** Verify the embeddings are actually distributing correctly in vector space.

**Current State:** Resetting focus from "Features" (Chat/Voice) to "Engineering Depth" (Scale/ML/Ops).

## Day 10: The Glass Box & Synthetic Data
**Date:** Feb 13, 2026
**Focus:** Synthetic Data Generation, Sorting Logic, and Transparency UI

### 1. The Pivot
* Shifted focus from "Consumer Features" (Voice/Chat) to "Enterprise Engineering" (Security/Observability).
* Recognized that a "Black Box" security tool is useless if the admin cannot verify it works.

### 2. Implementation Progress
* **Synthetic Data Pipeline:**
    * Built a Python script using `Faker` to generate 50+ realistic documents (Invoices, Medical Records, Resumes).
    * Injected high-risk PII (SSNs, Credit Cards) to stress-test the system.
* **Vector Search Upgrade:**
    * **Bug Fix:** The system was retrieving documents but ignoring the most relevant ones due to lack of sorting.
    * **Fix:** Implemented `sorted(docs, key=lambda x: x['score'], reverse=True)` to ensure the AI always sees the best matches first.
* **The "Glass Box" UI (Developer Mode):**
    * **Backend:** Updated `/chat/` to stream NDJSON (New-Line Delimited JSON), sending `debug_metadata` before the first token of text.
    * **Frontend:** Built a "Hacker Console" that visualizes:
        * Real-time Vector Similarity Scores (Bar Charts).
        * The exact "Redacted Context" being fed to the LLM.

### 3. Key Results
* **Leak Prevention:** Uploaded a synthetic medical record with an SSN.
* **Verification:** The "Glass Box" proved the backend replaced the SSN with `<SSN>` before the AI ever saw it.
* **Resume Value:** Demonstrated **Explainable AI (XAI)** and **Data Privacy pipelines**.

### 4. Status
* ✅ Core RAG Pipeline
* ✅ Voice & Streaming
* ✅ Visible Security Layer (The "GuardRail")
* 🔜 Next: Deep Learning (replacing Regex with BERT) & Kubernetes.
docker cp guardrail-ai-backend-1:/app/synthetic_docs ./backend/synthetic_docs


## Day 11: Deep Learning & Risk Intelligence
**Date:** Feb 14, 2026
**Focus:** Named Entity Recognition (BERT), Risk Scoring, and Automated Auditing

### 1. The Upgrade: From Regex to Brains 🧠
* **Problem:** Regex was too rigid. It missed context-based PII (like Names and Organizations).
* **Solution:** Integrated **Hugging Face Transformers (`bert-base-NER`)**.
* **Implementation:**
    * Created `NERRedactor` class.
    * Downloads and runs a BERT model inside the Docker container.
    * Performs hybrid redaction: Deep Learning for Context (Names/Locs) + Regex for Patterns (SSN/CC).

### 2. Feature: Risk Scoring 📊
* **Goal:** Differentiate between "Safe" documents and "Dangerous" leaks.
* **Algorithm:**
    * **Critical (100 pts):** SSN, Credit Cards.
    * **Sensitive (10 pts):** Emails, Phone Numbers.
    * **Context (1 pt):** Names, Organizations, Locations.
* **Result:**
    * Medical Records with SSNs hit scores of **100+** (🔴 High Risk).
    * Resumes with just names hit scores of **~10-20** (🟢 Safe).

### 3. Verification
* Validated using Synthetic Data generated via `Faker`.
* Confirmed that the "Glass Box" UI correctly flags high-risk files and redacts the sensitive data in real-time.

### 4. Project Status
* **Core:** Complete.
* **Security:** Enterprise-Grade (DLP + Redaction).
* **Next:** Deployment & Orchestration (Kubernetes).

## Day 12: Orchestration with Kubernetes (K8s)
**Date:** Feb 15, 2026
**Focus:** Infrastructure, Container Orchestration, and Scalability

### 1. The Shift to Cloud-Native
* Moved from `docker-compose` (local dev) to **Kubernetes** (production standard).
* Used **Colima** to run a lightweight K8s cluster on macOS (M2 Air).

### 2. Implementation Steps
* **Building Images:** K8s needs pre-built images. We built them locally to avoid uploading to Docker Hub:
    * `docker build -t guardrail-backend:latest ./backend`
    * `docker build -t guardrail-frontend:latest ./frontend`
* **Resource Allocation:**
    * **Issue:** The AI Models (BERT + SentenceTransformers) consume ~1.5GB RAM.
    * **Crash:** The default VM (2GB RAM) caused an `OOMKilled` (Out of Memory) error.
    * **Fix:** Upgraded Colima VM: `colima start --cpu 4 --memory 6 --kubernetes`.
* **Manifests (Infrastructure as Code):**
    * `postgres.yaml`: Deployed DB with a **PersistentVolumeClaim** so data survives restarts.
    * `backend.yaml`: Deployed the API with `imagePullPolicy: Never` (to use local images) and `postgresql+asyncpg://` (async driver fix).
    * `frontend.yaml`: Deployed Next.js and connected it to the backend Service.

### 3. Key Issues Solved
* **Async Driver Error:** The backend code uses `async/await`, but the connection string defaulted to a sync driver (`psycopg2`).
    * *Fix:* Changed URL to `postgresql+asyncpg://user:password@db:5432/guardrail`.
* **Memory Limits:** The cluster kept killing the backend pod.
    * *Fix:* Identified `OOMKilled` status and scaled the VM memory to 6GB.

### 4. Verification
* Used `kubectl port-forward` to tunnel the isolated cluster to localhost.
* **Success:** Full end-to-end flow (Login -> Upload -> Redaction -> Chat) verified running inside the cluster.

### 5. Commands Reference
* Start Cluster: `colima start --cpu 4 --memory 6 --kubernetes`
* Build Backend: `docker build -t guardrail-backend:latest ./backend`
* Deploy: `kubectl apply -f k8s/`
* Debug Logs: `kubectl logs <pod-name>`
* Access App: `kubectl port-forward service/frontend 3000:3000`

## Day 13: Helm & Package Management
**Date:** Feb 16, 2026
**Focus:** Kubernetes Packaging, Helm Charts, and Infrastructure as Code (IaC)

### 1. The Upgrade: From Manifests to Charts 📦
* **Problem:** Managing raw YAML files (`backend.yaml`, `frontend.yaml`) is error-prone and hard to scale. Hardcoded values make environment switching impossible.
* **Solution:** Migrated to **Helm** (The Kubernetes Package Manager).
    * Created a `guardrail` chart.
    * Templated all resources (Deployments, Services, PVCs).
    * Centralized configuration in `values.yaml` (Database creds, API Keys, Image tags).

### 2. Implementation Steps
* **Templating:** Rewrote hardcoded values (e.g., `image: guardrail-backend:latest`) into dynamic variables (`image: {{ .Values.backend.image }}`).
* **Configuration:** Injected `GROQ_API_KEY` and `DATABASE_URL` dynamically via `values.yaml`, ensuring sensitive keys aren't hardcoded in templates.
* **Deployment:** Executed `helm install my-guardrail ./guardrail` to deploy the full stack.

### 3. Challenges & Fixes 🛠️
* **Issue 1: Resource Ownership Conflict**
    * **Error:** `Error: INSTALLATION FAILED... PersistentVolumeClaim "postgres-pvc" ... exists and cannot be imported`.
    * **Cause:** Helm refused to overwrite resources that were previously created manually via `kubectl apply`. Helm strictly manages "ownership" to prevent accidental data loss.
    * **Fix:** We manually cleaned the cluster state before installing the chart:
        ```bash
        kubectl delete deployment backend frontend postgres
        kubectl delete service backend frontend db
        kubectl delete pvc postgres-pvc
        ```
* **Issue 2: Service Discovery Naming**
    * **Context:** The Backend needs to find the Database.
    * **Fix:** In `values.yaml`, we explicitly set the `databaseUrl` host to `postgres-service` to match the Service name defined in the Helm template, ensuring internal DNS resolution worked correctly.

### 4. Key Learnings
* **Helm vs. Kubectl:** `kubectl` is for manual, imperative commands. `helm` is for declarative, versioned releases.
* **State Management:** You cannot mix-and-match manual deployments with Helm releases without conflicts. A "Clean Slate" is required for the initial Helm install.

### 5. Next Steps
* **Cloud Deployment:** The app is ready for AWS EKS or Render.
* **Cloud Auth:** Replace local JWT with enterprise-grade Auth (Cognito/Auth0).


## Day 14: Cloud Readiness & Dynamic Configuration
**Date:** Feb 17, 2026
**Focus:** Refactoring for Production, Dynamic Environments, and Database Migrations

### 1. The Goal: "It Works Anywhere" 🌍
* **Problem:** The app was hardcoded to `localhost`. Deploying it to the cloud would break the frontend (which wouldn't find the backend) and the database (which enforced password requirements incompatible with OAuth).
* **Solution:** Refactored the entire stack to use **Environment Variables** and **Flexible Schemas**.

### 2. Implementation Steps 🛠️
* **Backend Refactor:**
    * **CORS:** Replaced hardcoded origins with `os.getenv("ALLOWED_ORIGINS")`.
    * **Database Model:** Updated `User` model to make `password_hash` optional (preparing for Google Login).
    * **Dependencies:** Added `python-jose` and `httpx` for future OAuth implementation.
* **Frontend Refactor:**
    * **API Client:** Created `utils/api.ts` using **Axios**.
    * **Dynamic URL:** Configured it to use `process.env.NEXT_PUBLIC_API_URL` with a fallback to localhost.
    * **Interceptor:** Automated token injection (`Authorization: Bearer ...`) for every request.
* **Infrastructure:**
    * Rebuilt Docker images to include new dependencies.
    * Redeployed via Helm to apply changes to the cluster.

### 3. Challenges & Fixes 🔧
* **Issue 1: TypeScript Import Errors**
    * **Error:** `Module '.../api' has no exported member 'api'`.
    * **Cause:** Mismatch between `export default` and named exports.
    * **Fix:** Standardized on named exports (`export const api = ...`) and updated imports in `page.tsx`.
* **Issue 2: Database Schema Mismatch**
    * **Error:** `500 Internal Server Error` when creating users.
    * **Cause:** The Python code expected a new column (`auth_provider`), but the existing Postgres database was using the old schema.
    * **Fix:** Performed a "Hard Reset" in Kubernetes:
        ```bash
        helm uninstall my-guardrail
        kubectl delete pvc postgres-pvc  # Wiped the old database
        helm install my-guardrail ./helm/guardrail
        ```
* **Issue 3: Duplicate User Entry**
    * **Error:** `IntegrityError: duplicate key value violates unique constraint`.
    * **Cause:** The "500 Error" in the previous step actually *succeeded* in creating the user before crashing on the response.
    * **Fix:** Validated that the user existed and simply logged in.

### 4. Current State
* **Architecture:** Fully Containerized & Orchestrated (K8s).
* **Network:** Dynamic Service Discovery via K8s DNS.
* **Security:** Ready for external traffic (CORS configured).


## Day 15: Identity Engineering (OAuth 2.0 & OIDC)
**Date:** Feb 18, 2026
**Focus:** Authentication, Security, Google OAuth, and Distributed Systems Debugging

### 1. The Upgrade: From "Secret123" to "Sign in with Google" 🔐
* **Goal:** Remove the reliance on local passwords and implement a secure, user-friendly OAuth flow.
* **Architecture:**
    * **Frontend:** Uses `@react-oauth/google` to get an ID Token from Google.
    * **Backend:** Verifies the token integrity with Google's servers, checks the Audience (Aud), and creates a session.
    * **Database:** Automatically registers new users with `auth_provider="google"`.

### 2. Implementation Steps 🛠️
* **Google Cloud Console:**
    * Created a project "GuardRail-AI".
    * Configured OAuth Consent Screen (External).
    * Generated Client ID and authorized `localhost:3000`.
* **Frontend:**
    * Created `GoogleProvider.tsx` wrapper to handle the OAuth Context.
    * Added the Google Login Button to `login/page.tsx`.
* **Backend:**
    * Created `app/auth.py` to centralize security logic (JWT generation + Google Token verification).
    * Added `POST /auth/google` endpoint to exchange Google Tokens for App Session Tokens.
* **Infrastructure:**
    * Updated Helm `values.yaml` to inject `GOOGLE_CLIENT_ID` into the backend container.

### 3. Critical Issues & Fixes 🔧
* **Issue 1: The "Ghost" Schema (Database Mismatch)**
    * **Error:** `ProgrammingError: column "auth_provider" does not exist`.
    * **Context:** Even though we updated the code, the Postgres Persistent Volume (PVC) retained the old table structure.
    * **Fix:** Performed a "Hard Reset" of the database storage:
        ```bash
        helm uninstall my-guardrail
        kubectl delete pvc postgres-pvc  # <--- The Critical Step
        helm install my-guardrail ./helm/guardrail
        ```
* **Issue 2: The "Split Brain" Security (401 Unauthorized)**
    * **Error:** Google Login succeeded (200 OK), but fetching documents failed (401).
    * **Context:** `auth.py` was signing tokens with a hardcoded key, but the document route was validating them with a different key from `config.py`.
    * **Fix:** Refactored `auth.py` to import `SECRET_KEY` from `app.core.config`, ensuring both systems used the exact same key.

### 4. Key Commands Used
* **Rebuild Backend:** `docker build -t guardrail-backend:latest ./backend`
* **Update Configuration:** `helm upgrade --install my-guardrail ./helm/guardrail`
* **Restart Pods:** `kubectl rollout restart deployment backend`
* **Deep Debugging:** `kubectl logs backend-<id>` to trace the SQL errors.

### 5. Outcome
* **Status:** Fully Functional.
* **Capability:** Users can log in via Email OR Google. Session tokens are standardized across both methods.