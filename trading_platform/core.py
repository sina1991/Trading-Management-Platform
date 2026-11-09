"""Core contracts: command registry, readiness checker and system inspection."""
from dataclasses import dataclass, field
from enum import Enum
from importlib.util import find_spec
from pathlib import Path
from typing import Any, Callable
import platform
import sys
import sqlite3


class ReadinessStatus(str, Enum):
    READY = "READY"
    PARTIAL = "PARTIAL"
    NOT_IMPLEMENTED = "NOT IMPLEMENTED"
    MISSING_FILES = "MISSING FILES"
    MISSING_DEPENDENCIES = "MISSING DEPENDENCIES"
    CONFIGURATION_ERROR = "CONFIGURATION ERROR"
    DEPENDENCY_ERROR = "DEPENDENCY ERROR"
    STORAGE_ERROR = "STORAGE ERROR"


@dataclass(frozen=True)
class CommandSpec:
    command_id: str
    title: str
    description: str
    menu_id: str
    implementation: str = "planned"
    handler_key: str | None = None
    required_files: tuple[str, ...] = field(default_factory=tuple)
    dependencies: tuple[str, ...] = field(default_factory=tuple)
    required_config: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ReadinessReport:
    command_id: str
    status: ReadinessStatus
    checks: tuple[str, ...] = ()
    missing: tuple[str, ...] = ()
    message: str = ""

    @property
    def is_ready(self) -> bool:
        return self.status is ReadinessStatus.READY


class CommandRegistry:
    def __init__(self, commands: list[CommandSpec] | tuple[CommandSpec, ...]):
        self._commands: dict[str, CommandSpec] = {}
        for command in commands:
            if command.command_id in self._commands:
                raise ValueError(f"Duplicate command id: {command.command_id}")
            self._commands[command.command_id] = command

    def get(self, command_id: str) -> CommandSpec:
        if command_id not in self._commands:
            raise KeyError(f"Unknown command: {command_id}")
        return self._commands[command_id]

    def all(self) -> tuple[CommandSpec, ...]:
        return tuple(self._commands.values())

    def for_menu(self, menu_id: str) -> tuple[CommandSpec, ...]:
        return tuple(c for c in self._commands.values() if c.menu_id == menu_id)

    def __len__(self) -> int:
        return len(self._commands)


