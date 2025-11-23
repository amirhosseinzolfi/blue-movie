"""
Rich-based logging configuration for Telegram Movie Bot
Provides colorful, structured logging with different levels and formats
"""

import logging
import sys
from pathlib import Path
from rich.console import Console
from rich.logging import RichHandler
from rich.traceback import install
from rich.theme import Theme
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from datetime import datetime

# Install rich traceback handler for better error formatting
install(show_locals=True)

# Custom theme for consistent colors
CUSTOM_THEME = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "red bold",
    "critical": "red on white bold",
    "success": "green bold",
    "debug": "dim blue",
    "telegram": "blue bold",
    "user": "magenta",
    "movie": "green",
    "channel": "yellow bold",
    "database": "cyan bold"
})

# Create console with custom theme
console = Console(theme=CUSTOM_THEME)

class TelegramBotFormatter(logging.Formatter):
    """Custom formatter for telegram bot specific logging"""
    
    def format(self, record):
        # Add custom fields for better context
        if hasattr(record, 'user_id'):
            record.user_context = f"[User:{record.user_id}]"
        else:
            record.user_context = ""
            
        if hasattr(record, 'movie_id'):
            record.movie_context = f"[Movie:{record.movie_id}]"
        else:
            record.movie_context = ""
            
        return super().format(record)

def setup_logging(log_level=logging.INFO, log_file="bot.log"):
    """
    Setup comprehensive logging with Rich formatting
    
    Args:
        log_level: Logging level (default: INFO)
        log_file: Log file path (default: bot.log)
    """
    
    # Change the logger configuration to include a timestamp and source details.
    LOG_FORMAT = "[%(asctime)s] %(levelname)-8s %(message)s (%(filename)s:%(lineno)d)"
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt="%y/%m/%d %H:%M:%S")
    
    # Create logs directory if it doesn't exist
    log_path = Path(log_file).parent
    log_path.mkdir(exist_ok=True)
    
    # Clear existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    # Rich console handler for colorful terminal output
    rich_handler = RichHandler(
        console=console,
        show_time=True,
        show_path=True,
        show_level=True,
        markup=True,
        rich_tracebacks=True,
        tracebacks_show_locals=True
    )
    rich_handler.setLevel(log_level)
    
    # File handler for persistent logging
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    
    # Custom formatter for file logging
    file_formatter = TelegramBotFormatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)-20s | %(user_context)s%(movie_context)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    
    # Configure root logger
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(rich_handler)
    root_logger.addHandler(file_handler)
    
    # Reduce noise from external libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.INFO)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    return root_logger

def get_logger(name: str):
    """Get a logger instance with the given name"""
    return logging.getLogger(name)

def log_user_action(logger, user_id: int, action: str, details: str = ""):
    """Log user actions with context"""
    extra = {'user_id': user_id}
    logger.info(f"[user]{action}[/user] {details}", extra=extra)

def log_movie_action(logger, movie_id: str, action: str, details: str = ""):
    """Log movie-related actions with context"""
    extra = {'movie_id': movie_id}
    logger.info(f"[movie]{action}[/movie] {details}", extra=extra)

def log_channel_check(logger, user_id: int, channel: str, status: str):
    """Log channel subscription checks"""
    extra = {'user_id': user_id}
    logger.info(f"[channel]Channel Check[/channel] {channel} - Status: {status}", extra=extra)

def log_database_operation(logger, operation: str, details: str = ""):
    """Log database operations"""
    logger.info(f"[database]{operation}[/database] {details}")

def log_server_operation(logger, operation: str, details: str = ""):
    """Log server-related operations"""
    logger.info(f"[telegram]Server[/telegram] {operation} - {details}")

def log_error_with_context(logger, error: Exception, context: str = "", user_id: int = None):
    """Log errors with rich context and formatting"""
    extra = {}
    if user_id:
        extra['user_id'] = user_id
    
    logger.error(f"[error]ERROR[/error] {context}: {str(error)}", extra=extra, exc_info=True)

def log_startup_banner(logger):
    """Display a beautiful startup banner"""
    console.print(Panel.fit(
        "[telegram]🎬 Telegram Movie Preview Bot[/telegram]\n"
        "[info]Starting up with Rich logging enabled[/info]\n"
        f"[success]Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/success]",
        title="[bold blue]Bot Initialization[/bold blue]",
        border_style="blue"
    ))
    logger.info("[success]Bot startup initiated[/success]")

def log_stats_table(logger, stats_data: dict):
    """Log statistics in a beautiful table format"""
    table = Table(title="Bot Statistics", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")
    
    for key, value in stats_data.items():
        table.add_row(key, str(value))
    
    console.print(table)
    logger.info(f"[success]Statistics updated[/success]: {stats_data}")

# Initialize logging when module is imported
logger = setup_logging()