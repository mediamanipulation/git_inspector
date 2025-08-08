# gui.py
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

from core.searcher import search_repo
from core.reporter import save_json_report, save_txt_report, save_md_report
from core.history import load_history, save_history

HISTORY_FILE = Path("reports/history.json")

class InspectorGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Git Inspector GUI")
        self.geometry("800x500")
        self._create_widgets()
        self._load_history()

    def _create_widgets(self):
        container = ttk.Frame(self, padding=10)
        container.pack(fill=tk.X)

        # History dropdown
        ttk.Label(container, text="Previous Searches:").grid(row=0, column=0, sticky=tk.W)
        self.history_var = tk.StringVar()
        self.history_cb = ttk.Combobox(
            container, textvariable=self.history_var, state="readonly", width=50
        )
        self.history_cb.grid(row=0, column=1, columnspan=2, sticky=tk.W)
        self.history_cb.bind("<<ComboboxSelected>>", self._on_history)

        # Repo path
        ttk.Label(container, text="Repo Path:").grid(row=1, column=0, sticky=tk.W)
        self.repo_entry = ttk.Entry(container, width=50)
        self.repo_entry.grid(row=1, column=1, sticky=tk.W)
        ttk.Button(
            container, text="Browse…", command=self._browse_repo
        ).grid(row=1, column=2, padx=5)

        # Search pattern
        ttk.Label(container, text="Pattern (regex):").grid(row=2, column=0, sticky=tk.W)
        self.pattern_entry = ttk.Entry(container, width=50)
        self.pattern_entry.grid(row=2, column=1, columnspan=2, sticky=tk.W)

        # Extensions
        ttk.Label(container, text="Extensions:").grid(row=3, column=0, sticky=tk.W)
        self.ext_entry = ttk.Entry(container, width=50)
        self.ext_entry.insert(0, ".html .hbs")
        self.ext_entry.grid(row=3, column=1, columnspan=2, sticky=tk.W)

        # Run button
        ttk.Button(
            container, text="Run Search", command=self._run_search
        ).grid(row=4, column=1, pady=10)

        # Results treeview
        columns = ("folder", "file", "line", "match")
        self.tree = ttk.Treeview(
            self, columns=columns, show="headings"
        )
        for col in columns:
            width = 300 if col == "match" else 150
            self.tree.heading(col, text=col.capitalize())
            self.tree.column(col, width=width, anchor=tk.W)
        self.tree.pack(expand=True, fill=tk.BOTH, padx=10, pady=(0,10))

    def _load_history(self):
        self.history = load_history()
        options = ["<New Search>"] + [
            f"{h['pattern']} @ {Path(h['repo']).name}" for h in self.history
        ]
        self.history_cb["values"] = options
        self.history_cb.current(0)

    def _on_history(self, event):
        idx = self.history_cb.current() - 1
        if idx >= 0:
            entry = self.history[idx]
            self.repo_entry.delete(0, tk.END)
            self.repo_entry.insert(0, entry["repo"])
            self.pattern_entry.delete(0, tk.END)
            self.pattern_entry.insert(0, entry["pattern"])
            self.ext_entry.delete(0, tk.END)
            exts = " ".join(entry.get("extensions", []))
            self.ext_entry.insert(0, exts)

    def _browse_repo(self):
        start = self.repo_entry.get() or "."
        directory = filedialog.askdirectory(
            initialdir=start, title="Select Repository"
        )
        if directory:
            self.repo_entry.delete(0, tk.END)
            self.repo_entry.insert(0, directory)

    def _run_search(self):
        repo = self.repo_entry.get().strip()
        pattern = self.pattern_entry.get().strip()
        exts = self.ext_entry.get().split()
        if not repo or not pattern:
            messagebox.showerror(
                "Error", "Repo path and pattern are required."
            )
            return

        # Search
        results = search_repo(repo, pattern, exts)

        # Clear and populate
        for item in self.tree.get_children():
            self.tree.delete(item)
        for m in results:
            self.tree.insert(
                "", tk.END,
                values=(m.get("folder",""), m.get("file",""), m.get("line",""), m.get("match","")[:80])
            )

        # Ensure reports dir
        outdir = Path("reports")
        outdir.mkdir(exist_ok=True)

        # Save reports
        save_json_report(results, outdir/"search_report.json")
        save_txt_report(results, outdir/"search_report.txt")
        save_md_report(results, outdir/"search_report.md")

        # History
        save_history(repo, pattern, exts)
        self._load_history()

        messagebox.showinfo(
            "Done", f"{len(results)} matches. Reports in {outdir.absolute()}"
        )

if __name__ == "__main__":
    app = InspectorGUI()
    app.mainloop()
