# CLI Guide

Run from the repository root:

    python -m trading_platform

The main menu exposes the sixteen top-level management areas from the initial brief. Domain submenus expose every listed operation, including operations not yet implemented.

The status beside each operation is calculated from the central Command Registry and Readiness Checker. Selecting an operation displays its readiness report. The CLI dispatches only READY operations with a registered handler. Other operations remain visible but cannot execute.

Select 0 to go back or exit. Invalid input is rejected.

The current operational foundation includes System Status, Project Readiness, Project Structure Inspector, View Configuration, Validate Configuration, View Logs, Platform Status, and Development Roadmap.
