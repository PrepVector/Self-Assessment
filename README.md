# 🧠 PrepVector Cognitive Assessment — AI-Powered Technical Evaluation Platform

> **An end-to-end technical assessment platform for evaluating Data Science expertise using React, FastAPI, Google Gemini, Playwright, Google Sheets, and Hostinger SMTP.**

---

## 📖 Overview

The **PrepVector Cognitive Assessment** platform is an AI-powered technical evaluation system designed to dynamically assess candidate proficiency across core Data Science domains.

The application uses a **React + Vite** frontend for frictionless candidate interaction and a **FastAPI** backend for assessment generation, scoring, and AI-driven analysis. It generates balanced 35-question quizzes from a master bank, scores them using a difficulty-weighted model, and leverages **Google Gemini** to produce deep technical insights. Finally, it natively renders professional PDF reports via **Playwright** and asynchronously dispatches them to candidates using **Hostinger SMTP**.

---

# ✨ Key Features

- 🤖 **AI-Powered Evaluation** — Gemini-based analysis of candidate performance with robust fallback handling (Groq / alternative Gemini models)
- 📊 **Dynamic Stratified Sampling** — Algorithmic generation of balanced 35-question quizzes from a 147-question master bank
- 🧮 **"Clean-70" Scoring Model** — Difficulty-weighted point distribution across 7 core Data Science domains
- 📄 **Native PDF Rendering** — Programmatic generation of highly styled assessment reports using Playwright/Chromium
- 📧 **SMTP Email Dispatch** — Asynchronous delivery of PDF reports natively through Hostinger SMTP
- 🗄️ **Dual-Layer Persistence** — Instant local CSV logging backed by Google Sheets API synchronization
- 🎨 **Automated Asset Generation** — Python scripts to dynamically generate necessary charts and visual assets using Matplotlib

---

# 🛠 Tech Stack

| Category | Technologies |
|-----------|--------------|
| Frontend | React (Vite), Tailwind CSS, React Markdown |
| Backend | FastAPI (Python 3.12.x), Uvicorn |
| AI Engine | Google Gemini (Primary), Groq (Fallback) |
| PDF Generation | Playwright, Chromium, FPDF2 (Legacy Fallback) |
| Email Dispatch | Hostinger SMTP (aiosmtplib) |
| Data Persistence | Python CSV, Google Sheets API (gspread) |
| Asset Generation | Matplotlib, NumPy |

---

# 🏗 System Architecture

```text
                         ┌──────────────────┐
                         │    Candidate     │
                         └────────┬─────────┘
                                  │
                                  ▼
                      ┌────────────────────────┐
                      │    React Frontend      │
                      │    Vite + Tailwind     │
                      └───────────┬────────────┘
                                  │
                                  ▼
                      ┌────────────────────────┐
                      │    FastAPI Backend     │
                      └───────────┬────────────┘
                                  │
            ┌─────────────────────┼─────────────────────┐
            │                     │                     │
            ▼                     ▼                     ▼
    ┌───────────────┐     ┌───────────────┐     ┌───────────────┐
    │ Question Bank │     │    Scoring    │     │   AI Engine   │
    │    147 Qs     │     │   Clean-70    │     │    Gemini     │
    └───────────────┘     └───────────────┘     └───────┬───────┘
                                                        │
                                                ┌───────┴───────┐
                                                │Model Fallbacks│
                                                └───────┬───────┘
                                                        │
            ┌──────────────────┬────────────────────────┘
            │                  │                  │
            ▼                  ▼                  ▼
    ┌──────────────┐   ┌──────────────┐   ┌────────────────┐
    │ CSV Logging  │   │ Google Sheets│   │ Report Engine  │
    └──────────────┘   └──────────────┘   └───────┬────────┘
                                                  │
                                                  ▼
                                          ┌──────────────┐
                                          │  Playwright  │
                                          │ PDF Renderer │
                                          └───────┬──────┘
                                                  │
                                                  ▼
                                          ┌──────────────┐
                                          │  Hostinger   │
                                          │  SMTP Email  │
                                          └──────────────┘
```

