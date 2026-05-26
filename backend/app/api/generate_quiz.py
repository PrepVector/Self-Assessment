from fastapi import APIRouter, HTTPException
from app.agents.quiz_master import generate_da_quiz
import json

router = APIRouter()

# Notice we removed the Pydantic QuizRequest model because we don't need user input anymore!

@router.post("/generate-quiz")
def generate_quiz_endpoint():
    """
    Endpoint that returns the advanced Data Analyst JSON quiz.
    """
    # Call our new, hardcoded function
    quiz_json_string = generate_da_quiz()
    
    if not quiz_json_string:
        raise HTTPException(status_code=500, detail="Failed to generate quiz from AI.")
    
    return json.loads(quiz_json_string)