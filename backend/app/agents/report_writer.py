import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_ID = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

def generate_evaluation_report(score: int, total_questions: int, wrong_answers: list[dict]) -> str | None:
    """
    Generates a detailed, encouraging evaluation report in Markdown format
    using the Gemini API, given the user's score and wrong answers.
    """
    # Format the wrong answers into a readable block for the LLM prompt
    wrong_answers_formatted = ""
    for i, wa in enumerate(wrong_answers, 1):
        section_info = f" [Section: {wa.get('section_name')}]" if wa.get('section_name') else ""
        wrong_answers_formatted += f"""
Question {i}{section_info}:
- Text: {wa.get('question_text')}
- User's Choice: {wa.get('user_answer')}
- Correct Choice: {wa.get('correct_answer')}
- Explanation: {wa.get('explanation', 'N/A')}
"""

    success_rate = (score / total_questions) * 100 if total_questions > 0 else 0

    prompt = f"""
    You are an expert Data Science Career Coach and Technical Mentor. 
    A candidate has just completed a rigorous Data Science Expert technical assessment.
    
    Candidate Assessment Summary:
    - Final Score: {score} / {total_questions} ({success_rate:.1f}% Success Rate)
    
    Details of Incorrect Answers:
    {wrong_answers_formatted}
    
    Please write a highly detailed, professional, and encouraging evaluation report in Markdown format.
    
    Ensure the Markdown report follows this structure:
    1. **Executive Summary**: A high-level overview of the candidate's performance, acknowledging their score in an encouraging, constructive, and professional tone.
    2. **Strengths Analysis**: Highlight the areas they did well in (acknowledging they answered {score} out of {total_questions} correctly) and detail the capabilities they demonstrated.
    3. **Key Growth Areas**: Identify common themes or topics among their incorrect answers (e.g., SQL joins, Pandas grouping, applied statistics) and explain the conceptual gaps.
    4. **Constructive Review of Mistakes**: For each incorrect answer, break down the core concept in a highly educational way. Explain why their chosen option might be a common pitfall, why the correct answer is technically correct, and what rule or framework to apply next time.
    5. **Custom Actionable Study Plan**: Outline a practical step-by-step roadmap to bridge their technical gaps, recommending specific topics to review and strategies to tackle code-based multiple-choice questions.
    """

    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.6
            ),
        )
        return response.text
    except Exception as e:
        print(f"Error generating evaluation report in report_writer: {e}")
        return None