---

# 🎯 Assessment & Scoring Methodology

The platform evaluates candidates across **7 Data Science domains**: SQL, Python, Pandas, Data Visualization, Applied Statistics, Machine Learning, and A/B Testing.

- **The Bank** — 147 total questions (21 per domain)
- **The Sample** — Each assessment dynamically samples 35 questions (5 per domain: 2 Easy, 2 Moderate, 1 Advanced)
- **Clean-70 Scoring** — Points are awarded by difficulty (Easy = 1 pt, Moderate = 2 pts, Advanced = 4 pts). Each domain contributes a maximum of 10 points, resulting in a normalized final score out of **70**

---

# 📂 Project Structure

```text
Self-Assessment/
│
├── backend/
│   ├── app/
│   │   ├── agents/          # Gemini AI evaluation logic
│   │   ├── api/             # FastAPI routing
│   │   └── services/        # Hostinger SMTP & Google Sheets logic
│   ├── data/                # CSV logs and question_bank.json
│   ├── generated_reports/   # Playwright PDF output directory (Ignored by Git)
│   ├── scripts/             # Builder and asset generation scripts
│   ├── requirements.txt
│   └── .env
│
├── frontend/
│   ├── src/
│   └── package.json
│
└── report_reference/
    ├── skill_assessment_report_template.html
    ├── resources_section.html
    ├── study_calendar_section_v3.html
    └── report_generation_algorithm.md
```

> **Note:** The `report_reference/` directory contains the HTML templates and supporting files required by the backend's PDF report-generation pipeline. The `skill_assessment_report_template.html` file is required at runtime for generating the final assessment PDF.

---

# 🚀 Local Development Setup

> The project consists of two decoupled applications that must be run **concurrently**. Ensure you have **Python 3.12.x** and **Node.js** installed.

## Phase 1: Backend Setup (FastAPI)

```bash
# 1. Clone the repository and navigate to backend
git clone https://github.com/PrepVector/Self-Assessment.git
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

# 🔐 Environment Configuration

Create a `.env` file in the `backend/` directory. **Never commit this file to version control.**

```env
# AI Configuration
GEMINI_API_KEY="your_google_gemini_api_key"
GEMINI_MODEL="gemini-3.5-flash"
GROQ_API_KEY="your_groq_api_key"

# Data Persistence
SPREADSHEET_ID="your_google_sheet_id"

# Hostinger SMTP
SMTP_HOST="smtp.hostinger.com"
SMTP_PORT=465
SMTP_USERNAME="internal@prepvector.com"
SMTP_PASSWORD="your_smtp_password"
SMTP_FROM="internal@prepvector.com"
```

## Additional Credentials

Google Sheets functionality requires a valid `credentials.json` file placed in the `backend/` directory. This is excluded from Git via `.gitignore` and must be provisioned manually in your deployment environment.

---

# 🌍 Production Deployment Notes

When moving from local development to production, the IT/DevOps team must configure the following:

- **API URLs** — Update the frontend to point to the production backend URL instead of `http://localhost:8000`
- **CORS Configuration** — Update the FastAPI `allow_origins` array to accept requests from the deployed frontend domain
- **Secret Management** — Provision all required environment variables securely, including Gemini, Groq, Google Sheets, and SMTP credentials
- **Google Sheets Authentication** — Provision the required `credentials.json` securely in the production environment
- **Report Templates** — Ensure the root-level `report_reference/` directory is available to the backend at runtime. The `skill_assessment_report_template.html` file is required for PDF report generation
- **Playwright/Chromium** — Ensure the production environment has the required Playwright/Chromium runtime support for PDF generation
- **SMTP** — Ensure the production environment can connect to Hostinger SMTP on port 465

---

⭐ If you found this project interesting, consider giving it a star!
