# core/history.py
import json
from pathlib import Path

HISTORY_FILE = Path("reports/history.json")

def load_history() -> list:
    """Load history entries from HISTORY_FILE, or return empty list."""
    if HISTORY_FILE.exists():
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    return []

def save_history(repo: str, pattern: str, extensions: list) -> None:
    """Append a search entry to history file, maintaining unique entries."""
    HISTORY_FILE.parent.mkdir(exist_ok=True)
    history = load_history()
    entry = {"repo": repo, "pattern": pattern, "extensions": extensions}
    # remove duplicates
    history = [h for h in history if not (h['repo']==repo and h['pattern']==pattern and h['extensions']==extensions)]
    history.insert(0, entry)
    HISTORY_FILE.write_text(json.dumps(history, indent=2), encoding="utf-8")