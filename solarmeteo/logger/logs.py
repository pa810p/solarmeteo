import logging
from logging.handlers import RotatingFileHandler
import os

class ProjectOnlyFilter(logging.Filter):
    def __init__(self, project_prefix):
        super().__init__()
        self.project_prefix = project_prefix

    def filter(self, record):
        return record.name.startswith(self.project_prefix)

def setup_logging(level=logging.INFO, log_file="solarmeteo.log", project_prefix="solarmeteo"):
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, log_file)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.WARNING)  # restrict default to WARNING

    # Clear existing handlers
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # File handler with rotation
    file_handler = RotatingFileHandler(log_path, maxBytes=5 * 1024 * 1024, backupCount=3)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(ProjectOnlyFilter(project_prefix))
    root_logger.addHandler(file_handler)

    # Console handler (optional)
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    console.addFilter(ProjectOnlyFilter(project_prefix))
    root_logger.addHandler(console)

    # Explicitly enable DEBUG for your own project
    logging.getLogger(project_prefix).setLevel(level)


def get_log_level(level_str: str) -> int:
    try:
        return getattr(logging, level_str.upper())
    except AttributeError:
        raise ValueError(f"Invalid log level: {level_str}")