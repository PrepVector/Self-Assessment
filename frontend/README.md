# Cognitive Assessment - AI-Powered Technical Evaluation Platform

**Cognitive Assessment** is an enterprise-grade, end-to-end technical evaluation platform designed to test Data Science Experts. It dynamically generates tailored assessments, automatically evaluates candidate submissions using Google's **Gemini AI**, renders comprehensive PDF reports featuring data visualizations, and seamlessly delivers them via email.

---

## 🧠 Architecture & Logic

This platform is built on a sophisticated, decoupled architecture that separates question generation, dynamic sampling, AI evaluation, and report delivery.

### 1. The Question Bank & AI Builder
The platform is powered by a robust JSON question bank containing exactly **147 questions** across **7 core Data Science sections** (SQL, Python, Pandas, Data Visualization, Applied Statistics, Machine Learning, A/B Testing).
*   **Distribution:** Each section contains 21 questions (8 Easy, 8 Moderate, 5 Advanced).
*   **The Validation Layer:** The question pool is generated via a strict AI pipeline (`build_question_bank.py`). This script utilizes **Pydantic validation layers** to enforce strict formatting, prevent context leakage, isolate domains (e.g., Python questions cannot accidentally test Pandas concepts), and guarantee pure LaTeX mathematics.

### 2. The Smoke Sampler & Scoring
When a candidate starts an assessment, the **Smoke Sampler** dynamically selects a balanced 35-question quiz from the main bank.
*   **Selection:** 5 questions per section (2 Easy, 2 Moderate, 1 Advanced).
*   **Scoring ("Clean-70" Model):** Points are weighted by difficulty (Easy = 1pt, Moderate = 2pts, Advanced = 4pts). The max score is 70 points (10 points per section).

### 3. AI Evaluation Agents & Reporting
*   **The Evaluator:** Integrates with Google's Gemini AI (using **Gemini 3.5 Flash** as the primary model) to evaluate candidate responses, identify technical blind spots, and generate highly detailed, personalized feedback reports.
*   **Chart Generator Utils:** A backend utility dynamically builds visual components (using Matplotlib/Seaborn/Plotly) that are embedded directly into the final PDF.
*   **Playwright Renderer:** Programmatically transforms the AI's Markdown report into a beautifully styled, professional PDF document[cite: 4].

### 4. Frictionless Intake & Email Dispatch
*   **Zero-Dependency Persistence:** Fully relies on standard Python CSV handling for instant, lightweight data persistence—no MongoDB or external database required[cite: 4].
*   **Resend Integration:** Captures candidate emails post-assessment and uses the Resend API to securely queue and dispatch final PDF reports directly to their inboxes[cite: 4].

---

## 🛠️ Tech Stack
*   **Frontend:** React (Vite), Tailwind CSS, React Markdown, React Confetti[cite: 4]
*   **Backend:** FastAPI (Python 3.12+) served via Uvicorn[cite: 4]
*   **AI Engine:** Google GenAI SDK (Gemini Models), Groq (Fallback)[cite: 4]
*   **PDF Rendering:** Playwright[cite: 4]
*   **Email Dispatch:** Resend API[cite: 4]

---

## 💻 Local Development Setup

To run this application locally, you will need to run the Backend and the Frontend simultaneously in two separate terminal windows[cite: 4].

### Phase 1: Backend Setup (FastAPI)
FastAPI is the web framework we use to build the backend API, but it requires an ASGI (Asynchronous Server Gateway Interface) server to actually run and listen for web traffic[cite: 4]. We use **Uvicorn** for this purpose[cite: 4].

**1. Clone and Prepare**
```bash
# Clone the repository
git clone [https://github.com/PrepVector/Self-Assessment.git](https://github.com/PrepVector/Self-Assessment.git)

# Navigate to the backend directory
cd Self-Assessment/backend

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install required backend dependencies
pip install -r requirements.txt

# Install Playwright browsers (required for PDF rendering)
playwright install chromium

2. Environment Variables
Create a .env file inside the backend directory[cite: 4]. You will need to provision three API keys[cite: 4]:

Gemini: Get this from Google AI Studio[cite: 4].

Resend: Create a free account at Resend to get an API key[cite: 4]. (Note: On the free tier, you can only send emails to the address you registered with[cite: 4]).

Groq: Get this from the Groq Console[cite: 4].

Code snippet
GEMINI_API_KEY=your_gemini_api_key_here
RESEND_API_KEY=your_resend_api_key_here
GROQ_API_KEY=your_groq_api_key_here

3. Start the Backend Server

# Ensure your venv is activated, then start Uvicorn
uvicorn app.main:app --reload

The --reload flag ensures the server automatically restarts when you make code changes[cite: 4]. The backend will run on http://127.0.0.1:8000[cite: 4].

Phase 2: Frontend Setup (React/Vite)
Open a second terminal window (keep the backend running in the first)[cite: 4].

# Navigate to the frontend directory
cd frontend

# Install Node dependencies
npm install

# Start the Vite development server
npm run dev

Vite will provide a local URL (e.g., http://localhost:5173) to view the application in your browser[cite: 4].

📚 Managing the Question Bank
The application uses an AI-driven script (build_question_bank.py) to generate the underlying 147-question pool[cite: 4].

Best Practice: To conserve API quota, prevent rate limits, and reduce execution time, it is highly advisable to generate only one section at a time[cite: 4]. Open build_question_bank.py, comment out the completed sections inside the SECTIONS array, and leave only your target section uncommented[cite: 4].

# Ensure you are in the backend directory with your venv activated
cd backend

# Run the builder script
python -m scripts.build_question_bank

