"""
cv_parser.py
Extracts text from a .docx file, sends it to Ollama Cloud (gpt-oss:120b),
and returns a structured JSON object representing the CV.

Ollama Cloud integration matches ai_service.py from BridgeSpace:
  - Base URL : https://ollama.com
  - Endpoint : /api/generate  (streaming, line-by-line)
  - Auth     : Authorization: Bearer <OLLAMA_API_KEY>
  - Model    : gpt-oss:120b
"""

import json
import logging
import os
import re

import requests

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = os.environ.get('OLLAMA_URL', 'https://ollama.com')
OLLAMA_MODEL    = os.environ.get('OLLAMA_MODEL', 'gpt-oss:120b')
OLLAMA_API_KEY  = os.environ.get('OLLAMA_API_KEY', '')

# ── JSON schema prompt ────────────────────────────────────────────────────────

PROMPT_TEMPLATE = """You are a CV parser. Given the raw text of a CV/resume below, extract ALL information and return it as a single valid JSON object.

RULES:
- Return ONLY the raw JSON object — no markdown, no code fences, no explanation
- If a field is absent in the CV use null or []

Required schema:
{{
  "name": "string",
  "title": "string",
  "location": "string",
  "email": "string",
  "phone": "string",
  "website": "string",
  "summary": "string",
  "competencies": {{
    "<group label>": ["skill1", "skill2"]
  }},
  "experience": [
    {{
      "company": "string",
      "role": "string",
      "period": "string",
      "bullets": ["string"]
    }}
  ],
  "projects": [
    {{
      "name": "string",
      "url": "string",
      "role": "string",
      "tools": "string",
      "description": "string",
      "bullets": ["string"],
      "stack": ["string"]
    }}
  ],
  "education": [
    {{
      "degree": "string",
      "institution": "string",
      "period": "string"
    }}
  ],
  "certifications": ["string"],
  "languages": ["string"],
  "active_projects": ["string"],
  "volunteer": "string"
}}

CV text:
{cv_text}

JSON:"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _headers() -> dict:
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OLLAMA_API_KEY}",
    }


def _ask(prompt: str, max_retries: int = 2) -> str:
    """Stream a generate call to Ollama Cloud and return the full response text."""
    payload = {"model": OLLAMA_MODEL, "prompt": prompt}

    for attempt in range(max_retries + 1):
        try:
            full_response = ""
            with requests.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                headers=_headers(),
                json=payload,
                stream=True,
                timeout=180,
            ) as r:
                r.raise_for_status()
                for line in r.iter_lines():
                    if line:
                        try:
                            data = json.loads(line.decode("utf-8"))
                            if "response" in data:
                                full_response += data["response"]
                        except json.JSONDecodeError:
                            continue
            return full_response.strip()

        except requests.exceptions.RequestException as exc:
            logger.warning("Ollama Cloud attempt %d/%d failed: %s", attempt + 1, max_retries + 1, exc)
            if attempt == max_retries:
                raise RuntimeError(f"Ollama Cloud request failed after {max_retries + 1} attempts: {exc}") from exc

    return ""


# ── Public API ────────────────────────────────────────────────────────────────

def extract_text_from_docx(filepath: str) -> str:
    """Extract plain text from a .docx using python-docx."""
    try:
        from docx import Document
    except ImportError:
        raise RuntimeError("python-docx is not installed. Run: pip install python-docx")

    doc = Document(filepath)
    paragraphs = [para.text.strip() for para in doc.paragraphs if para.text.strip()]
    return '\n'.join(paragraphs)


def parse_cv_with_ollama(filepath: str) -> dict:
    """
    1. Extract plain text from the .docx
    2. Send to Ollama Cloud via /api/generate (streaming)
    3. Parse the streamed response as JSON and return
    """
    raw_text = extract_text_from_docx(filepath)
    if not raw_text.strip():
        raise ValueError("Could not extract any text from the uploaded file.")

    prompt = PROMPT_TEMPLATE.format(cv_text=raw_text)
    raw = _ask(prompt)

    # Strip any accidental markdown code fences
    clean = re.sub(r'^```(?:json)?\s*', '', raw.strip())
    clean = re.sub(r'\s*```$', '', clean.strip())

    try:
        return json.loads(clean)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Ollama returned invalid JSON: {exc}\n\n"
            f"Raw response (first 500 chars):\n{clean[:500]}"
        ) from exc
