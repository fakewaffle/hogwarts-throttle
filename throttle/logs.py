import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"
MAX_BYTES = 1_000_000
BACKUPS = 5


def setup_logging(log_file: Path | None) -> None:
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(RotatingFileHandler(log_file, maxBytes=MAX_BYTES, backupCount=BACKUPS))
    logging.basicConfig(level=logging.INFO, format=FORMAT, handlers=handlers, force=True)
