# history.py

import json
from pathlib import Path
from datetime import datetime

HISTORY_FILE = Path("reports/history.json")

def load_history():
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_history(repo, pattern, extensions):
    history = load_history()
    history.append({
        "repo": repo,
        "pattern": pattern,
        "extensions": extensions,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    HISTORY_FILE.parent.mkdir(exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)
