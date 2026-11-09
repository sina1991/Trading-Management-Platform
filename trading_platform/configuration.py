"""TOML configuration loading and validation."""
import os
import sys
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


class ConfigurationError(ValueError):
    pass


class ConfigurationManager:
    def __init__(self, project_root: Path, config_path: str | None = None):
        self.project_root = Path(project_root).resolve()
        selected = config_path or os.getenv("TRADING_PLATFORM_CONFIG", "config/platform.example.toml")
        candidate = Path(selected)
        self.config_path = candidate if candidate.is_absolute() else self.project_root / candidate
        self._config: dict[str, Any] = {}

    def load(self) -> dict[str, Any]:
        if not self.config_path.is_file():
            raise ConfigurationError(f"Configuration file not found: {self.config_path}")
        try:
            with self.config_path.open("rb") as stream:
                self._config = tomllib.load(stream)
        except (tomllib.TOMLDecodeError, OSError) as exc:
            raise ConfigurationError(f"Unable to load configuration: {exc}") from exc
        override = os.getenv("TRADING_PLATFORM_LOG_LEVEL")
        if override:
            self._config.setdefault("logging", {})["level"] = override
        self.validate()
        return self.snapshot()

    def validate(self) -> tuple[str, ...]:
        required = ("platform.name", "platform.environment", "logging.level",
                    "logging.file", "storage.data_dir")
        missing = [key for key in required if not isinstance(self._get(key), str)
                   or not self._get(key).strip()]
        if missing:
            raise ConfigurationError("Missing or invalid keys: " + ", ".join(missing))
        if self._get("logging.level").upper() not in {
            "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
        }:
            raise ConfigurationError("logging.level must be DEBUG, INFO, WARNING, ERROR, or CRITICAL")
        return required

    def snapshot(self) -> dict[str, Any]:
        return {key: dict(value) if isinstance(value, dict) else value
                for key, value in self._config.items()}

    def _get(self, dotted: str) -> Any:
        value: Any = self._config
        for part in dotted.split("."):
            if not isinstance(value, dict):
                return None
            value = value.get(part)
        return value
