# AI Voice Interviewer 🎙️🤖

An enterprise-ready, standalone AI-powered voice interview platform for conducting realistic mock and technical interviews using real-time conversational voice.

The platform extracts a candidate's resume via PyMuPDF, analyzes their experience with OpenAI, generates 10–15 personalized interview questions based strictly on their actual projects and skills, conducts a live two-way voice interview using the **OpenAI Realtime WebRTC API**, adaptively asks relevant follow-up questions, evaluates answers across 5 technical competencies, and generates an executive report stored in PostgreSQL.

---

## Architecture Overview

```text
                    Candidate (Browser)
                            │
                            ▼
                     Next.js Frontend
                    (Tailwind / WebRTC)
                            │
               ┌────────────┴────────────┐
               │ HTTPS                   │ WebRTC Audio
               ▼                         ▼
        FastAPI Backend           OpenAI Realtime
      (Python 3.11 / Pydantic)   (Voice Interview)
               │
       ┌───────┴───────┐
       ▼               ▼
  PostgreSQL      OpenAI API
  (Database)    (Resume / Evaluation / Report)
```

---

## Table of Contents

1. [Key Features](#1-key-features)
2. [Prerequisites](#2-prerequisites)
3. [Tools Installation Guide](#3-tools-installation-guide)
4. [OpenAI API Key Setup](#4-openai-api-key-setup)
5. [Project Structure](#5-project-structure)
6. [Local Development Setup](#6-local-development-setup)
   - [Step 1: Start PostgreSQL with Docker](#step-1-start-postgresql-with-docker)
   - [Step 2: Configure Backend Environment](#step-2-configure-backend-environment)
   - [Step 3: Setup Python Virtual Environment](#step-3-setup-python-virtual-environment)
   - [Step 4: Install Dependencies & Run Database Migrations](#step-4-install-dependencies--run-database-migrations)
   - [Step 5: Start FastAPI Backend](#step-5-start-fastapi-backend)
   - [Step 6: Configure Frontend Environment](#step-6-configure-frontend-environment)
   - [Step 7: Install Node Modules & Start Next.js](#step-7-install-node-modules--start-nextjs)
7. [Running End-to-End Tests](#7-running-end-to-end-tests)
8. [End-to-End Interview Walkthrough](#8-end-to-end-interview-walkthrough)
9. [Recruiter / Admin Dashboard](#9-recruiter--admin-dashboard)
10. [Security & Privacy Standards](#10-security--privacy-standards)
11. [Deployment Guide (Vercel & Railway)](#11-deployment-guide-vercel--railway)
12. [Common Errors & Troubleshooting](#12-common-errors--troubleshooting)
13. [Future Automation (n8n Roadmap)](#13-future-automation-n8n-roadmap)

---

## 1. Key Features

- **Digital Resume Extraction**: Uses PyMuPDF (`fitz`) to extract text and validate PDFs (rejects empty scans, executables, or files > 10MB).
- **Personalized Question Generation**: Generates 10–15 questions across Introduction, Resume, Technical Skills, Projects, Experience, Problem Solving, and Behavioral categories tailored to the candidate's actual projects.
- **Two-Way Voice Interview**: Spoken instructions and questions via OpenAI Realtime WebRTC with server-side voice activity detection (VAD).
- **Adaptive Follow-Up Logic**: Dynamically asks relevant follow-up questions if a candidate provides a surface-level response, bounded by strict rules (maximum 1 follow-up per question).
- **Objective Multi-Pillar Scoring**: Evaluates answers across 5 pillars (Technical Knowledge, Project Understanding, Problem Solving, Communication Clarity, Resume Understanding) with zero demographic bias.
- **Executive Report Generation**: Complete question-by-question breakdown, strengths, missing points, and "Human Review Recommended" decision flag stored in PostgreSQL.
- **Zero Browser Secret Exposure**: The permanent `OPENAI_API_KEY` never reaches the browser; the backend mints short-lived ephemeral session credentials.

---

## 2. Prerequisites

Ensure you have installed:
- **Git**: For version control
- **Node.js**: v18.17+ or v20+
- **Python**: 3.10+ or 3.11+
- **Docker Desktop**: For running local PostgreSQL (or local PostgreSQL server)
- **OpenAI API Key**: Account with access to Chat Completions and Realtime API

---

## 3. Tools Installation Guide

### Installing Git
- **Windows**: Download from [git-scm.com](https://git-scm.com/) and run the installer. Verify:
  ```powershell
  git --version
  ```
- **macOS**: Run in Terminal: `xcode-select --install` or `brew install git`.
- **Linux (Ubuntu/Debian)**:
  ```bash
  sudo apt update && sudo apt install git -y
  ```

### Installing Node.js & npm
- Download the **LTS version (v20+)** from [nodejs.org](https://nodejs.org/).
- Verify:
  ```bash
  node --version
  npm --version
  ```

### Installing Python
- Download Python 3.11 from [python.org](https://www.python.org/).
- On Windows, make sure to check the box: **"Add Python to PATH"**.
- Verify:
  ```bash
  python --version
  ```

### Installing Docker Desktop
- Download from [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/).
- Launch Docker Desktop and ensure the engine is running.
- Verify:
  ```bash
  docker --version
  ```

---

## 4. OpenAI API Key Setup

1. Sign up or log in at [platform.openai.com](https://platform.openai.com/).
2. Navigate to **API Keys** -> **Create new secret key**.
3. Copy your key (`sk-proj-...`).
4. **Important**: Keep this key secret. You will place it only in `backend/.env`.

---

## 5. Project Structure

```text
ai-voice-interviewer/
├── backend/
│   ├── app/
│   │   ├── api/                 # REST endpoints (resumes, interviews, realtime, admin)
│   │   ├── core/                # Configuration (BaseSettings, CORS)
│   │   ├── db/                  # SQLAlchemy engine, session, Base
│   │   ├── models/              # Candidate, Interview, Question, Answer ORM
│   │   ├── schemas/             # Pydantic validation schemas
│   │   ├── services/            # PyMuPDF, OpenAI, Evaluator, Report Generator
│   │   ├── prompts/             # System and user prompt templates
│   │   └── main.py              # FastAPI application entrypoint
│   ├── migrations/              # Alembic database migrations
│   ├── tests/                   # Pytest test suite
│   ├── alembic.ini              # Alembic config
│   ├── requirements.txt         # Python dependencies
│   └── .env.example             # Backend environment template
├── frontend/
│   ├── app/
│   │   ├── page.tsx             # Professional landing page
│   │   ├── upload/page.tsx      # Step 2: Upload & Step 4: Profile confirmation
│   │   ├── interview/[id]/      # Step 6 & 7: Live voice interview room
│   │   ├── report/[id]/         # Step 8: Final AI interview assessment report
│   │   ├── admin/page.tsx       # Recruiter candidate dashboard
│   │   ├── layout.tsx           # Global layout & metadata
│   │   └── globals.css          # Tailwind CSS styling
│   ├── components/              # Navbar, Footer, VoiceVisualizer, ScoreGauge
│   ├── lib/                     # api.ts (HTTP client), realtime.ts (WebRTC)
│   ├── types/                   # TypeScript interfaces
│   ├── package.json             # Next.js dependencies
│   └── .env.example             # Frontend environment template
├── sample_resumes/              # Sample resumes for testing
│   └── alex_morgan_resume.pdf
├── docker-compose.yml           # PostgreSQL Docker service
├── BUILD_NOTES.md               # Technical architecture & design decisions
└── README.md                    # Comprehensive beginner-friendly guide
```

---

## 6. Local Development Setup

### Step 1: Start PostgreSQL with Docker

Open a terminal in the root directory:

```bash
docker compose up -d postgres
```
- **What it does**: Starts a containerized PostgreSQL 16 database running on port `5432`.
- **Expected Output**:
  ```text
  [+] Running 2/2
   ✔ Network ai-voice-interviewer_default  Created
   ✔ Container ai_interviewer_postgres    Started
  ```

> **Note**: If you don't have Docker running, the application includes an automatic fallback to local SQLite (`interviewer.db`) so you can run and test immediately without Docker!

---

### Step 2: Configure Backend Environment

Copy `.env.example` to `.env` in the `backend/` folder:

```bash
# On Windows PowerShell
copy backend\.env.example backend\.env

# On macOS / Linux
cp backend/.env.example backend/.env
```

Open `backend/.env` in your text editor and add your OpenAI API key:

```env
APP_ENV=development
DATABASE_URL=postgresql+psycopg://interviewer:interviewer_password@localhost:5432/ai_interviewer
OPENAI_API_KEY=sk-proj-your-actual-key-here
FRONTEND_URL=http://localhost:3000
MAX_RESUME_SIZE_MB=10
OPENAI_TEXT_MODEL=gpt-4o-mini
OPENAI_REALTIME_MODEL=gpt-4o-realtime-preview-2024-12-17
OPENAI_VOICE=alloy
```

---

### Step 3: Setup Python Virtual Environment

Navigate into `backend/`:

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment:
- **Windows PowerShell**:
  ```powershell
  .\.venv\Scripts\Activate.ps1
  ```
  *(If you see an execution policy error, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)*
- **Windows Command Prompt (cmd)**:
  ```cmd
  .venv\Scripts\activate.bat
  ```
- **macOS / Linux**:
  ```bash
  source .venv/bin/activate
  ```

---

### Step 4: Install Dependencies & Run Database Migrations

With `.venv` activated:

```bash
pip install -r requirements.txt
alembic upgrade head
```

- **What it does**: Installs FastAPI, SQLAlchemy, PyMuPDF, OpenAI SDK, and applies the initial schema migration creating the `candidates`, `interviews`, `questions`, and `answers` tables.
- **Expected Output**:
  ```text
  INFO  [alembic.runtime.migration] Running upgrade  -> 001_initial_schema, initial_schema
  ```

---

### Step 5: Start FastAPI Backend

From the `backend/` directory:

```bash
uvicorn app.main:app --reload --port 8000
```

- **Where to execute**: Inside `backend/` with `.venv` active.
- **Expected Output**:
  ```text
  INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
  INFO:     Started reloader process
  INFO:     Application startup complete.
  ```
- You can check health in your browser: [http://localhost:8000/health](http://localhost:8000/health)
- Interactive API Docs (Swagger): [http://localhost:8000/docs](http://localhost:8000/docs)

---

### Step 6: Configure Frontend Environment

Open a **new second terminal** and navigate to `frontend/`:

```bash
# On Windows PowerShell
copy frontend\.env.example frontend\.env.local

# On macOS / Linux
cp frontend/.env.example frontend/.env.local
```

Ensure `frontend/.env.local` contains:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```
> **Security Reminder**: Never place your `OPENAI_API_KEY` here.

---

### Step 7: Install Node Modules & Start Next.js

From the `frontend/` directory:

```bash
npm install
npm run dev
```

- **Where to execute**: Inside `frontend/`.
- **Expected Output**:
  ```text
  ▲ Next.js 14.2.15
  - Local:        http://localhost:3000
  - Environments: .env.local
  ✓ Ready in 1500ms
  ```

Open your browser and visit: **[http://localhost:3000](http://localhost:3000)**!

---

## 7. Running End-to-End Tests

To verify backend services, PDF parsing, DB relationships, and API endpoints, run pytest:

```bash
# From root directory
.\backend\.venv\Scripts\pytest .\backend\tests -v
```

Expected result:
```text
backend/tests/test_api.py::test_health_endpoint PASSED                   [ 12%]
backend/tests/test_api.py::test_invalid_resume_upload_filetype PASSED    [ 25%]
backend/tests/test_api.py::test_interview_lifecycle PASSED               [ 37%]
backend/tests/test_models.py::test_candidate_and_interview_creation PASSED [ 50%]
backend/tests/test_models.py::test_question_and_answer_relationship PASSED [ 62%]
backend/tests/test_pdf_parser.py::test_extract_text_from_valid_pdf PASSED [ 75%]
backend/tests/test_pdf_parser.py::test_extract_text_empty_bytes PASSED   [ 87%]
backend/tests/test_pdf_parser.py::test_extract_text_insufficient_content PASSED [100%]

============================== 8 passed in 8.62s ==============================
```

---

## 8. End-to-End Interview Walkthrough

### Step 1: Landing Page
- Go to `http://localhost:3000`.
- Click **"Start Voice Interview"**.

### Step 2: Resume Upload
- Drag and drop the provided sample resume:
  `sample_resumes/alex_morgan_resume.pdf`
- Click **"Analyze Resume & Generate Questions"**.
- PyMuPDF extracts digital text; OpenAI extracts the structured candidate profile and generates 10–15 tailored questions.

### Step 3: Candidate Profile Confirmation
- Inspect the extracted details: Name (Alex Morgan), Skills (Python, PyTorch, CNN, ViT, FastAPI, Docker), Experience, and Projects.
- Click **"Start Interview"**.

### Step 4: The Live Voice Interview
- In the interview chamber, click the primary **"Start Interview"** button.
- Your browser requests microphone permissions.
- The AI speaks the welcome instructions aloud.
- The AI speaks Question 1:
  > *"Tell me about yourself and your technical background in machine learning and distributed systems."*
- Speak your response into your microphone. Your spoken words are transcribed in real time.
- Click **"Submit & Continue"**.
- The AI evaluates your response. If you omitted key architectural rationale, it adaptively asks a follow-up question before proceeding.

### Step 5: Final Evaluation Report
- Upon answering questions or ending the session, you are redirected to `/report/[id]`.
- View your **Overall Score (e.g. 84/100)** with the official **"Human Review Recommended"** badge.
- Review scores across 5 pillars:
  - Technical Knowledge
  - Project Understanding
  - Problem Solving
  - Communication Clarity
  - Resume Understanding
- Read key strengths, areas for improvement, and the question-by-question breakdown.
- Click **"Print Report"** to export a clean PDF for the hiring committee.

---

## 9. Recruiter / Admin Dashboard

Navigate to **[http://localhost:3000/admin](http://localhost:3000/admin)**:
- View all completed and ongoing interviews.
- Inspect metrics: Total Interviews, Completed Sessions, and Average Technical Score.
- Search candidates by name or resume filename.
- Click **"View Report"** for any candidate to inspect their complete assessment.

---

## 10. Security & Privacy Standards

1. **Short-Lived Ephemeral Keys**:
   The client browser connects to OpenAI Realtime via an ephemeral session token generated dynamically by FastAPI (`POST /api/realtime/session`). No client can view or reuse the master API key.
2. **Objective AI Prompting**:
   The system prompts strictly prohibit evaluating accent, vernacular, gender, race, disability, or personal characteristics.
3. **Human In The Loop**:
   The system never issues automated rejections; all evaluations are stamped **"Human Review Recommended"**.

---

## 11. Deployment Guide (Vercel & Railway)

### Architecture
```text
Candidate ──HTTPS──> Vercel (Next.js) ──HTTPS──> Railway (FastAPI) ──> Railway PostgreSQL
                          │                                │
                          └────────── WebRTC Audio ────────┴──> OpenAI Realtime
```

### 1. Deploy PostgreSQL and FastAPI Backend on Railway

1. Sign up at [railway.app](https://railway.app/).
2. Click **New Project** -> **Provision PostgreSQL**.
3. Under the Postgres service, copy the **`DATABASE_URL`** connection string.
4. Click **New** -> **GitHub Repo** -> select `ai-voice-interviewer`.
5. Under service settings:
   - **Root Directory**: `backend`
   - **Start Command**:
     ```bash
     uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```
6. Add Environment Variables in Railway:
   ```env
   APP_ENV=production
   DATABASE_URL=postgresql+psycopg://... (your Railway Postgres URL)
   OPENAI_API_KEY=sk-proj-...
   FRONTEND_URL=https://your-frontend.vercel.app
   OPENAI_TEXT_MODEL=gpt-4o-mini
   OPENAI_REALTIME_MODEL=gpt-4o-realtime-preview-2024-12-17
   OPENAI_VOICE=alloy
   ```
7. Generate a public domain (e.g. `https://ai-voice-backend.up.railway.app`).
8. Run migrations on Railway:
   Open the Railway service CLI and run:
   ```bash
   alembic upgrade head
   ```

### 2. Deploy Next.js Frontend on Vercel

1. Sign up at [vercel.com](https://vercel.com/) and connect your GitHub repository.
2. Select your repository.
3. In Project Settings:
   - **Root Directory**: `frontend`
   - **Framework Preset**: Next.js
4. Add Environment Variable:
   ```env
   NEXT_PUBLIC_API_URL=https://ai-voice-backend.up.railway.app
   ```
5. Click **Deploy**.
6. Update `FRONTEND_URL` on Railway to match your Vercel URL (e.g. `https://ai-voice-interviewer.vercel.app`) to authorize CORS.

---

## 12. Common Errors & Troubleshooting

| Issue | Cause | Solution |
|---|---|---|
| `OpenAI API key is missing` | `OPENAI_API_KEY` not set in `backend/.env` | Open `backend/.env` and add your OpenAI key, then restart backend. |
| `psycopg.OperationalError: connection failed` | Docker or PostgreSQL not running | Run `docker compose up -d postgres`. Note: The system automatically falls back to SQLite (`interviewer.db`) if Postgres is offline. |
| `Cannot connect to microphone` | Browser permissions blocked | Click the lock/camera icon in the browser address bar and set Microphone to **Allow**. |
| `CORS Error in Browser Console` | `FRONTEND_URL` mismatch | In `backend/.env`, set `FRONTEND_URL=http://localhost:3000`. |
| `Alembic: Path doesn't exist: migrations` | Executing alembic from wrong folder | Run alembic from inside `backend/` or specify `-c backend/alembic.ini`. |

---

## 13. Future Automation (n8n Roadmap)

While this MVP is built completely standalone without third-party automation dependencies, its clean REST API architecture is designed for future n8n workflow integration:

```text
               n8n Workflow Engine
                        │
       ┌────────────────┼────────────────┐
       ▼                ▼                ▼
 Candidate         Slack / Email      HR Report
 Scheduling          Alerts          Sync to ATS
       │                │                │
       └────────────────┼────────────────┘
                        ▼
            AI Voice Interviewer API
```

Future automated workflows will include:
1. **Candidate Invitation Flow**: ATS triggers n8n -> generates personalized interview link -> emails candidate.
2. **HR Notifications**: On interview completion, n8n receives webhook -> posts summary report directly to Slack `#recruiting`.
3. **CRM / Google Sheets Integration**: Candidate scores and category metrics automatically logged to corporate recruitment dashboards.
