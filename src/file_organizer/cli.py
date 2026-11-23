"""Modern terminal user interface powered by Rich."""

import argparse
import os
import sys
from typing import List

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from .config import DEFAULT_CATEGORIES, SAFE_CONTENT_EXTENSIONS
from .core import OrganizerEngine
from .history import HistoryManager

console = Console()


def show_banner():
    """Display an eye-catching banner."""
    banner_text = (
        "[bold cyan]AI File Organizer[/bold cyan] [dim]|[/dim] "
        "[bold green]Powered by Google Gemini[/bold green]\n"
        "[dim]Context-aware, privacy-preserving file classification system[/dim]"
    )
    console.print(Panel(banner_text, border_style="cyan", expand=False))


def display_plan_table(planned_moves: List[dict], dry_run: bool = False):
    """Render a structured table of planned file movements."""
    title = "[bold yellow]Simulation (Dry Run) - No Files Moved[/bold yellow]" if dry_run else "[bold green]Proposed Organization Plan[/bold green]"
    table = Table(title=title, show_lines=True)
    table.add_column("File Name", style="cyan", no_wrap=False)
    table.add_column("Target Category", style="bold magenta")
    table.add_column("Analysis Mode", style="dim")

    for move in planned_moves:
        table.add_row(
            move["file_name"],
            move["category"],
            move.get("method", "Filename Scan"),
        )

    console.print(table)


def run_undo():
    """Roll back the last recorded organization session."""
    history = HistoryManager()
    with console.status("[bold yellow]Rolling back previous session...[/bold yellow]"):
        success, message, restored = history.undo_last_session()

    if not success:
        console.print(f"[bold red]Undo failed:[/bold red] {message}")
        return

    console.print(f"[bold green]Success:[/bold green] {message}")
    if restored:
        table = Table(title="[bold green]Restored Files[/bold green]")
        table.add_column("Source (Folder)", style="yellow")
        table.add_column("Restored To", style="green")
        for item in restored:
            table.add_row(item["source"], item["destination"])
        console.print(table)


