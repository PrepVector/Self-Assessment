import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_ID = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

# --- 1. The Upgraded Pydantic Schema ---
class Question(BaseModel):
    id: str = Field(description="Unique ID, e.g., 'sql_q1'")
    difficulty: str = Field(description="Must be 'Easy', 'Moderate', 'Hard', or 'Expert'")
    text: str = Field(description="The question text. MUST include code snippets or practical scenarios where applicable.")
    options: list[str] = Field(description="Exactly 4 multiple choice options. Can be code outputs.")
    correct_answer: str = Field(description="The exact text of the correct option")
    explanation: str = Field(description="Detailed explanation of why this is correct and others are wrong.")

class QuizSection(BaseModel):
    section_name: str = Field(description="The specific Data Science Expert topic")
    questions: list[Question] = Field(description="Exactly 5 questions with progressive difficulty")

class AssessmentQuiz(BaseModel):
    role: str = Field(description="Hardcoded to 'Data Science Expert'")
    sections: list[QuizSection] = Field(description="Exactly 7 sections testing the full Data Science Expert pipeline")

# --- 2. The Stricter Core Agent Function ---
def generate_dse_quiz() -> str | None:
    prompt = """
    You are a Senior Technical Recruiter at PrepVector creating a rigorous, advanced assessment for a Data Science Expert candidate.
    
    CRITICAL REQUIREMENTS:
    1. Create EXACTLY 7 sections in this STRICT ORDER:
       Section 1: SQL
       Section 2: Python
       Section 3: Pandas
       Section 4: Data Visualization
       Section 5: Applied Statistics
       Section 6: Machine Learning
       Section 7: A/B Testing
    2. Create EXACTLY 5 questions per section (35 questions total).
    3. PROGRESSIVE DIFFICULTY: Within each section, Q1 must be 'Easy', Q2/Q3 'Moderate', Q4 'Hard', and Q5 'Expert'.
    4. NO TRIVIA: Do NOT ask basic definition questions (e.g., "What does SELECT do?", "What is a variable?").
    5. USE SCENARIOS & CODE: Moderate to Expert questions MUST involve analyzing a provided code snippet, predicting the output of a query, debugging an error, or solving a real-world data science case. Use standard markdown code blocks inside the question text.
    6. DATA CLEANING IN SQL: Heavily embed data cleaning scenarios directly into SQL questions. SQL questions must include topics such as handling NULL values (COALESCE, IS NULL), deduplicating rows (ROW_NUMBER with PARTITION BY), type casting, cleaning inconsistent string formats with functions like TRIM/LOWER/UPPER, and filtering out corrupt or out-of-range data in WHERE clauses.
    7. DATA CLEANING IN PYTHON: Heavily embed data cleaning scenarios directly into Python questions. Python questions must include topics such as handling missing values, stripping whitespace from strings, validating data types, removing duplicates, applying regex-based cleaning, and writing functions that enforce constraints or flag anomalies in raw datasets.
    8. Do NOT create standalone sections for 'Data Cleaning' or 'Business Logic'. These concepts must be woven into the SQL and Python sections respectively.
    """

    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=AssessmentQuiz,
                temperature=0.3 # Lower temperature for highly logical, consistent code questions
            ),
        )
        return response.text
        
    except Exception as e:
        print(f"Error generating quiz: {e}")
        return None

if __name__ == "__main__":
    print(f"Generating Advanced Data Science Expert Quiz using {MODEL_ID}...\n")
    quiz_json = generate_dse_quiz()
    
    if quiz_json:
        parsed = json.loads(quiz_json)
        print(json.dumps(parsed, indent=2))
    else:
        print("Failed to generate quiz.")