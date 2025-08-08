# core/reporter.py

import json
import os
from collections import Counter

def save_json_report(matches, output_path):
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(matches, f, indent=2)

def save_txt_report(matches, output_path):
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        for m in matches:
            f.write(f"{m['folder']}/{m['file']}:{m['line']} → {m['match']}\n")

def save_md_report(matches, output_path):
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('| Folder | File | Line | Match |\n')
        f.write('|--------|------|------|-------|\n')
        for m in matches:
            safe = m['match'].replace('|','\\|')
            f.write(f"| {m['folder']} | {m['file']} | {m['line']} | `{safe}` |\n")

def compute_summary(matches):
    """
    Returns a dict with:
      - total           : total number of matches
      - per_file        : { filename: count, … }
      - per_directory   : { immediate_folder: count, … }
      - full_directory  : { nested/path: cumulative count, … }
    """
    total = len(matches)

    # per-file counts
    file_counts = Counter(m['file'] for m in matches)

    # immediate parent directory counts
    dir_counts  = Counter(m['folder'] or '.' for m in matches)

    # full-path roll-up counts
    full_counts = Counter()
    for m in matches:
        d = m['folder'] or '.'
        parts = d.split(os.sep)
        for i in range(1, len(parts)+1):
            p = os.sep.join(parts[:i])
            full_counts[p] += 1

    return {
        'total': total,
        'per_file':       dict(file_counts),
        'per_directory':  dict(dir_counts),
        'full_directory': dict(full_counts),
    }
