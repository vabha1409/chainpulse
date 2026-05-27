"""
utils/display.py — Terminal output helpers with rich formatting
"""

import os
import sys
from datetime import datetime

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.text import Text
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

console = Console() if RICH_AVAILABLE else None

CHAINS = {
    "eth": ("Ξ", "#627EEA"),
    "btc": ("₿", "#F7931A"),
    "sol": ("◎", "#9945FF"),
    "bnb": ("⬡", "#F0B90B"),
    "arb": ("△", "#28A0F0"),
}

def banner():
    if RICH_AVAILABLE:
        text = Text()
        text.append("  ██████╗██╗  ██╗ █████╗ ██╗███╗   ██╗\n", style="bold cyan")
        text.append(" ██╔════╝██║  ██║██╔══██╗██║████╗  ██║\n", style="bold cyan")
        text.append(" ██║     ███████║███████║██║██╔██╗ ██║\n", style="bold blue")
        text.append(" ██║     ██╔══██║██╔══██║██║██║╚██╗██║\n", style="bold blue")
        text.append(" ╚██████╗██║  ██║██║  ██║██║██║ ╚████║\n", style="bold magenta")
        text.append(" ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝\n", style="bold magenta")
        text.append(" PULSE  —  Multi-Chain On-Chain Analysis\n", style="dim")
        text.append(f" v1.0.0  |  {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC\n", style="dim")
        console.print(Panel(text, border_style="cyan", padding=(0, 2)))
    else:
        print("=" * 50)
        print("  CHAINPULSE — Multi-Chain On-Chain Analysis")
        print("=" * 50)

def success(msg):
    if RICH_AVAILABLE:
        console.print(f"[bold green]✓[/] {msg}")
    else:
        print(f"[OK] {msg}")

def error(msg):
    if RICH_AVAILABLE:
        console.print(f"[bold red]✗[/] {msg}")
    else:
        print(f"[ERROR] {msg}", file=sys.stderr)

def info(msg):
    if RICH_AVAILABLE:
        console.print(f"[bold cyan]ℹ[/] {msg}")
    else:
        print(f"[INFO] {msg}")

def warn(msg):
    if RICH_AVAILABLE:
        console.print(f"[bold yellow]⚠[/] {msg}")
    else:
        print(f"[WARN] {msg}")

def section(title):
    if RICH_AVAILABLE:
        console.rule(f"[bold cyan]{title}[/]")
    else:
        print(f"\n{'─'*40}\n  {title}\n{'─'*40}")

def metric_card(label, value, delta=None, unit=""):
    """Print a KPI metric card."""
    if RICH_AVAILABLE:
        delta_str = ""
        if delta is not None:
            color = "green" if delta >= 0 else "red"
            arrow = "▲" if delta >= 0 else "▼"
            delta_str = f"  [{color}]{arrow} {abs(delta):.1f}%[/]"
        console.print(f"  [dim]{label}[/]  [bold white]{value}{unit}[/]{delta_str}")
    else:
        delta_str = f"  ({'+' if delta >= 0 else ''}{delta:.1f}%)" if delta else ""
        print(f"  {label}: {value}{unit}{delta_str}")

def make_table(title, columns, rows, column_styles=None):
    """Build and print a rich table."""
    if RICH_AVAILABLE:
        table = Table(
            title=title,
            box=box.SIMPLE_HEAD,
            title_style="bold cyan",
            header_style="bold white",
            border_style="dim",
            show_lines=False,
        )
        styles = column_styles or {}
        for col in columns:
            table.add_column(col, style=styles.get(col, "white"), no_wrap=True)
        for row in rows:
            table.add_row(*[str(x) for x in row])
        console.print(table)
    else:
        print(f"\n{title}")
        print("  ".join(columns))
        for row in rows:
            print("  ".join(str(x) for x in row))

def progress_context(description="Fetching data..."):
    if RICH_AVAILABLE:
        return Progress(
            SpinnerColumn(),
            TextColumn("[cyan]{task.description}"),
            BarColumn(),
            console=console
        )
    else:
        class FakeProgress:
            def __enter__(self): print(description); return self
            def __exit__(self, *a): pass
            def add_task(self, desc, total=None): return 0
            def advance(self, task, n=1): pass
        return FakeProgress()

def chain_badge(chain):
    symbol, _ = CHAINS.get(chain.lower(), ("?", "#888888"))
    return f"{symbol} {chain.upper()}"

def format_usd(value):
    if value >= 1e9:
        return f"${value/1e9:.2f}B"
    elif value >= 1e6:
        return f"${value/1e6:.2f}M"
    elif value >= 1e3:
        return f"${value/1e3:.2f}K"
    return f"${value:.2f}"

def format_pct(value, color=True):
    sign = "+" if value >= 0 else ""
    s = f"{sign}{value:.2f}%"
    if RICH_AVAILABLE and color:
        c = "green" if value >= 0 else "red"
        return f"[{c}]{s}[/]"
    return s
