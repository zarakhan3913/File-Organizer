"""Core AI classification and file organization engine."""

import os
import shutil
import time
from typing import Callable, Dict, List, Optional, Tuple

from google import genai

from .config import (
    CLASSIFICATION_PROMPT_TEMPLATE,
    CONTENT_PROMPT_TEMPLATE,
    DEFAULT_MODEL,
    FALLBACK_MODELS,
    IGNORED_DIRECTORIES,
    IGNORED_FILES,
    SAFE_CONTENT_EXTENSIONS,
)
from .history import HistoryManager


class OrganizerEngine:
    """Intelligent file organization engine utilizing Google Gemini models."""

    def __init__(
        self,
        client: Optional[genai.Client] = None,
        model: str = DEFAULT_MODEL,
        history_manager: Optional[HistoryManager] = None,
    ):
        """Initialize engine with an optional custom Gemini client for testing."""
        self.client = client
        self.model = model
        self.history_manager = history_manager or HistoryManager()
        self.last_error: Optional[str] = None

    def get_client(self) -> genai.Client:
        """Lazily initialize Gemini Client if not already provided."""
        if self.client is None:
            self.client = genai.Client()
        return self.client

    def is_eligible_file(self, file_path: str, categories: List[str]) -> bool:
        """Determine whether a file should be organized."""
        base_name = os.path.basename(file_path)

        if not os.path.isfile(file_path):
            return False

        if base_name in IGNORED_FILES or base_name.startswith("."):
            return False

        if base_name in categories or base_name in IGNORED_DIRECTORIES:
            return False

        return True

    def scan_directory(
        self, target_dir: str, categories: List[str]
    ) -> List[str]:
        """Scan target directory and return list of unorganized eligible files."""
        eligible_files = []
        try:
            entries = os.listdir(target_dir)
        except OSError:
            return []

        for entry in entries:
            full_path = os.path.join(target_dir, entry)
            if self.is_eligible_file(full_path, categories):
                eligible_files.append(entry)

        return sorted(eligible_files)

    def _clean_category_response(self, text: str, categories: List[str]) -> str:
        """Clean markdown, punctuation, and match case-insensitively against categories."""
        cleaned = text.strip().strip("*").strip("`").strip("\"'").strip().rstrip(".")
        for cat in categories:
            if cat.lower() == cleaned.lower():
                return cat
        return "Unknown"

    def classify_by_filename(
        self,
        file_name: str,
        ext: str,
        categories: List[str],
        max_retries: int = 2,
    ) -> str:
        """Classify a file based solely on its filename and extension.
        
        Returns:
            - Category name if successfully classified.
            - "Unknown" if Gemini evaluated the filename as ambiguous/generic.
            - "API_ERROR" if the API call failed (e.g. 503, 429, timeout).
        """
        client = self.get_client()
        prompt = CLASSIFICATION_PROMPT_TEMPLATE.format(
            file_name=file_name, ext=ext, categories=categories
        )

        models_to_try = [self.model] + [m for m in FALLBACK_MODELS if m != self.model]
        last_exception = None

        for model_name in models_to_try:
            for attempt in range(max_retries):
                try:
                    response = client.models.generate_content(
                        model=model_name, contents=prompt
                    )
                    return self._clean_category_response(response.text, categories)

                except Exception as e:
                    last_exception = e
                    err_msg = str(e)
                    if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                        self.last_error = (
                            "Daily API quota exceeded (429 RESOURCE_EXHAUSTED)."
                        )
                        break  # Try next fallback model
                    elif "503" in err_msg or "UNAVAILABLE" in err_msg:
                        self.last_error = (
                            "Gemini model service temporarily unavailable (503)."
                        )
                    else:
                        self.last_error = f"API error: {err_msg[:80]}"

                    if attempt < max_retries - 1:
                        time.sleep(1)
                    else:
                        break

        # If all attempts failed with exceptions, distinguish as API_ERROR
        if last_exception is not None:
            return "API_ERROR"

        return "Unknown"

    def classify_by_content(
        self, file_path: str, categories: List[str]
    ) -> str:
        """Deep scan: upload and analyze document content via Gemini File API.
        
        Returns:
            - Category name if successfully classified.
            - "UNSUPPORTED" if file extension is not in SAFE_CONTENT_EXTENSIONS.
            - "API_ERROR" if the API upload or call failed.
            - "Unknown" if the content could not be matched.
        """
        _, ext = os.path.splitext(file_path)
        if ext.lower() not in SAFE_CONTENT_EXTENSIONS:
            return "UNSUPPORTED"

        client = self.get_client()
        uploaded_file = None
        try:
            uploaded_file = client.files.upload(file=file_path)
            prompt = CONTENT_PROMPT_TEMPLATE.format(categories=categories)

            response = client.models.generate_content(
                model=self.model, contents=[prompt, uploaded_file]
            )
            return self._clean_category_response(response.text, categories)

        except Exception as e:
            err_msg = str(e)
            if "503" in err_msg or "UNAVAILABLE" in err_msg:
                self.last_error = "Gemini service temporarily unavailable (503)."
            elif "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                self.last_error = "Daily API quota exceeded (429)."
            else:
                self.last_error = f"Content scan error: {err_msg[:80]}"
            return "API_ERROR"

        finally:
            if uploaded_file is not None:
                try:
                    client.files.delete(name=uploaded_file.name)
                except Exception:
                    pass

    def plan_organization(
        self,
        target_dir: str,
        categories: List[str],
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> Tuple[List[Dict[str, str]], List[str], List[Dict[str, str]]]:
        """Analyze files in target_dir and generate proposed move plan.
        
        Returns:
            Tuple of (planned_moves, unknown_files, api_failed_files)
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        files = self.scan_directory(target_dir, categories)
        planned_moves = []
        unknown_files = []
        api_failed_files = []

        total = len(files)
        if total == 0:
            return [], [], []

        def _classify_single(file_name: str):
            _, ext = os.path.splitext(file_name)
            cat = self.classify_by_filename(file_name, ext.lower(), categories)
            return file_name, cat

        completed_count = 0
        with ThreadPoolExecutor(max_workers=min(5, total)) as executor:
            future_to_file = {
                executor.submit(_classify_single, fname): fname for fname in files
            }
            for future in as_completed(future_to_file):
                file_name, category = future.result()
                completed_count += 1
                if progress_callback:
                    progress_callback(file_name, completed_count, total)

                if category in categories:
                    src = os.path.join(target_dir, file_name)
                    dest = os.path.join(target_dir, category, file_name)
                    planned_moves.append(
                        {
                            "file_name": file_name,
                            "source": src,
                            "destination": dest,
                            "category": category,
                            "method": "Filename Analysis",
                        }
                    )
                elif category == "API_ERROR":
                    api_failed_files.append(
                        {
                            "file_name": file_name,
                            "error": self.last_error or "API request failed",
                        }
                    )
                else:
                    unknown_files.append(file_name)

        # Sort lists for consistent display
        planned_moves.sort(key=lambda x: x["file_name"])
        unknown_files.sort()
        api_failed_files.sort(key=lambda x: x["file_name"])

        self.api_failed_files = api_failed_files
        return planned_moves, unknown_files, api_failed_files

    def execute_plan(
        self,
        target_dir: str,
        moves: List[Dict[str, str]],
        dry_run: bool = False,
    ) -> List[Dict[str, str]]:
        """Execute the planned moves or simulate if dry_run=True."""
        executed = []

        if dry_run:
            return moves

        for item in moves:
            src = item["source"]
            dest = item["destination"]
            cat_dir = os.path.dirname(dest)

            if os.path.exists(dest):
                continue

            os.makedirs(cat_dir, exist_ok=True)
            shutil.move(src, dest)
            executed.append(item)

        if executed:
            self.history_manager.record_session(target_dir, executed)

        return executed
