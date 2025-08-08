# core/searcher.py
import os
import re
from typing import List, Dict

def search_repo(
    base_dir: str,
    pattern: str,
    exts: List[str],
    use_regex: bool = True
) -> List[Dict]:
    """
    Recursively search files under base_dir for pattern in specified extensions.
    Returns list of dicts with keys: folder, file, line, match.
    """
    results = []
    matcher = re.compile(pattern) if use_regex else None
    for root, _, files in os.walk(base_dir):
        for fname in files:
            if any(fname.endswith(ext) for ext in exts):
                path = os.path.join(root, fname)
                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        for lineno, line in enumerate(f, start=1):
                            if (matcher.search(line) if matcher else pattern in line):
                                results.append({
                                    'folder': root,
                                    'file': fname,
                                    'line': lineno,
                                    'match': line.strip()
                                })
                except Exception:
                    continue
    return results