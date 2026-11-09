from pathlib import Path
import pytest

from trading_platform.catalog import MAIN_MENU, build_command_specs
from trading_platform.cli import TradingPlatformCLI
from trading_platform.configuration import ConfigurationManager
from trading_platform.core import (
    CommandRegistry, CommandSpec, ReadinessChecker, ReadinessStatus, inspect_project
)


def test_complete_command_catalog_and_menu():
    registry = CommandRegistry(build_command_specs())
    assert len(registry) >= 70
    assert len(MAIN_MENU) >= 20
    assert registry.get("bot.start").implementation == "planned"


def test_duplicate_command_ids_rejected():
    command = CommandSpec("x", "X", "x", "m")
    with pytest.raises(ValueError):
        CommandRegistry([command, command])


def test_planned_command_is_not_ready(project_root):
    command = CommandSpec("future", "Future", "future", "m")
    report = ReadinessChecker(project_root).check(command)
    assert report.status is ReadinessStatus.NOT_IMPLEMENTED
    assert not report.is_ready


def test_missing_files_detected(project_root):
    command = CommandSpec("x", "X", "x", "m", "implemented", "handler",
                          required_files=("missing.file",))
    assert ReadinessChecker(project_root).check(command).status is ReadinessStatus.MISSING_FILES


def test_missing_dependencies_detected(project_root):
    command = CommandSpec("x", "X", "x", "m", "implemented", "handler",
                          dependencies=("not_a_real_python_module_123",))
    assert ReadinessChecker(project_root).check(command).status is ReadinessStatus.MISSING_DEPENDENCIES


def test_configuration_error_detected(project_root):
    command = CommandSpec("x", "X", "x", "m", "implemented", "handler",
                          required_config=("missing.key",))
    assert ReadinessChecker(project_root, {}).check(command).status is ReadinessStatus.CONFIGURATION_ERROR


def test_dependency_error_detected(project_root):
    command = CommandSpec("x", "X", "x", "m", "implemented", "handler",
                          dependencies=("json",))
    checker = ReadinessChecker(project_root, dependency_checks={"json": lambda: False})
    assert checker.check(command).status is ReadinessStatus.DEPENDENCY_ERROR


def test_ready_command_requires_file_and_handler(project_root):
    command = CommandSpec("x", "X", "x", "m", "implemented", "handler",
                          required_files=("pyproject.toml",), dependencies=("json",))
    report = ReadinessChecker(project_root).check(command)
    assert report.status is ReadinessStatus.READY


def test_example_configuration_loads(project_root):
    config = ConfigurationManager(project_root).load()
    assert config["platform"]["name"] == "Trading Management Platform"


def test_project_inspector_reports_expected_paths(project_root):
    report = inspect_project(project_root)
    assert "trading_platform/core.py" in report["present"]
    assert "docs/ARCHITECTURE.md" in report["present"]


def test_cli_main_menu_and_exit(project_root):
    output = []
    TradingPlatformCLI(project_root, input_fn=lambda _: "0", output_fn=output.append).run()
    assert "Exchange Management" in "\n".join(output)
    assert "Development Roadmap" in "\n".join(output)


def test_cli_blocks_unimplemented_command(project_root):
    output = []
    cli = TradingPlatformCLI(project_root, output_fn=output.append)
    cli._dispatch("exchange.add_cex")
    result = "\n".join(output)
    assert "NOT IMPLEMENTED" in result
    assert "cannot execute" in result


@pytest.fixture
def project_root():
    return Path(__file__).resolve().parents[1]


def test_project_structure_inspector_is_reachable_from_readiness_menu(project_root):
    output = []
    choices = iter(["15", "2", "0", "0"])
    cli = TradingPlatformCLI(project_root, input_fn=lambda _: next(choices), output_fn=output.append)
    cli.run()
    assert any("PROJECT STRUCTURE INSPECTOR" in item for item in output)


def test_metadata_readiness_reports_corrupt_database(tmp_path):
    from trading_platform.core import CommandSpec, ReadinessStatus
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "metadata.sqlite3").write_bytes(b"not a sqlite database")
    command = CommandSpec("metadata.test", "Metadata", "test", "storage",
                          "implemented", "metadata_dispatch")
    checker = ReadinessChecker(tmp_path, {"storage": {"data_dir": str(data_dir)}})
    assert checker.check(command).status is ReadinessStatus.STORAGE_ERROR

def test_metadata_readiness_does_not_create_uninitialized_database(tmp_path):
    from trading_platform.core import CommandSpec, ReadinessStatus
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    command = CommandSpec("metadata.test", "Metadata", "test", "storage",
                          "implemented", "metadata_dispatch")
    checker = ReadinessChecker(tmp_path, {"storage": {"data_dir": str(data_dir)}})
    assert checker.check(command).status is ReadinessStatus.READY
    assert not (data_dir / "metadata.sqlite3").exists()


def test_public_market_data_commands_are_ready_and_dispatched(project_root):
    from trading_platform.cli import TradingPlatformCLI
    registry = CommandRegistry(build_command_specs())
    checker = ReadinessChecker(project_root, {})
    for command_id in ("marketdata.quote", "marketdata.book"):
        command = registry.get(command_id)
        assert checker.check(command).status is ReadinessStatus.READY
        assert command.handler_key in {"market_data_quote", "market_data_book"}
    assert hasattr(TradingPlatformCLI, "_market_data_quote")
    assert hasattr(TradingPlatformCLI, "_market_data_book")
