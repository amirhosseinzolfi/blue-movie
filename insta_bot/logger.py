from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.text import Text # Added import

# Initialize Rich Console
console = Console()

def log_info(message, title=None):
    """Log info messages with blue color"""
    if title:
        console.print(Panel(message, title=f"[blue]ℹ️ {title}[/blue]", border_style="blue"))
    else:
        console.print(f"[blue]ℹ️[/blue] {message}")

def log_success(message, title=None):
    """Log success messages with green color"""
    if title:
        console.print(Panel(message, title=f"[green]✅ {title}[/green]", border_style="green"))
    else:
        console.print(f"[green]✅[/green] {message}")

def log_warning(message, title=None):
    """Log warning messages with yellow color"""
    if title:
        console.print(Panel(message, title=f"[yellow]⚠️ {title}[/yellow]", border_style="yellow"))
    else:
        console.print(f"[yellow]⚠️[/yellow] {message}")

def log_error(message, title=None):
    """Log error messages with red color"""
    if title:
        console.print(Panel(message, title=f"[red]❌ {title}[/red]", border_style="red"))
    else:
        console.print(f"[red]❌[/red] {message}")

def log_process(message, title=None):
    """Log process messages with cyan color"""
    if title:
        console.print(Panel(message, title=f"[cyan]🔄 {title}[/cyan]", border_style="cyan"))
    else:
        console.print(f"[cyan]🔄[/cyan] {message}")

def show_startup_banner():
    """Display startup banner"""
    banner = Text("INSTAGRAM BOT v3.0", style="bold magenta")
    banner.justify = "center"
    console.print(Panel(banner, box=box.DOUBLE, border_style="magenta", padding=(1, 2)))

def show_rules_table(rules):
    """Display loaded rules in a formatted table"""
    table = Table(title="[bold cyan]Loaded Rules Configuration[/bold cyan]", box=box.ROUNDED)
    table.add_column("Rule ID", style="cyan", no_wrap=True)
    table.add_column("Post ID", style="blue")
    table.add_column("Special Number", style="yellow")
    table.add_column("Message Preview", style="green")
    
    for rule in rules:
        message_preview = rule.get('message_to_send', '')[:30] + "..." if len(rule.get('message_to_send', '')) > 30 else rule.get('message_to_send', '')
        table.add_row(
            rule.get('rule_id', 'N/A'),
            rule.get('post_id', 'N/A'),
            rule.get('special_number', 'N/A'),
            message_preview
        )
    
    console.print(table)

def show_cycle_header(cycle_count):
    """Show formatted cycle header"""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    header_text = f"POLLING CYCLE #{cycle_count} - {current_time}"
    console.print(Panel(Text(header_text, style="bold white"), border_style="bright_blue", padding=(0, 1)))

def show_rule_processing(rule_id, post_id, special_number, comments_count):
    """Show rule processing information"""
    rule_info = f"[cyan]Rule ID:[/cyan] {rule_id} | [blue]Post:[/blue] {post_id} | [yellow]Code:[/yellow] '{special_number}' | [green]Comments:[/green] {comments_count}"
    console.print(f"  🔍 {rule_info}")

def show_match_found(comment_pk, username, special_number, rule_id):
    """Show when a matching comment is found"""
    match_text = f"[green]MATCH FOUND![/green] Comment {comment_pk} by [bold]@{username}[/bold] contains '{special_number}' (Rule: {rule_id})"
    console.print(f"    🎯 {match_text}")

def show_cycle_summary(total_comments_checked, total_matches_found, total_processed):
    """Show cycle summary in a table"""
    console.print()
    summary_table = Table(title="[bold cyan]Cycle Summary[/bold cyan]", box=box.SIMPLE)
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="white")
    
    summary_table.add_row("Comments Checked", str(total_comments_checked))
    summary_table.add_row("Matches Found", str(total_matches_found))
    summary_table.add_row("Total Processed", str(total_processed))
    
    console.print(summary_table)

def status_context(message, spinner="dots"):
    """Return a context manager for showing status with spinner"""
    return console.status(message, spinner=spinner)