class ReadinessChecker:
    def __init__(
        self,
        project_root: Path,
        config: dict[str, Any] | None = None,
        dependency_checks: dict[str, Callable[[], bool]] | None = None,
    ):
        self.project_root = Path(project_root).resolve()
        self.config = config or {}
        self.dependency_checks = dependency_checks or {}

    def check(self, command: CommandSpec) -> ReadinessReport:
        checks: list[str] = []
        if command.implementation == "planned":
            return ReadinessReport(command.command_id, ReadinessStatus.NOT_IMPLEMENTED,
                                   ("Command is registered and visible.",),
                                   message="No operational implementation is registered.")
        if command.implementation == "partial":
            return ReadinessReport(command.command_id, ReadinessStatus.PARTIAL,
                                   ("A limited implementation exists.",),
                                   message="The operation is only partially implemented.")

        missing_files = []
        for relative in command.required_files:
            target = (self.project_root / relative).resolve()
            if not target.is_relative_to(self.project_root) or not target.is_file():
                missing_files.append(relative)
        if missing_files:
            return ReadinessReport(command.command_id, ReadinessStatus.MISSING_FILES,
                                   missing=tuple(missing_files),
                                   message="Required project files are missing.")
        if command.required_files:
            checks.append("Required files exist.")

        missing_deps = []
        for name in command.dependencies:
            try:
                if find_spec(name) is None:
                    missing_deps.append(name)
            except (ImportError, ModuleNotFoundError, ValueError):
                missing_deps.append(name)
        if missing_deps:
            return ReadinessReport(command.command_id, ReadinessStatus.MISSING_DEPENDENCIES,
                                   tuple(checks), tuple(missing_deps),
                                   "Required Python dependencies are not installed.")
        if command.dependencies:
            checks.append("Required dependencies are importable.")

        missing_config = [key for key in command.required_config if not self._has_config(key)]
        if missing_config:
            return ReadinessReport(command.command_id, ReadinessStatus.CONFIGURATION_ERROR,
                                   tuple(checks), tuple(missing_config),
                                   "Required configuration values are absent or empty.")
        if command.required_config:
            checks.append("Required configuration values are present.")

        for name, probe in self.dependency_checks.items():
            if name in command.dependencies:
                try:
                    if not probe():
                        return ReadinessReport(command.command_id, ReadinessStatus.DEPENDENCY_ERROR,
                                               tuple(checks), (name,),
                                               "Dependency health check failed.")
                except Exception as exc:
                    return ReadinessReport(command.command_id, ReadinessStatus.DEPENDENCY_ERROR,
                                           tuple(checks), (f"{name}: {type(exc).__name__}",),
                                           "Dependency health check raised an error.")

        if command.handler_key == "metadata_dispatch":
            storage = self.config.get("storage", {})
            data_dir = storage.get("data_dir") if isinstance(storage, dict) else None
            if isinstance(data_dir, str) and data_dir.strip():
                folder = Path(data_dir).expanduser()
                if not folder.is_absolute(): folder = self.project_root / folder
                database = folder / "metadata.sqlite3"
                if database.exists():
                    try:
                        connection = sqlite3.connect(f"file:{database.resolve().as_posix()}?mode=ro", uri=True, timeout=2)
                        try:
                            integrity = [row[0] for row in connection.execute("PRAGMA integrity_check")]
                            violations = list(connection.execute("PRAGMA foreign_key_check"))
                        finally:
                            connection.close()
                        if integrity != ["ok"] or violations:
                            return ReadinessReport(command.command_id, ReadinessStatus.STORAGE_ERROR,
                                                   tuple(checks), (str(database),),
                                                   "Metadata database integrity or foreign-key checks failed.")
                        checks.append("Metadata database is reachable and passes integrity checks.")
                    except sqlite3.Error as exc:
                        return ReadinessReport(command.command_id, ReadinessStatus.STORAGE_ERROR,
                                               tuple(checks), (f"{database}: {type(exc).__name__}",),
                                               "Metadata database cannot be inspected.")
                else:
                    checks.append("Metadata database is not initialized; first use will initialize it.")
        if not command.handler_key:
            return ReadinessReport(command.command_id, ReadinessStatus.NOT_IMPLEMENTED,
                                   tuple(checks), message="No execution handler is registered.")
        checks.append("Execution handler is registered.")
        return ReadinessReport(command.command_id, ReadinessStatus.READY, tuple(checks),
                               message="All declared readiness checks passed.")

    def _has_config(self, dotted_key: str) -> bool:
        value: Any = self.config
        for part in dotted_key.split("."):
            if not isinstance(value, dict) or part not in value:
                return False
            value = value[part]
        return value is not None and value != ""


REQUIRED_PATHS = (
    "trading_platform/__main__.py",
    "trading_platform/core.py",
    "trading_platform/cli.py",
    "config/platform.example.toml",
    "tests",
    "docs/ARCHITECTURE.md",
)


def inspect_project(project_root: Path) -> dict[str, Any]:
    root = Path(project_root).resolve()
    present, missing = [], []
    for relative in REQUIRED_PATHS:
        (present if (root / relative).exists() else missing).append(relative)
    return {"root": str(root), "present": tuple(present),
            "missing": tuple(missing), "complete": not missing}


def system_status(project_root: Path) -> dict[str, str]:
    return {
        "Application": "Trading Management Platform",
        "Python": sys.version.split()[0],
        "Implementation": platform.python_implementation(),
        "Platform": platform.platform(),
        "Project root": str(Path(project_root).resolve()),
        "Runtime": "CLI process active",
    }
