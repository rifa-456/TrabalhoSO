import sys
from pathlib import Path
from datetime import datetime
from loguru import logger

def setup_loggers(pid: int):
    """
    Configures loguru to log to the console and two separate files.

    This setup creates a unique directory for each tracing session based on
    the process ID and the start time. Inside this directory, it creates:
    1. A structured JSON log for machine analysis ('structured.log').
    2. A human-readable plain text log ('human.log').
    3. It also prints colorized, user-friendly output to the console.

    Args:
        pid (int): The process ID being traced, used for the log directory name.
    
    Returns:
        Path: The path to the newly created log directory.
    """
    logger.remove()
    project_root = Path(__file__).parent.parent.parent
    log_dir_name = f"trace-{pid}-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    log_path = project_root / "logs" / log_dir_name
    log_path.mkdir(parents=True, exist_ok=True)
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        colorize=True
    )
    human_log_file = log_path / "human.log"
    logger.add(
        human_log_file,
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        colorize=False
    )

    structured_log_file = log_path / "structured.log"
    logger.add(
        structured_log_file,
        level="INFO",
        serialize=True,
        colorize=False
    )
    return log_path