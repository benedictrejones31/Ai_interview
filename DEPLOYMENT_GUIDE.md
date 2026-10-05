# Step-by-Step Production Hosting Guide
## Showcasing "AI Voice Interviewer" to Clients Online

This guide walks you through deploying your application with live public URLs (`https://your-app.vercel.app` and `https://your-api.onrender.com`) for free.

---

### Architecture Overview

```
 [ Candidate / Client Browser ]
              │
              ▼
   Vercel Edge Network (Next.js Frontend)
   https://ai-voice-interviewer.vercel.app
              │
              │ API Calls & Audio Transcripts
              ▼
   Render / Railway (FastAPI Backend)
   https://ai-voice-backend.onrender.com
              │
      ┌───────┴────────┐
      ▼                ▼
Render PostgreSQL   Google Gemini API
 (Neon / Supabase)   (100% Free AI Engine)
```

---

## STEP 1: Deploy Backend on Render (100% Free)

1. Open **[https://render.com](https://render.com)** and sign in with GitHub.

2. Click **New +** &rarr; select **Web Service**.
   - Choose your repository: `https://github.com/benedictrejones31/Ai_interview.git` (or select `benedictrejones31/Ai_interview`).

3. Configure Web Service settings:
   - **Name**: `ai-voice-interviewer-backend`
   - **Region**: Choose nearest (e.g. Frankfurt, Oregon, Singapore)
   - **Branch**: `master`
   - **Root Directory**: `backend` *(CRITICAL: Must set to `backend`!)*
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: Select **Free ($0/month)**

4. Add Environment Variables (click "Add Environment Variable" below):
   - `GEMINI_API_KEY`: Paste your Gemini API key (from Google AI Studio)
   - `GEMINI_MODEL`: `gemini-flash-latest`
   - `RESEND_API_KEY`: Paste your Resend API key (from https://resend.com/api-keys)
   - `RESEND_FROM`: `AI Voice Interviewer <onboarding@resend.dev>`
   - `HR_NOTIFICATION_EMAIL`: `benedictrejones3101@gmail.com`
   - `FRONTEND_URL`: Leave blank for now (or set to your preliminary Vercel URL)

5. Click **Create Web Service**. Once deployed, copy your backend URL:
   `https://ai-voice-interviewer-backend-xxxx.onrender.com`

---

## STEP 2: Deploy Frontend on Vercel (100% Free)

1. Open **[https://vercel.com](https://vercel.com)** and sign in with GitHub.

2. Click **Add New...** &rarr; **Project**.
   - Select your repository: `benedictrejones31/Ai_interview`.

3. Configure Project Settings:
   - **Framework Preset**: Next.js
   - **Root Directory**: Click *Edit* and select `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`

4. Add Environment Variable:
   - **Key**: `NEXT_PUBLIC_API_URL`
   - **Value**: `https://ai-voice-interviewer-backend-xxxx.onrender.com` *(your backend Render URL from Step 1, without trailing slash)*

5. Click **Deploy**.
   - In ~60 seconds, your site is live at:
     `https://your-project.vercel.app`

6. Return to Render and update `FRONTEND_URL` with your new Vercel address:
   - `FRONTEND_URL`: `https://your-project.vercel.app`

---

## STEP 3: Automated HR Report Delivery via Resend

The application uses **Resend** (https://resend.com) to email the assessment PDF:
- Every time an interview completes, the backend automatically generates a comprehensive PDF report and sends it to:
  `benedictrejones3101@gmail.com`
- Configure `RESEND_API_KEY` in Render environment variables (or local `backend/.env`)
- Sender: `AI Voice Interviewer <onboarding@resend.dev>`
- The candidate report page also includes an **Email Report to HR** button for instant manual re-dispatch, plus a **Download PDF** button.

---

## Testing Your Live Client Demo

1. Open your live Vercel URL on mobile or laptop.
2. Grant Camera and Microphone access.
3. Upload a sample resume.
4. Complete the 10-question AI Voice interview with live camera feed.
5. Review the comprehensive score report, download the PDF, and verify the email arrived in your inbox.