def main():
    """Main CLI entrypoint."""
    load_dotenv()
    show_banner()

    parser = argparse.ArgumentParser(
        description="AI-Powered Context-Aware File Organizer using Google Gemini."
    )
    parser.add_argument(
        "--path",
        type=str,
        default=None,
        help="Target directory to organize (default: current directory or interactive prompt).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate file classification without moving files.",
    )
    parser.add_argument(
        "--undo",
        action="store_true",
        help="Undo the last organization session.",
    )
    parser.add_argument(
        "--categories",
        type=str,
        default=None,
        help="Comma-separated list of target categories (replaces defaults).",
    )
    parser.add_argument(
        "--add-categories",
        type=str,
        default=None,
        help="Comma-separated list of extra categories to add to the existing list.",
    )
    parser.add_argument(
        "--deep-scan",
        action="store_true",
        help="Automatically perform deep content analysis on unknown files.",
    )

    args = parser.parse_args()

    # Handle Undo request immediately
    if args.undo:
        run_undo()
        return

    # Check for Gemini API key
    if not os.getenv("GEMINI_API_KEY"):
        console.print(
            "[bold red]Warning:[/bold red] GEMINI_API_KEY not found in environment.\n"
            "Please create a [bold yellow].env[/bold yellow] file with: [green]GEMINI_API_KEY=your_key_here[/green]\n"
            "or set it in your system environment variables.",
            style="yellow",
        )

    # Determine Target Directory
    target_dir = args.path
    if not target_dir:
        if sys.stdin.isatty():
            input_dir = Prompt.ask(
                "[bold cyan]Enter directory to organize[/bold cyan]",
                default=".",
            )
            target_dir = input_dir.strip()
        else:
            target_dir = "."

    target_dir = os.path.abspath(os.path.expanduser(target_dir))
    if not os.path.isdir(target_dir):
        console.print(f"[bold red]Error:[/bold red] Path '{target_dir}' does not exist.")
        sys.exit(1)

    # Determine Categories
    cat_file = os.path.join(target_dir, "ai_categories.json")
    if args.categories:
        categories = [c.strip() for c in args.categories.split(",") if c.strip()]
    else:
        categories = []
        if os.path.exists(cat_file):
            import json
            try:
                with open(cat_file, "r") as f:
                    categories = json.load(f)
            except Exception:
                pass

        if not categories:
            categories = list(DEFAULT_CATEGORIES)

        if sys.stdin.isatty():
            console.print("\n[bold]Current Active Categories:[/bold]")
            for cat in categories:
                console.print(f"  • [magenta]{cat}[/magenta]")

            wants_custom = Confirm.ask(
                "\nDo you want to add or customize categories?", default=False
            )
            if wants_custom:
                console.print(
                    "[dim]Tip: Enter new categories separated by commas (e.g. 'Studies, Taxes'), "
                    "or type [bold yellow]'replace'[/bold yellow] to overwrite all categories.[/dim]"
                )
                action = Prompt.ask("[bold cyan]Enter categories to add[/bold cyan]").strip()

                if action.lower() == "replace":
                    custom_input = Prompt.ask("Enter your replacement categories separated by commas")
                    categories = [c.strip() for c in custom_input.split(",") if c.strip()]
                    console.print(f"[bold green]Categories set to:[/bold green] {', '.join(categories)}")
                elif action:
                    extras = [c.strip() for c in action.split(",") if c.strip()]
                    added = []
                    for ex in extras:
                        if ex not in categories:
                            categories.append(ex)
                            added.append(ex)
                    if added:
                        console.print(f"[bold green]Added:[/bold green] {', '.join(added)}")

    # If --add-categories flag was passed, append them
    if args.add_categories:
        extras = [c.strip() for c in args.add_categories.split(",") if c.strip()]
        for ex in extras:
            if ex not in categories:
                categories.append(ex)

    # Persist categories to ai_categories.json in target directory
    try:
        import json
        with open(cat_file, "w") as f:
            json.dump(categories, f, indent=2)
    except Exception:
        pass

    if not categories:
        console.print("[bold red]No categories specified. Exiting.[/bold red]")
        sys.exit(1)

    # Initialize Engine
    engine = OrganizerEngine()

    console.print(f"\n[bold blue]Scanning directory:[/bold blue] {target_dir}")
    with console.status("[bold green]Analyzing files with Google Gemini...[/bold green]"):
        planned_moves, unknown_files, api_failed_files = engine.plan_organization(target_dir, categories)

    if not planned_moves and not unknown_files and not api_failed_files:
        console.print("[bold green]No files found needing organization![/bold green]")
        return

    # 1. Distinguish and report API failures separately from Unknown classifications
    if api_failed_files:
        console.print(
            f"\n[bold red]API Request Errors ({len(api_failed_files)} file(s)):[/bold red]"
        )
        console.print(
            "[dim]The following requests could not reach Gemini (e.g. 503 Server Error / 429 Quota Exceeded / Network Timeout).\n"
            "Note: These are API communication failures, NOT Unknown classifications. These files will remain untouched:[/dim]"
        )
        for af in api_failed_files:
            console.print(f"  [red]✖[/red] {af['file_name']} [dim]— {af.get('error', 'API request failed')}[/dim]")

    # 2. Report Unknown files with clear Breakdown of Eligible vs Unsupported files
    if unknown_files:
        console.print(
            f"\n[bold yellow]Unclassified Files ({len(unknown_files)} file(s)):[/bold yellow]"
        )
        console.print(
            "[dim]Gemini analyzed these filenames but could not determine a specific category from the name alone:[/dim]"
        )
        for uf in unknown_files:
            console.print(f"  [yellow]?[/yellow] {uf}")

        # Partition into eligible for deep scan vs unsupported formats
        eligible_for_deep_scan = [
            f for f in unknown_files
            if os.path.splitext(f)[1].lower() in SAFE_CONTENT_EXTENSIONS
        ]
        unsupported_files = [
            f for f in unknown_files
            if os.path.splitext(f)[1].lower() not in SAFE_CONTENT_EXTENSIONS
        ]

        console.print("\n[bold cyan]Deep Scan Eligibility Breakdown:[/bold cyan]")
        console.print(f"  • [green]{len(eligible_for_deep_scan)} file(s) eligible for Deep Content Scan[/green]")
        console.print(f"  • [yellow]{len(unsupported_files)} file(s) have unsupported formats and will remain untouched[/yellow]")

        if unsupported_files:
            console.print("\n[dim]Unsupported format files (will remain in place):[/dim]")
            for unf in unsupported_files:
                ext_name = os.path.splitext(unf)[1].lower() or "no extension"
                console.print(f"  [dim]– {unf} ({ext_name})[/dim]")

        # 3. Privacy Disclosure and Explicit File List before Deep Scan consent
        if eligible_for_deep_scan:
            console.print(f"\n[bold green]Files Eligible for Deep Scan ({len(eligible_for_deep_scan)}):[/bold green]")
            for ef in eligible_for_deep_scan:
                console.print(f"  [green]•[/green] {ef}")

            disclosure_text = (
                "[bold yellow]⚠️  Privacy Disclosure:[/bold yellow]\n"
                "Deep Scan will upload the contents of eligible files to Google's Gemini service for analysis.\n"
                "[bold red]Do not enable this for sensitive or confidential files.[/bold red]\n\n"
                "[dim]Important: An extension being allowlisted does NOT automatically mean its contents are safe to upload.\n"
                "Ensure these files do not contain confidential, personal, or regulated data.\n"
                "Files uploaded are deleted immediately from Google's temporary storage after analysis.[/dim]"
            )
            console.print(Panel(disclosure_text, border_style="yellow", expand=False))

            perform_deep_scan = args.deep_scan or (
                Confirm.ask(
                    f"\nUpload and analyze the contents of these {len(eligible_for_deep_scan)} eligible file(s) with Gemini Deep Scan?",
                    default=False,
                )
                if sys.stdin.isatty()
                else False
            )

            if perform_deep_scan:
                with console.status("[bold cyan]Uploading and scanning contents with Gemini...[/bold cyan]"):
                    for ef in eligible_for_deep_scan:
                        full_path = os.path.join(target_dir, ef)
                        cat = engine.classify_by_content(full_path, categories)
                        if cat in categories:
                            planned_moves.append(
                                {
                                    "file_name": ef,
                                    "source": full_path,
                                    "destination": os.path.join(target_dir, cat, ef),
                                    "category": cat,
                                    "method": "Deep Content Scan",
                                }
                            )
                        elif cat == "API_ERROR":
                            console.print(f"  [red]✖[/red] Could not scan {ef} due to an API Error.")
                        else:
                            console.print(f"  [dim]? {ef} content remained unclassified.[/dim]")

    if not planned_moves:
        console.print("[yellow]No files were matched with target categories.[/yellow]")
        return

    # Display Plan
    display_plan_table(planned_moves, dry_run=args.dry_run)

    if args.dry_run:
        console.print(
            "\n[bold yellow]Dry-run finished. Remove --dry-run flag to execute moves.[/bold yellow]"
        )
        return

    if sys.stdin.isatty():
        proceed = Confirm.ask("\nProceed with moving these files?", default=True)
    else:
        proceed = True
    if not proceed:
        console.print("[yellow]Operation cancelled by user.[/yellow]")
        return

    with console.status("[bold green]Moving files...[/bold green]"):
        executed = engine.execute_plan(target_dir, planned_moves, dry_run=False)

    console.print(
        f"\n[bold green]Done![/bold green] Successfully organized [bold]{len(executed)}[/bold] file(s)."
    )
    console.print("[dim]Tip: You can undo this anytime using: [cyan]--undo[/cyan][/dim]")


if __name__ == "__main__":
    main()
