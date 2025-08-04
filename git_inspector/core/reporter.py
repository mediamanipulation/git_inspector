# reporter.py

import json

def save_json_report(matches, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(matches, f, indent=2)
    print(f"[✓] JSON report saved to {output_path}")

def save_txt_report(matches, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        for m in matches:
            f.write(f"{m['folder']}/{m['file']}:{m['line']} → {m['match']}\n")
    print(f"[✓] Text report saved to {output_path}")

def save_md_report(matches, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("| Folder | File | Line | Match |\n")
        f.write("|--------|------|------|-------|\n")
        for m in matches:
            safe_match = m['match'].replace("|", "\\|")
            f.write(f"| {m['folder']} | {m['file']} | {m['line']} | `{safe_match}` |\n")
    print(f"[✓] Markdown report saved to {output_path}")
