# __main__.py

from core.searcher import search_repo
from core.reporter import save_json_report, save_txt_report, save_md_report
from core.history import load_history, save_history
from core.browse import browse_folders
from pathlib import Path
from rich.console import Console

console = Console()

def run_cli():
    console.print("[bold green]🔍 Tinctkr Git Inspector[/bold green]")
    console.print("------------------------")

    history = load_history()

    if history:
        console.print("\n[cyan]📜 Search History:[/cyan]")
        for idx, item in enumerate(history, 1):
            console.print(f"{idx}. {item['pattern']} ({item['repo']}) [{item['timestamp']}]")
        use_prev = input("Use previous search? (y/n): ").strip().lower()
        if use_prev == "y":
            idx = int(input("Enter history number: ")) - 1
            if 0 <= idx < len(history):
                params = history[idx]
                repo = params['repo']
                pattern = params['pattern']
                extensions = params['extensions']
            else:
                console.print("[red]Invalid choice[/red]")
                return
        else:
            repo = input("📁 Path to repo: ").strip()
            repo = browse_folders(repo)
            pattern = input("🔎 Search pattern (regex): ").strip()
            ext_input = input("📄 File extensions (default: .html .hbs): ").strip()
            extensions = ext_input.split() if ext_input else [".html", ".hbs"]
    else:
        repo = input("📁 Path to repo: ").strip()
        repo = browse_folders(repo)
        pattern = input("🔎 Search pattern (regex): ").strip()
        ext_input = input("📄 File extensions (default: .html .hbs): ").strip()
        extensions = ext_input.split() if ext_input else [".html", ".hbs"]

    console.print("[yellow]⏳ Searching...[/yellow]")
    results = search_repo(repo, pattern, extensions)

    console.print(f"\n✅ Found [bold]{len(results)}[/bold] matches:\n")
    for m in results[:10]:
        highlighted = m["match"].replace(pattern, f"[bold red]{pattern}[/bold red]")
        console.print(f"[green]{m['folder']}/{m['file']}[/green]:{m['line']} → {highlighted}")

    outdir = Path("reports")
    outdir.mkdir(exist_ok=True)

    save_json_report(results, outdir / "search_report.json")
    save_txt_report(results, outdir / "search_report.txt")
    save_md_report(results, outdir / "search_report.md")

    save_history(repo, pattern, extensions)

if __name__ == "__main__":
    run_cli()
