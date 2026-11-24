"""Tema visual e helpers de UI com rich."""
from __future__ import annotations
from rich.console import Console
from rich.theme import Theme
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import box

THEME = Theme({"brand":"bold #7CFFB2","accent":"#59C2FF","muted":"grey62",
    "ok":"bold #7CFFB2","warn":"bold #FFD166","err":"bold #FF6B6B","key":"bold #C792EA"})
console = Console(theme=THEME, highlight=False)

BANNER = r"""
 ____           _        _   _          _
|  _ \ ___   ___| | _____| |_| |    __ _| |__
| |_) / _ \ / __| |/ / _ \ __| |   / _` | '_ \
|  __/ (_) | (__|   <  __/ |_| |__| (_| | |_) |
|_|   \___/ \___|_|\_\___|\__|_____\__,_|_.__/
"""

def banner(version, db_count, ir_ok):
    console.print(Text(BANNER, style="brand"))
    sub = Text(); sub.append("canivete de laboratorio 100% Termux", style="accent")
    sub.append(f"   v{version}", style="muted"); console.print(sub)
    line = Text(); line.append("capturas: ", style="muted"); line.append(str(db_count), style="key")
    line.append("   IR nativo: ", style="muted")
    line.append("disponivel" if ir_ok else "ausente", style="ok" if ir_ok else "warn")
    console.print(line); console.print()

def rule(title): console.rule(f"[accent]{title}[/]", style="muted")
def ok(msg): console.print(f"[ok]✔[/] {msg}")
def warn(msg): console.print(f"[warn]![/] {msg}")
def err(msg): console.print(f"[err]✘[/] {msg}")
def info(msg): console.print(f"[accent]›[/] {msg}")

def menu_table(items):
    t = Table(box=box.ROUNDED, border_style="muted", show_header=True, header_style="accent", expand=False, pad_edge=False)
    t.add_column("#", style="key", justify="right", width=3)
    t.add_column("ferramenta", style="brand")
    t.add_column("descricao", style="muted")
    for k, name, desc in items: t.add_row(k, name, desc)
    return t

def panel(body, title, style="accent"):
    console.print(Panel(body, title=f"[{style}]{title}[/]", border_style=style, box=box.ROUNDED))
