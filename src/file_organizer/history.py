"""Transaction history and undo system for safe file operations."""

import json
import os
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class HistoryManager:
    """Manages transactional logs of file movements to enable reliable rollbacks."""

    def __init__(self, history_file: str = "organization_history.json"):
        self.history_file = history_file

    def record_session(
        self, target_dir: str, actions: List[Dict[str, str]]
    ) -> Optional[str]:
        """Record an organization session.
        
        Args:
            target_dir: Absolute path of the organized directory.
            actions: List of dicts with keys 'source', 'destination', 'category'.
            
        Returns:
            session_id if recorded, None if actions list was empty.
        """
        if not actions:
            return None

        history = self._load_history()
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        session_entry = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "target_dir": os.path.abspath(target_dir),
            "moves_count": len(actions),
            "actions": actions,
        }

        history.append(session_entry)
        self._save_history(history)
        return session_id

    def undo_last_session(self) -> Tuple[bool, str, List[Dict[str, str]]]:
        """Roll back the most recent organization session.
        
        Returns:
            Tuple of (success_status, message, details_list)
        """
        history = self._load_history()
        if not history:
            return False, "No previous organization history found.", []

        last_session = history.pop()
        actions = last_session.get("actions", [])
        restored = []
        errors = []

        for act in reversed(actions):
            dest = act.get("destination")
            src = act.get("source")

            if not dest or not src:
                continue

            if not os.path.exists(dest):
                errors.append(f"File missing at destination: {dest}")
                continue

            if os.path.exists(src):
                errors.append(f"Target already occupied: {src}")
                continue

            try:
                # Ensure parent directory for src exists
                os.makedirs(os.path.dirname(src), exist_ok=True)
                shutil.move(dest, src)
                restored.append({"source": dest, "destination": src})

                # If the category folder is now empty, remove it
                dest_dir = os.path.dirname(dest)
                if os.path.exists(dest_dir) and not os.listdir(dest_dir):
                    try:
                        os.rmdir(dest_dir)
                    except OSError:
                        pass
            except Exception as e:
                errors.append(f"Failed to restore {dest} -> {src}: {e}")

        # Update history file without the reverted session
        self._save_history(history)

        msg = f"Restored {len(restored)} files."
        if errors:
            msg += f" Encountered {len(errors)} issues."

        return True, msg, restored

    def _load_history(self) -> List[Dict]:
        if not os.path.exists(self.history_file):
            return []
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return []

    def _save_history(self, history: List[Dict]) -> None:
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
