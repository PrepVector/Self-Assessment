"""
main.py
=======
FastAPI application entry point.

MongoDB has been fully removed (Phase 5.5).  The app now relies entirely on:
  • backend/data/question_bank.json  — pre-generated question pool
  • backend/data/user_assessments.csv — append-only result log
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.api import generate_quiz, submit_answers, download_report

# Load environment variables
load_dotenv()

# Initialize the FastAPI app (no lifespan / DB connections needed)
app = FastAPI(title="Cognitive Career Assessment API")

# Configure CORS — explicitly allow the Vite frontend origin.
# NOTE: allow_credentials=True is incompatible with allow_origins=["*"],
#       so we must list the exact origin(s).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect the routers
app.include_router(generate_quiz.router, prefix="/api")
app.include_router(submit_answers.router, prefix="/api")
app.include_router(download_report.router, prefix="/api")


@app.get("/")
def read_root():
    return {"message": "Welcome to the Cognitive Career Assessment API. The backend is running."}