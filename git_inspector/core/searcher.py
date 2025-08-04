# searcher.py

import re
from pathlib import Path

def search_repo(repo_path, pattern, extensions):
    repo_path = Path(repo_path).resolve()
    regex = re.compile(pattern)
    matches = []

    for filepath in repo_path.rglob("*"):
        if not filepath.is_file():
            continue
        if not any(filepath.name.endswith(ext) for ext in extensions):
            continue

        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                for i, line in enumerate(f, 1):
                    if regex.search(line):
                        relative_path = filepath.relative_to(repo_path)
                        matches.append({
                            "folder": str(relative_path.parent),
                            "file": filepath.name,
                            "line": i,
                            "match": line.strip()
                        })
        except Exception as e:
            print(f"⚠️ Error reading {filepath}: {e}")
    return matches
