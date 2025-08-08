# gui.py
import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path

from core.browse    import ask_directory
from core.history   import load_history, save_history
from core.searcher  import search_repo
from core.reporter  import (
    save_json_report,
    save_txt_report,
    save_md_report,
    compute_summary
)

class InspectorGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Git Inspector GUI")
        self.geometry("900x600")
        self.results = []
        self.current_pattern = ""
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

        # Run + Summary buttons
        ttk.Button(
            container, text="Run Search", command=self._run_search
        ).grid(row=4, column=1, pady=10)
        ttk.Button(
            container, text="Show Summary", command=self._show_summary
        ).grid(row=4, column=2, pady=10)

        # Results treeview
        columns = ("folder", "file", "line", "match")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        for col in columns:
            width = 350 if col == "match" else 150
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

    def _on_history(self, _):
        idx = self.history_cb.current() - 1
        if idx >= 0:
            entry = self.history[idx]
            self.repo_entry.delete(0, tk.END);     self.repo_entry.insert(0, entry["repo"])
            self.pattern_entry.delete(0, tk.END);  self.pattern_entry.insert(0, entry["pattern"])
            self.ext_entry.delete(0, tk.END);      self.ext_entry.insert(0, " ".join(entry["extensions"]))

    def _browse_repo(self):
        start = self.repo_entry.get() or "."
        directory = ask_directory(initial_dir=start, title="Select Repository")
        if directory:
            self.repo_entry.delete(0, tk.END)
            self.repo_entry.insert(0, directory)

    def _run_search(self):
        repo    = self.repo_entry.get().strip()
        pattern = self.pattern_entry.get().strip()
        exts    = self.ext_entry.get().split()
        if not repo or not pattern:
            messagebox.showerror("Error", "Repo path and pattern are required.")
            return

        # Search
        self.results = search_repo(repo, pattern, exts)
        self.current_pattern = pattern

        # Populate results
        for item in self.tree.get_children():
            self.tree.delete(item)
        for m in self.results:
            self.tree.insert(
                "", tk.END,
                values=(m["folder"], m["file"], m["line"], m["match"][:80])
            )

        # Save reports + summary
        outdir = Path("reports"); outdir.mkdir(exist_ok=True)
        save_json_report(self.results,    outdir/"search_report.json")
        save_txt_report(self.results,     outdir/"search_report.txt")
        save_md_report(self.results,      outdir/"search_report.md")
        summary = compute_summary(self.results)
        (outdir/"search_summary.json").write_text(json.dumps(summary, indent=2))
        save_history(repo, pattern, exts)

        messagebox.showinfo("Done", f"{len(self.results)} matches. Reports in {outdir.absolute()}")

    def _show_summary(self):
        if not self.results:
            messagebox.showwarning("No Data", "Run a search first.")
            return
        summary = compute_summary(self.results)
        win = tk.Toplevel(self); win.title("Search Summary"); win.geometry("600x500")
        text = tk.Text(win, wrap="none", padx=10, pady=10); text.pack(expand=True, fill=tk.BOTH)

        total = summary["total"]
        text.insert("end", f"Pattern: {self.current_pattern}\nTotal Matches: {total}\n\n")

        # Per-file
        text.insert("end", "📂 Matches by File:\n")
        text.insert("end", "File".ljust(50) + "Count   %\n")
        text.insert("end", "-"*70 + "\n")
        for f, cnt in summary["per_file"].items():
            pct = cnt/total*100
            text.insert("end", f"{f.ljust(50)} {cnt:3d}  {pct:5.1f}%\n")

        # Per-dir
        text.insert("end", "\n🌐 Matches by Directory:\n")
        text.insert("end", "Dir".ljust(50) + "Count   %\n")
        text.insert("end", "-"*70 + "\n")
        for d, cnt in summary["per_directory"].items():
            pct = cnt/total*100
            text.insert("end", f"{d.ljust(50)} {cnt:3d}  {pct:5.1f}%\n")

        # Full-path
        text.insert("end", "\n🌳 Full-path Roll-up:\n")
        text.insert("end", "Path".ljust(50) + "Count   %\n")
        text.insert("end", "-"*70 + "\n")
        for d, cnt in summary["full_directory"].items():
            pct = cnt/total*100
            text.insert("end", f"{d.ljust(50)} {cnt:3d}  {pct:5.1f}%\n")

        text.config(state="disabled")

if __name__ == "__main__":
    app = InspectorGUI()
    app.mainloop()
