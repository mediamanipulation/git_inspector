# html_hbs_search_gui.py

import os
import json
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText
from collections import Counter, defaultdict
import subprocess
import markdown2
import csv

TARGET_EXTENSIONS = [".html", ".hbs"]
CONFIG_FILE = "search_config.json"
SETTINGS_FILE = "gui_settings.json"


def load_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)["search_terms"]


def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f)


def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    return {}


def search_in_file(file_path, terms):
    results = []
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
            lines = file.readlines()
            for i, line in enumerate(lines, start=1):
                for term in terms:
                    pattern = term["pattern"]
                    is_regex = term.get("regex", False)
                    if re.search(pattern, line) if is_regex else pattern in line:
                        results.append({
                            "term": pattern,
                            "file": file_path,
                            "line": i,
                            "content": line.rstrip("\n")
                        })
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return results


def search_repo(base_dir, terms, extensions):
    matches = []
    for root, _, files in os.walk(base_dir):
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                full_path = os.path.join(root, file)
                matches.extend(search_in_file(full_path, terms))
    return matches


def git_blame(file, line):
    try:
        result = subprocess.run(
            ["git", "blame", "-L", f"{line},{line}", file],
            capture_output=True, text=True
        )
        return result.stdout.strip().split('(')[-1].split(')')[0].strip()
    except:
        return "Unknown"


def write_report(matches):
    term_counter = Counter()
    file_counter = defaultdict(Counter)
    dir_counter = Counter()

    for match in matches:
        term = match["term"]
        file = match["file"]
        directory = os.path.dirname(file)

        term_counter[term] += 1
        file_counter[file][term] += 1
        dir_counter[directory] += 1

    total_matches = sum(term_counter.values())

    # Markdown
    with open("search_report.md", "w", encoding="utf-8") as report:
        report.write("# 📊 Git Repo Search Report\n\n")
        report.write("## 🔢 Term Summary\n\n")
        report.write("| Search Term | Count | Percentage |\n")
        report.write("|-------------|-------|------------|\n")
        for term, count in term_counter.items():
            pct = (count / total_matches) * 100
            report.write(f"| `{term}` | {count} | {pct:.2f}% |\n")
        report.write(f"\n**Total Matches:** {total_matches}\n\n")
        report.write("---\n\n## 📂 Matches by File\n\n")
        for file, terms in file_counter.items():
            report.write(f"### 📄 `{file}`\n")
            for term, count in terms.items():
                report.write(f"- `{term}`: {count}\n")
            report.write("\n")
        report.write("---\n\n## 🌐 Directory Heatmap\n\n")
        report.write("| Directory | Match Count |\n")
        report.write("|-----------|--------------|\n")
        for dir_path, count in dir_counter.most_common():
            report.write(f"| `{dir_path}` | {count} |\n")
        report.write("\n---\n\n## 🧩 Match Details\n\n")
        for match in matches:
            author = git_blame(match['file'], match['line'])
            report.write(
                f"### Term: `{match['term']}`\n"
                f"- 📄 File: `{match['file']}`\n"
                f"- 🔢 Line: `{match['line']}`\n"
                f"- 👤 Author: {author}\n"
                f"- 📄 Snippet: `{match['content']}`\n\n"
            )
    # HTML
    html = markdown2.markdown_path("search_report.md")
    with open("search_report.html", "w", encoding="utf-8") as html_out:
        html_out.write(html)
    # CSV
    with open("search_summary.csv", "w", newline="", encoding="utf-8") as csv_out:
        writer = csv.writer(csv_out)
        writer.writerow(["Search Term", "Count", "Percentage"])
        for term, count in term_counter.items():
            pct = (count / total_matches) * 100
            writer.writerow([term, count, f"{pct:.2f}%"])


