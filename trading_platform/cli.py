"""Interactive CLI. Non-READY operations are display-only and never dispatched."""
from pathlib import Path
import logging

from trading_platform.catalog import MAIN_MENU, build_command_specs
from trading_platform.configuration import ConfigurationManager
from trading_platform.core import CommandRegistry, ReadinessChecker, inspect_project, system_status
from trading_platform.monitoring import configure_logging


def _header(title: str) -> str:
    line = "=" * 58
    return f"{line}\n{title.center(58)}\n{line}"


class TradingPlatformCLI:
    def __init__(self, project_root: Path | None = None, input_fn=input, output_fn=print):
        self.root = Path(project_root or Path.cwd()).resolve()
        self.input = input_fn
        self.output = output_fn
        self.config_manager = ConfigurationManager(self.root)
        self.config = self.config_manager.load()
        self.logger = configure_logging(self.root, self.config)
        self.registry = CommandRegistry(build_command_specs())
        self.checker = ReadinessChecker(self.root, self.config)
        self.handlers = {
            "system_status": self._system_status,
            "readiness": self._readiness,
            "inspect": self._inspect,
            "config_view": self._config_view,
            "config_validate": self._config_validate,
            "logs": self._logs,
            "roadmap": self._roadmap,
            "market_data_quote": self._market_data_quote,
            "market_data_book": self._market_data_book,
        }

    def run(self) -> None:
        self.logger.info("CLI started")
        while True:
            self.output(_header("TRADING MANAGEMENT PLATFORM"))
            for index, (_, title) in enumerate(MAIN_MENU, 1):
                self.output(f"{index:>2}. {title}")
            self.output(" 0. Exit")
            choice = self._choice("Select an operation: ", len(MAIN_MENU))
            if choice is None or choice == 0:
                self.logger.info("CLI exited")
                self.output("Goodbye.")
                return
            if choice < 0:
                continue
            menu_id, title = MAIN_MENU[choice - 1]
            if menu_id in {"system", "roadmap"}:
                command_id = {"system": "system.status", "roadmap": "roadmap.view"}[menu_id]
                self._dispatch(command_id)
            else:
                self._submenu(menu_id, title)

    def _submenu(self, menu_id: str, title: str) -> None:
        commands = self.registry.for_menu(menu_id)
        while True:
            self.output(_header(title.upper()))
            for index, command in enumerate(commands, 1):
                status = self.checker.check(command).status.value
                self.output(f"{index:>2}. {command.title:<31} [{status}]")
            self.output(" 0. Back")
            choice = self._choice("Select an operation: ", len(commands))
            if choice is None or choice == 0:
                return
            if choice < 0:
                continue
            self._dispatch(commands[choice - 1].command_id)

    def _dispatch(self, command_id: str) -> None:
        command = self.registry.get(command_id)
        report = self.checker.check(command)
        self.output(_header(command.title.upper()))
        self.output(f"STATUS: {report.status.value}")
        if report.message:
            self.output(report.message)
        for item in report.checks:
            self.output(f"[OK] {item}")
        for item in report.missing:
            self.output(f"[MISSING] {item}")
        if not report.is_ready:
            self.output("This operation cannot execute until its status is READY.")
            return
        if command.handler_key == "metadata_dispatch":
            self._metadata_dispatch(command_id)
            return
        handler = self.handlers.get(command.handler_key or "")
        if handler is None:
            self.output("Readiness inconsistency: no runtime handler is registered.")
            self.logger.error("Missing handler for READY command %s", command_id)
            return
        handler()

    def _metadata_dispatch(self, command_id: str) -> None:
        from trading_platform.metadata_cli import MetadataCLI
        adapter = None
        try:
            adapter = MetadataCLI(self.root, self.config, self.input, self.output)
            adapter.execute(command_id)
        except Exception as exc:
            self.output(f"Metadata operation failed: {type(exc).__name__}: {exc}")
            self.logger.exception("Metadata command failed: %s", command_id)
        finally:
            if adapter is not None:
                adapter.close()

    def _readiness(self) -> None:
        self.output(_header("PROJECT READINESS"))
        for command in self.registry.all():
            self.output(f"{command.title:<34} {self.checker.check(command).status.value}")

    def _system_status(self) -> None:
        self.output(_header("SYSTEM STATUS"))
        for key, value in system_status(self.root).items():
            self.output(f"{key:<22}: {value}")

    def _inspect(self) -> None:
        report = inspect_project(self.root)
        self.output(_header("PROJECT STRUCTURE INSPECTOR"))
        self.output(f"Root: {report['root']}")
        for path in report["present"]:
            self.output(f"[OK] {path}")
        for path in report["missing"]:
            self.output(f"[MISSING] {path}")

    def _config_view(self) -> None:
        self.output(_header("EFFECTIVE CONFIGURATION"))
        for section, values in self.config_manager.snapshot().items():
            self.output(f"[{section}]")
            if isinstance(values, dict):
                for key, value in values.items():
                    self.output(f"{key} = {value}")
            else:
                self.output(str(values))

    def _config_validate(self) -> None:
        self.config_manager.validate()
        self.output("Configuration valid.")

    def _logs(self) -> None:
        target = Path(str(self.config.get("logging", {}).get("file", "logs/platform.log")))
        if not target.is_absolute():
            target = self.root / target
        self.output(_header("RECENT LOGS"))
        if not target.is_file():
            self.output("No log file has been created yet.")
            return
        lines = target.read_text(encoding="utf-8").splitlines()
        self.output("\n".join(lines[-30:]) if lines else "Log file is empty.")

    def _market_data_quote(self) -> None:
        from trading_platform.connectors.coinbase_advanced_trade import CoinbaseAdvancedTradeProvider
        product_id = self.input("Product ID (for example BTC-USD): ").strip().upper()
        if not product_id:
            self.output("Cancelled.")
            return
        try:
            quote = CoinbaseAdvancedTradeProvider().get_quote(product_id)
        except Exception as exc:
            self.output(f"Market-data request failed: {type(exc).__name__}: {exc}")
            self.logger.warning("Public market-data quote failed: %s", type(exc).__name__)
            return
        self.output(f"Provider: {quote.provider}")
        self.output(f"Product: {quote.product_id}")
        self.output(f"Best bid: {quote.bid} (size {quote.bid_size})")
        self.output(f"Best ask: {quote.ask} (size {quote.ask_size})")
        self.output(f"Midpoint: {quote.midpoint}")
        self.output(f"Spread: {quote.spread} ({quote.spread_bps:.4f} bps)")
        self.output(f"Received at: {quote.received_at.isoformat()}")
        self.output("READ-ONLY SNAPSHOT — no order was created or submitted.")

    def _market_data_book(self) -> None:
        from trading_platform.connectors.coinbase_advanced_trade import CoinbaseAdvancedTradeProvider
        product_id = self.input("Product ID (for example BTC-USD): ").strip().upper()
        if not product_id:
            self.output("Cancelled.")
            return
        try:
            book = CoinbaseAdvancedTradeProvider().get_order_book(product_id)
        except Exception as exc:
            self.output(f"Market-data request failed: {type(exc).__name__}: {exc}")
            self.logger.warning("Public order-book request failed: %s", type(exc).__name__)
            return
        self.output(f"Provider: {book.provider} | Product: {book.product_id}")
        self.output("BIDS")
        for level in book.bids:
            self.output(f"  {level.price} x {level.size}")
        self.output("ASKS")
        for level in book.asks:
            self.output(f"  {level.price} x {level.size}")
        self.output(f"Received at: {book.received_at.isoformat()}")
        self.output("READ-ONLY SNAPSHOT — no order was created or submitted.")

    def _roadmap(self) -> None:
        target = self.root / "docs/ROADMAP.md"
        self.output(target.read_text(encoding="utf-8"))

    def _choice(self, prompt: str, maximum: int) -> int | None:
        try:
            raw = self.input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            return None
        if not raw.isdigit():
            self.output("Invalid input. Enter a listed number.")
            return -1
        value = int(raw)
        if 0 <= value <= maximum:
            return value
        self.output("Invalid selection.")
        return -1


def main() -> None:
    try:
        TradingPlatformCLI().run()
    except Exception as exc:
        logging.getLogger("trading_platform").exception("Startup failed")
        print(f"Unable to start platform: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()
