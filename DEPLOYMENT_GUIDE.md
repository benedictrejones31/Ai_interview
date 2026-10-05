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

## STEP 1: Deploy Backend & Database on Render (Free)

1. Push your repository to **GitHub**:
   ```bash
   git add -A
   git commit -m "feat: complete voice interview with resend email and video feed"
   git push -u origin master
   ```

2. Open [https://render.com](https://render.com) and sign in with GitHub.

3. Click **New +** &rarr; **Blueprint** (or **Web Service**):
   - Select your repository `https://github.com/benedictrejones31/Ai_interview.git`.
   - Render will detect the included `render.yaml` automatically, creating:
     - 1 Web Service (Python FastAPI Backend)
     - 1 PostgreSQL Database (Free Tier)

4. Configure the Environment Variables on Render:
   - `GEMINI_API_KEY`: Paste your Gemini API key (from Google AI Studio)
   - `GEMINI_MODEL`: `gemini-flash-latest`
   - `RESEND_API_KEY`: Paste your Resend API key (from https://resend.com/api-keys)
   - `RESEND_FROM`: `AI Voice Interviewer <onboarding@resend.dev>`
   - `HR_NOTIFICATION_EMAIL`: `benedictrejones3101@gmail.com`
   - `FRONTEND_URL`: (Paste your Vercel URL here in Step 2)
   - `DATABASE_URL`: Automatically linked from Render Postgres (or paste external Postgres URL)

5. Click **Apply / Deploy**. Once deployed, copy your backend URL:
   `https://ai-voice-interviewer-backend.onrender.com`

---

## STEP 2: Deploy Frontend on Vercel (Free & Instant)

1. Open [https://vercel.com](https://vercel.com) and sign in with GitHub.

2. Click **Add New...** &rarr; **Project**.
   - Select your repository: `benedictrejones31/Ai_interview`.

3. Configure Project Settings:
   - **Framework Preset**: Next.js
   - **Root Directory**: Click *Edit* and select `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`

4. Add Environment Variable:
   - Name: `NEXT_PUBLIC_API_URL`
   - Value: `https://ai-voice-interviewer-backend.onrender.com` *(your backend Render URL from Step 1)*

5. Click **Deploy**.
   - In ~60 seconds, your site is live at:
     `https://ai-interview-preview.vercel.app`

6. Return to Render and update `FRONTEND_URL` with your new Vercel address:
   - `FRONTEND_URL`: `https://ai-interview-preview.vercel.app`

---

## STEP 3: Automated HR Report Delivery via Resend (Active)

The application is pre-configured with **Resend** (https://resend.com):
- Every time an interview completes, the backend automatically generates a comprehensive PDF report and sends it to:
  `benedictrejones3101@gmail.com`
- Configure `RESEND_API_KEY` in Render environment variables (or in your local `backend/.env`)
- Sender: `AI Voice Interviewer <onboarding@resend.dev>`
- The candidate report page also includes an **Email Report to HR** button for instant manual re-dispatch, plus a **Download PDF** button.

---

## Testing Your Live Client Demo

1. Open your live Vercel URL on mobile or laptop.
2. Grant Camera and Microphone access.
3. Upload a sample resume.
4. Complete the 10-question AI Voice interview with live camera feed.
5. Review the comprehensive score report, download the PDF, and review the HR assessment.
