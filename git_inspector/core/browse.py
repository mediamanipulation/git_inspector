# core/browse.py
import os
from tkinter import filedialog, Tk

def ask_directory(initial_dir: str = None, title: str = "Select Folder") -> str:
    """
    Open a native directory picker and return the selected path, or empty string.
    """
    root = Tk()
    root.withdraw()
    path = filedialog.askdirectory(initialdir=initial_dir or os.getcwd(), title=title)
    root.destroy()
    return path