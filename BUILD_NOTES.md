# AI Voice Interviewer — Architecture & Build Notes

## 1. Executive Architecture Overview

AI Voice Interviewer is a production-ready, standalone full-stack platform for conducting automated, adaptive mock and technical interviews using AI voice interaction.

### Tech Stack
- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS, WebRTC (`RTCPeerConnection` & `RTCDataChannel`), Web Speech API fallback.
- **Backend**: FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic, PyMuPDF (`fitz`), Async HTTP client (`httpx`).
- **Database**: PostgreSQL (with psycopg 3 binary driver), resilient SQLite fallback for instant zero-dependency local runs.
- **AI Models**:
  - **OpenAI Text / Structured Outputs**: `gpt-4o-mini` (or configurable) for resume extraction, 10–15 personalized question generation, objective answer evaluation, and final comprehensive report synthesis.
  - **OpenAI Realtime WebRTC**: `gpt-4o-realtime-preview-2024-12-17` for two-way, low-latency voice dialogue.

---

## 2. Key Security Principles

1. **Zero Browser Exposure of Permanent API Keys**:
   - The permanent `OPENAI_API_KEY` resides strictly on the FastAPI server environment.
   - Frontend never imports `OPENAI_API_KEY` (never prefixed with `NEXT_PUBLIC_*`).
   - When an interview starts, the frontend calls `POST /api/realtime/session`.
   - FastAPI communicates with OpenAI's `/v1/realtime/sessions` endpoint using the backend key to mint a short-lived ephemeral client token (`client_secret.value`).
   - The browser connects to OpenAI's WebRTC gateway directly with this short-lived credential.

2. **Objective, Ethical Evaluation Standards**:
   - The evaluation prompts explicitly forbid rating or penalizing accent, dialect, speech cadence, gender, race, disability, or other protected demographic characteristics.
   - Evaluation is strictly evidence-based and grounded in engineering correctness, architectural depth, relevance, and logical clarity.
   - The platform never makes automated hiring rejections; final reports are labeled **"Human Review Recommended"** for recruiter oversight.

---

## 3. Database Schema Design

- **`candidates`**: Stores candidate ID, name, email, original resume filename, extracted raw text, structured profile JSON (`skills`, `projects`, `experience`, `education`, `certifications`), and timestamps.
- **`interviews`**: Tracks interview session state (`pending`, `in_progress`, `completed`), started/completed timestamps, overall score, final synthesized report JSON, and question counters.
- **`questions`**: Stores generated interview questions (order, category, question text, difficulty, skills tested, expected topics, follow-up flags, and parent question IDs).
- **`answers`**: Records candidate responses (transcript, duration, evaluation scores, correctness, relevance, technical depth, clarity, strengths, missing points, and follow-up recommendations).

---

## 4. Controlled Adaptive Questioning

- Standard interviews generate **10 to 15 questions** directly tied to the candidate's actual projects, languages, and technologies.
- If a candidate provides a surface-level answer or mentions an architecture without explaining their reasoning, the AI evaluator sets `needs_follow_up: true` and generates a targeted follow-up.
- Follow-ups are bounded by a strict rule: **maximum 1 follow-up per main topic** and a maximum total question cap, preventing endless loops or repetitive queries.

---

## 5. Verification & Test Coverage

- **PyMuPDF Parser**: Tested against valid digital PDFs, empty files, and insufficient text thresholds.
- **Data Models**: Verified SQLAlchemy relationships, cascading deletes, foreign keys, and indexes.
- **API Endpoints**: Tested `/health`, `/api/resumes/upload` validation, `/api/interviews/{id}`, `/api/interviews/{id}/start`, and `/api/admin/interviews`.
- **Frontend Build**: Compiled with Next.js production build (`next build`), verifying static generation and dynamic route rendering across all pages.
