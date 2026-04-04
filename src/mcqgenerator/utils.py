import os
import json
import logging
import tempfile
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    Docx2txtLoader,
    CSVLoader,
    WebBaseLoader
)

logger = logging.getLogger(__name__)


def read_file(uploaded_file) -> tuple:
    """Read any file type and return text."""
    try:
        file_name = uploaded_file.name
        extension = os.path.splitext(file_name)[1].lower()
        logger.info(f"Reading file: {file_name} | type: {extension}")

        if extension == ".pdf":
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name
            loader = PyPDFLoader(tmp_path)
            pages = loader.load()
            text = "\n".join([p.page_content for p in pages])
            os.unlink(tmp_path)
            return text, f"📄 PDF — {len(pages)} pages"

        elif extension == ".txt":
            with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode='wb') as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name
            loader = TextLoader(tmp_path)
            docs = loader.load()
            text = "\n".join([d.page_content for d in docs])
            os.unlink(tmp_path)
            return text, f"📃 TXT — {len(text)} characters"

        elif extension == ".docx":
            with tempfile.NamedTemporaryFile(delete=False, suffix=".docx", mode='wb') as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name
            loader = Docx2txtLoader(tmp_path)
            docs = loader.load()
            text = "\n".join([d.page_content for d in docs])
            os.unlink(tmp_path)
            return text, f"📝 DOCX — {len(text)} characters"

        elif extension == ".csv":
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode='wb') as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name
            loader = CSVLoader(tmp_path)
            docs = loader.load()
            text = "\n".join([d.page_content for d in docs])
            os.unlink(tmp_path)
            return text, f"📊 CSV — {len(docs)} rows"

        else:
            raise ValueError(f"Unsupported file type: {extension}")

    except Exception as e:
        logger.error(f"Error reading file: {str(e)}")
        raise e


def read_url(url: str) -> tuple:
    """Read URL — tries WebBaseLoader first, falls back to requests+BS4."""
    import requests
    from bs4 import BeautifulSoup
    from langchain_community.document_loaders import WebBaseLoader

    # ── Method 1: WebBaseLoader ───────────────────────────
    try:
        logger.info(f"Trying WebBaseLoader for: {url}")
        loader = WebBaseLoader(url)
        docs = loader.load()
        text = "\n".join([d.page_content for d in docs])

        if text and len(text) > 100:
            logger.info(f"WebBaseLoader success | chars={len(text)}")
            return text, f"🌐 URL — {len(text)} characters"

    except Exception as e:
        logger.warning(f"WebBaseLoader failed: {str(e)} | Trying fallback...")

    # ── Method 2: requests + BeautifulSoup (fallback) ─────
    try:
        logger.info(f"Trying requests+BS4 for: {url}")
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        text = soup.get_text(separator="\n")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        text = "\n".join(lines)

        if not text or len(text) < 100:
            raise ValueError("Could not extract meaningful content from URL")

        logger.info(f"BS4 fallback success | chars={len(text)}")
        return text, f"🌐 URL — {len(text)} characters"

    except Exception as e:
        logger.error(f"Both methods failed: {str(e)}")
        raise Exception(f"Could not load URL. Site may be blocking scrapers. Error: {str(e)}")
    
    
def get_table_data(mcqs: list) -> list:
    """Convert MCQs to table format for display."""
    try:
        table_data = []
        for i, mcq in enumerate(mcqs):
            table_data.append({
                "Q No.": i + 1,
                "Question": mcq["question"],
                "Correct Answer": mcq["correct_answer"],
                "Explanation": mcq["explanation"]
            })
        logger.info(f"Table data created for {len(table_data)} MCQs")
        return table_data
    except Exception as e:
        logger.error(f"Error creating table data: {str(e)}")
        raise e


def save_response(mcqs: list, filepath="Response.json"):
    """Save MCQs to JSON file."""
    try:
        with open(filepath, "w") as f:
            json.dump(mcqs, f, indent=2)
        logger.info(f"MCQs saved to {filepath}")
    except Exception as e:
        logger.error(f"Error saving response: {str(e)}")
        raise e