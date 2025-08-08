# gui.py
import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path

from core.browse import ask_directory
from core.history import load_history, save_history
from core.searcher import search_repo
from core.reporter import (
    save_json_report, save_txt_report, save_md_report, compute_summary
)

class InspectorGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Git Inspector GUI")
        self.geometry("900x600")
        self.results = []
        self._build()
        self._load_history()

    def _build(self):
        frm = ttk.Frame(self, padding=10)
        frm.pack(fill=tk.X)
        # History
        ttk.Label(frm, text="History:").grid(row=0, column=0)
        self.history_cb = ttk.Combobox(frm, state='readonly', width=50)
        self.history_cb.grid(row=0, column=1, columnspan=2)
        self.history_cb.bind('<<ComboboxSelected>>', self._on_history)
        # Repo
        ttk.Label(frm, text="Repo:").grid(row=1, column=0)
        self.repo_e = ttk.Entry(frm, width=50)
        self.repo_e.grid(row=1, column=1)
        ttk.Button(frm, text="Browse", command=lambda: self._set(self.repo_e, ask_directory())).grid(row=1, column=2)
        # Pattern
        ttk.Label(frm, text="Pattern:").grid(row=2, column=0)
        self.pat_e = ttk.Entry(frm, width=50)
        self.pat_e.grid(row=2, column=1, columnspan=2)
        # Exts
        ttk.Label(frm, text="Exts:").grid(row=3, column=0)
        self.ext_e = ttk.Entry(frm, width=50)
        self.ext_e.insert(0, ".html .hbs")
        self.ext_e.grid(row=3, column=1, columnspan=2)
        # Buttons
        ttk.Button(frm, text="Run", command=self._run).grid(row=4, column=1)
        ttk.Button(frm, text="Summary", command=self._summary).grid(row=4, column=2)
        # Tree
        cols = ('folder','file','line','match')
        self.tree = ttk.Treeview(self, columns=cols, show='headings')
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=200 if c!='match' else 400)
        self.tree.pack(expand=True, fill=tk.BOTH)

    def _set(self, entry, val):
        entry.delete(0, tk.END); entry.insert(0, val)

    def _load_history(self):
        hist = load_history()
        opts = ['<New>'] + [f"{h['pattern']}@{Path(h['repo']).name}" for h in hist]
        self.history_cb['values'] = opts; self.history_cb.current(0)

    def _on_history(self, e):
        idx = self.history_cb.current()-1
        if idx>=0:
            h = load_history()[idx]
            self._set(self.repo_e, h['repo'])
            self._set(self.pat_e, h['pattern'])
            self._set(self.ext_e, ' '.join(h['extensions']))

    def _run(self):
        repo, pat, exts = self.repo_e.get(), self.pat_e.get(), self.ext_e.get().split()
        self.results = search_repo(repo, pat, exts)
        # populate
        for i in self.tree.get_children(): self.tree.delete(i)
        for m in self.results:
            self.tree.insert('', tk.END, values=(m['folder'],m['file'],m['line'],m['match'][:80]))
        # reports
        out = Path('reports'); out.mkdir(exist_ok=True)
        save_json_report(self.results, out/'search_report.json')
        save_txt_report(self.results, out/'search_report.txt')
        save_md_report(self.results, out/'search_report.md')
        # summary
        summary = compute_summary(self.results)
        (out/'search_summary.json').write_text(json.dumps(summary, indent=2))
        save_history(repo, pat, exts)

    def _summary(self):
        if not self.results: return
        sumd = compute_summary(self.results)
        top = tk.Toplevel(self); top.title('Summary'); txt = tk.Text(top); txt.pack(expand=True, fill=tk.BOTH)
        txt.insert('end', json.dumps(sumd, indent=2))
        txt.config(state='disabled')

if __name__=='__main__':
    InspectorGUI().mainloop()