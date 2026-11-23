"""Configuration and constants for the AI File Organizer."""

import os

# Default Gemini model and fallback models for high availability
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
FALLBACK_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3.6-flash",
]

# Default categories when the user hasn't defined their own
DEFAULT_CATEGORIES = [
    "Invoices & Finance",
    "Resumes & Career",
    "Documents & Notes",
    "Spreadsheets & Data",
    "Code & Development",
    "Media & Images",
]

# File extensions safe for deep content scanning
SAFE_CONTENT_EXTENSIONS = {
    ".txt",
    ".md",
    ".csv",
    ".json",
    ".pptx",
    ".py",
    ".pdf",
    ".html",
    ".xml",
    ".log",
    ".docx",
    ".xlsx",
    ".doc",
    ".xls",
}

# Files and directories that should NEVER be moved or touched
IGNORED_FILES = {
    "file-organizer.py",
    "main.py",
    "README.md",
    "ai_categories.json",
    "organization_history.json",
    ".gitignore",
    ".env",
    "requirements.txt",
    "pyproject.toml",
    "test_pdf.py",
}

IGNORED_DIRECTORIES = {
    ".git",
    ".github",
    ".pytest_cache",
    "__pycache__",
    "venv",
    ".venv",
    "src",
    "tests",
    "sample_data",
}

# Filename-based classification prompt
CLASSIFICATION_PROMPT_TEMPLATE = """
You are an intelligent file organization assistant.

Your task is to decide which folder is the BEST place to organize the given file based ONLY on its filename and extension.

File name:
{file_name}

Extension:
{ext}

Available folders:
{categories}

CRITICAL RULES:
- If the filename is ambiguous, numerical, generic, or meaningless (such as "1", "2", "file", "doc", "test", "untitled", "download", "scan", "new", random hashes or single words without topic context), you MUST return exactly:
Unknown
- Do NOT guess a category based solely on the file extension if the filename itself lacks meaningful semantic context.
- Choose ONLY ONE folder if the filename clearly indicates the file's primary context or purpose.
- Your answer MUST be exactly one category name from the provided list, or "Unknown".
- Do NOT provide explanations, punctuation, markdown formatting, or extra words.
"""

# Content-based classification prompt
CONTENT_PROMPT_TEMPLATE = """
You are an intelligent file organization assistant.

Analyze the actual text and contents of this document and decide which folder is the BEST place to organize it.

Available folders:
{categories}

Rules:
- Choose ONLY ONE category from the provided list based on the document's true subject matter.
- Return ONLY the exact category name.
- If none of the categories is appropriate, return exactly:
Unknown
- Do NOT provide explanations, asterisks, or markdown formatting.
"""
