"""File-based logging foundation."""
import logging
from pathlib import Path


def configure_logging(project_root: Path, config: dict) -> logging.Logger:
    settings = config.get("logging", {})
    level_name = str(settings.get("level", "INFO")).upper()
    level = getattr(logging, level_name, logging.INFO)
    target = Path(str(settings.get("file", "logs/platform.log")))
    if not target.is_absolute():
        target = Path(project_root) / target
    target.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("trading_platform")
    logger.setLevel(level)
    logger.propagate = False
    if not logger.handlers:
        handler = logging.FileHandler(target, encoding="utf-8")
        handler.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s: %(message)s"
        ))
        logger.addHandler(handler)
    return logger
