from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import generate_quiz

# Initialize the FastAPI app
app = FastAPI(title="Cognitive Career Assessment API")

# Configure CORS so your React frontend (running on a different port) can talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, change this to your React app's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect the routing
app.include_router(generate_quiz.router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Cognitive Career Assessment API. The backend is running."}