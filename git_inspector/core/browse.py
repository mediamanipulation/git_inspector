# browse.py

from pathlib import Path
from rich.console import Console

console = Console()

def browse_folders(start_path):
    path = Path(start_path).resolve()
    while True:
        subfolders = [p for p in path.iterdir() if p.is_dir()]
        console.print(f"\n[cyan]Browsing: {path}[/cyan]")
        for idx, folder in enumerate(subfolders, 1):
            console.print(f"{idx}. {folder.name}")
        console.print("0. Use this folder")
        
        choice = input("Select folder (0 to use current): ").strip()
        if choice == "0":
            return str(path)
        try:
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(subfolders):
                path = subfolders[choice_idx]
            else:
                console.print("[red]Invalid choice[/red]")
        except ValueError:
            console.print("[red]Enter a number[/red]")