def run_search_gui():
    settings = load_settings()

    root = tk.Tk()
    root.title("Git Repo HTML/HBS Search Tool")
    root.geometry("800x600")

    notebook = ttk.Notebook(root)
    notebook.pack(expand=True, fill=tk.BOTH)

    # --- Search Tab ---
    tab_search = ttk.Frame(notebook)
    notebook.add(tab_search, text="Search")

    # Directory & File Type
    frame_top = ttk.Frame(tab_search, padding=10)
    frame_top.pack(fill=tk.X)
    ttk.Label(frame_top, text="Project Folder:").grid(row=0, column=0, sticky=tk.W)
    entry_path = ttk.Entry(frame_top, width=50)
    entry_path.grid(row=0, column=1, sticky=tk.W)
    ttk.Button(frame_top, text="Browse", command=lambda: browse_dir(entry_path)).grid(row=0, column=2, padx=5)
    
    ext_vars = {}
    ttk.Label(frame_top, text="File Types:").grid(row=1, column=0, sticky=tk.W)
    for idx, ext in enumerate(TARGET_EXTENSIONS, start=1):
        var = tk.BooleanVar(value=settings.get("exts", TARGET_EXTENSIONS).count(ext))
        ext_vars[ext] = var
        ttk.Checkbutton(frame_top, text=ext, variable=var).grid(row=1, column=idx)

    ttk.Button(frame_top, text="Save Settings", command=lambda: save_proj_settings(entry_path.get(), ext_vars)).grid(row=0, column=3, padx=5)
    ttk.Button(frame_top, text="Load Settings", command=lambda: load_proj_settings(entry_path, ext_vars)).grid(row=1, column=3, padx=5)

    ttk.Button(frame_top, text="Run Search", command=lambda: run_search(entry_path.get(), ext_vars, text_results, text_preview)).grid(row=2, column=1, pady=10)

    # Results pane
    paned = ttk.Panedwindow(tab_search, orient=tk.VERTICAL)
    paned.pack(expand=True, fill=tk.BOTH)
    # Match list
    frame_list = ttk.Frame(paned)
    text_results = ttk.Treeview(frame_list, columns=("Term", "File", "Line"), show="headings")
    text_results.heading("Term", text="Term")
    text_results.heading("File", text="File")
    text_results.heading("Line", text="Line")
    text_results.bind("<<TreeviewSelect>>", lambda e: preview_match(text_results, text_preview))
    text_results.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
    paned.add(frame_list, weight=1)
    
    # Preview pane
    frame_preview = ttk.Frame(paned)
    text_preview = ScrolledText(frame_preview)
    text_preview.pack(expand=True, fill=tk.BOTH)
    paned.add(frame_preview, weight=2)

    # --- Regex Tester Tab ---
    tab_regex = ttk.Frame(notebook)
    notebook.add(tab_regex, text="Regex Tester")
    
    ttk.Label(tab_regex, text="Pattern:").pack(anchor=tk.W, padx=10, pady=(10,0))
    entry_pattern = ttk.Entry(tab_regex, width=60)
    entry_pattern.pack(anchor=tk.W, padx=10)
    ttk.Label(tab_regex, text="Test Text:").pack(anchor=tk.W, padx=10, pady=(10,0))
    text_test = ScrolledText(tab_regex, height=10)
    text_test.pack(expand=True, fill=tk.BOTH, padx=10)
    btn_test = ttk.Button(tab_regex, text="Test Regex", command=lambda: run_regex_test(entry_pattern.get(), text_test, listbox_regex))
    btn_test.pack(pady=5)
    listbox_regex = tk.Listbox(tab_regex)
    listbox_regex.pack(expand=True, fill=tk.BOTH, padx=10, pady=(0,10))

    # --- Settings Tab ---
    tab_settings = ttk.Frame(notebook)
    notebook.add(tab_settings, text="Settings")
    ttk.Label(tab_settings, text=f"Config File: {CONFIG_FILE}").pack(anchor=tk.W, padx=10, pady=5)
    ttk.Entry(tab_settings, textvariable=tk.StringVar(value=settings.get("config", CONFIG_FILE)), state='readonly', width=60).pack(anchor=tk.W, padx=10)
    
    root.mainloop()

# Helper functions for GUI

def browse_dir(entry):
    directory = filedialog.askdirectory()
    if directory:
        entry.delete(0, tk.END)
        entry.insert(0, directory)


def save_proj_settings(path, ext_vars):
    settings = {"path": path, "exts": [ext for ext, var in ext_vars.items() if var.get()], "config": CONFIG_FILE}
    save_settings(settings)
    messagebox.showinfo("Settings", "Project settings saved.")


def load_proj_settings(entry, ext_vars):
    settings = load_settings()
    if settings.get("path"):
        entry.delete(0, tk.END)
        entry.insert(0, settings["path"])
    for ext, var in ext_vars.items():
        var.set(ext in settings.get("exts", []))
    messagebox.showinfo("Settings", "Project settings loaded.")


def run_search(path, ext_vars, results_view, preview_widget):
    if not os.path.isdir(path):
        messagebox.showerror("Invalid Path", "Please select a valid directory.")
        return
    exts = [ext for ext, var in ext_vars.items() if var.get()]
    if not exts:
        messagebox.showerror("No File Types", "Select at least one file type.")
        return
    terms = load_config()
    matches = search_repo(path, terms, exts)
    # Clear and populate TreeView
    for i in results_view.get_children():
        results_view.delete(i)
    for m in matches:
        results_view.insert("", tk.END, values=(m['term'], m['file'], m['line']))
    write_report(matches)
    messagebox.showinfo("Done", "Search complete. Reports generated.")


def preview_match(tree, preview_widget):
    selected = tree.selection()
    if not selected:
        return
    term, file, line = tree.item(selected[0], 'values')
    try:
        with open(file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.readlines()
            preview_widget.delete(1.0, tk.END)
            for idx, txt in enumerate(content, start=1):
                preview_widget.insert(tk.END, f"{idx:4d}: {txt}")
            # Highlight line
            preview_widget.tag_remove('highlight', '1.0', tk.END)
            start = f"{int(line)}.0"
            end = f"{int(line)}.end"
            preview_widget.tag_add('highlight', start, end)
            preview_widget.tag_config('highlight', background='yellow')
            preview_widget.see(start)
    except Exception as e:
        messagebox.showerror("Preview Error", str(e))


def run_regex_test(pattern, text_widget, listbox):
    text = text_widget.get(1.0, tk.END)
    listbox.delete(0, tk.END)
    try:
        for m in re.finditer(pattern, text, re.MULTILINE):
            snippet = text[m.start():m.end()]
            listbox.insert(tk.END, f"Match at {m.start()}-{m.end()}: {snippet}")
    except re.error as err:
        messagebox.showerror("Regex Error", str(err))

if __name__ == "__main__":
    run_search_gui()
