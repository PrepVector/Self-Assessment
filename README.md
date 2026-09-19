# 🧠 PrepVector Cognitive Assessment — AI-Powered Technical Evaluation Platform

> **An enterprise-grade, end-to-end technical evaluation platform designed to test Data Science Experts using FastAPI, React, Google Gemini 3.5 Flash, Playwright, and Hostinger SMTP.**

---

## 📖 Overview

Cognitive Assessment is a sophisticated technical evaluation engine designed to dynamically assess candidate proficiency across core Data Science domains.

The application utilizes a **React-based frontend** for frictionless candidate intake and testing, paired with a high-performance **FastAPI backend**. It automatically generates balanced assessment samples, evaluates submissions using **Google's Gemini AI**, renders visually stunning feedback reports natively as PDFs via **Playwright**, and asynchronously dispatches those reports directly to candidates using **Hostinger SMTP**.

The system demonstrates a fully decoupled, zero-dependency data architecture, utilizing dual persistence (local CSV and Google Sheets API) to eliminate external database bloat while maintaining strict data integrity.

---

# ✨ Key Features

- 🤖 **Gemini-Powered Evaluation** — Automated grading and deep technical blind-spot analysis
- 📄 **Playwright PDF Rendering** — Programmatic generation of highly styled, professional assessment reports
- 📧 **Native SMTP Delivery** — Asynchronous email dispatch via Hostinger SMTP (aiosmtplib)
- 📊 **Dynamic Smoke Sampler** — Algorithmic extraction of balanced 35-question quizzes from a 147-question master bank
- 🗄️ **Dual-Layer Persistence** — Instant local CSV logging backed by Google Sheets API integration
- 📈 **"Clean-70" Scoring Model** — Difficulty-weighted point distribution across 7 domains
- 🎨 **Automated Asset Generation** — Python scripts to dynamically generate chart and image assets for specific questions

---

# 🛠 Tech Stack

| Category | Technologies |
|-----------|--------------|
| Frontend | React (Vite), Tailwind CSS, React Markdown |
| Backend | FastAPI (Python 3.12+), Uvicorn |
| AI Engine | Google Gemini 3.5 Flash (Primary), Groq (Fallback) |
| PDF Rendering | Playwright, FPDF2 (Legacy Fallback) |
| Email Dispatch | Hostinger SMTP (aiosmtplib) |
| Data Persistence | Python CSV, Google Sheets API (gspread) |
| Asset Generation | Matplotlib, Seaborn, Plotly |

---

# 🏗 System Architecture

```text
                          Candidate
                              │
         ┌────────────────────┼─────────────────────┐
         │                    │                      │
         ▼                    ▼                      ▼
  Candidate Intake      Assessment Quiz         Report Delivery
      (React)          (Dynamic Sampling)         (Email Inbox)
         │                    │                       ▲
         └──────────────┬─────┘                       │
                         ▼                             │
                FastAPI Backend Core                   │
                         │                              │
         ┌───────────────┼───────────────┐              │
         ▼               ▼               ▼              │
   Google Sheets    CSV Logger     Gemini 3.5 AI         │
   (Persistence)   (Local Backup)   (Evaluation)         │
                                        │                │
                                        ▼                │
                                Playwright Engine        │
                              (PDF Report Render)        │
                                        │                │
                                        ▼                │
                              Hostinger SMTP Engine ─────┘
```

---

# 🤖 Core Developer Pipelines

## 1️⃣ The Question Bank Builder

The platform operates on a strict **147-question JSON bank** covering 7 domains (SQL, Python, Pandas, Data Visualization, Applied Statistics, Machine Learning, A/B Testing).

- **Location:** `scripts/build_question_bank.py`
- **Workflow:** Utilizes Pydantic validation to enforce strict formatting and LaTeX math generation.
- **Developer Tip:** To conserve API quota and prevent rate limits, generate one section at a time. Open the script, comment out completed sections in the `SECTIONS` array, and run the script for the specific target domain.

## 2️⃣ Dynamic Asset Generator

Questions requiring visual charts or graphs are handled autonomously.

- **Location:** `scripts/generate_images.py`
- **Workflow:** The script parses `data/question_bank.json`, identifies questions flagged for visual assets, generates the appropriate plots using Matplotlib/Seaborn, and saves them locally for the frontend to render.

---

# 📂 Project Structure

```text
Self-Assessment/
│
├── backend/
│   ├── app/
│   │   ├── agents/          # Gemini AI evaluation logic
│   │   ├── api/             # FastAPI routing (submit_answers.py)
│   │   └── services/        # Hostinger SMTP & Google Sheets logic
│   ├── data/                # CSV logs and question_bank.json
│   ├── generated_reports/   # Playwright PDF output directory
│   ├── scripts/             # Builder and asset generation scripts
│   ├── requirements.txt
│   └── .env
│
└── frontend/
    ├── src/
    │   ├── components/      # React UI components
    │   └── assets/
    ├── package.json
    └── tailwind.config.js
```

---

# 🚀 Local Development Setup

> You must run the **Backend** and **Frontend** concurrently in two separate terminal windows.

## Phase 1: Backend Setup (FastAPI)

```bash
# 1. Clone the repository and navigate to backend
git clone https://github.com/PrepVector/Self-Assessment.git

or

git clone -b ritam-development https://github.com/PrepVector/Self-Assessment.git

cd Self-Assessment/backend

# 2. Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# 3. Install dependencies and Playwright binaries
pip install -r requirements.txt
playwright install chromium

# 4. Start the Uvicorn ASGI server
uvicorn app.main:app --reload
```

The backend will run on **http://127.0.0.1:8000**

## Phase 2: Frontend Setup (React/Vite)

> Open a new terminal window.

```bash
# 1. Navigate to the frontend directory
cd Self-Assessment/frontend

# 2. Install Node dependencies
npm install

# 3. Start the Vite development server
npm run dev
```

Vite will serve the frontend on **http://localhost:5173**

---

# 🔐 Environment Variables

Create a `.env` file in the `backend/` directory. **Never commit this file to version control.**

```env
# AI & Persistence Configuration
GEMINI_API_KEY="your_google_gemini_key"
GEMINI_MODEL="gemini-3.5-flash"
GROQ_API_KEY="your_groq_key"
SPREADSHEET_ID="your_google_sheets_id"

# Hostinger SMTP Configuration
SMTP_HOST="smtp.hostinger.com"
SMTP_PORT=465
SMTP_USERNAME="internal@prepvector.com"
SMTP_PASSWORD="your_smtp_password"
SMTP_FROM="internal@prepvector.com"
```

---

⭐ If you found this project interesting, consider giving it a star!
