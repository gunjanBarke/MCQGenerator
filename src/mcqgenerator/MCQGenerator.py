import os
import json
import logging
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ── Load .env ─────────────────────────────────────────────
load_dotenv()

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/mcq_generator.log",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def generate_mcqs(
    text: str,
    num_questions: int,
    difficulty: str,
    num_options: int,
    subject: str,
    groq_api_key: str,        # ← coming from Streamlit UI
    model_name: str = "llama-3.3-70b-versatile"
):
    try:
        # ── Use key from UI, fallback to .env ─────────────
        api_key = groq_api_key.strip() if groq_api_key.strip() else os.getenv("GROQ_API_KEY")

        if not api_key:
            raise ValueError("Groq API key not found!")

        logger.info(f"Starting MCQ generation | questions={num_questions} | difficulty={difficulty}")

        splitter = RecursiveCharacterTextSplitter(chunk_size=3000, chunk_overlap=200)
        chunks = splitter.split_text(text)
        selected_chunk = chunks[0] if chunks else text

        llm = ChatGroq(
            api_key=api_key,        # ✅ using resolved key
            model_name=model_name,
            temperature=0.5,
        )

        subject_text = f"Focus on the topic: {subject}." if subject else ""

        prompt = ChatPromptTemplate.from_template("""
You are an expert MCQ generator. Generate {num_questions} multiple choice questions
from the given text.

Difficulty Level: {difficulty}
{subject_text}
Each question must have exactly {num_options} options.

Text:
{text}

Return ONLY a valid JSON array like this (no extra text):
[
    {{
        "question": "Question here?",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "correct_answer": "Option A",
        "explanation": "Brief explanation why this is correct."
    }}
]
""")

        chain = prompt | llm | JsonOutputParser()

        mcqs = chain.invoke({
            "num_questions": num_questions,
            "difficulty": difficulty,
            "num_options": num_options,
            "subject_text": subject_text,
            "text": selected_chunk
        })

        logger.info(f"Successfully generated {len(mcqs)} MCQs")
        return mcqs

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise e