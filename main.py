"""Bulk Migrator Typer CLI entrypoint."""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import typer
from dotenv import load_dotenv
from rich.console import Console

project_root = Path(__file__).resolve().parent
load_dotenv(project_root / ".env", override=False)

app = typer.Typer(help="Bulk Migrator utility launcher")
console = Console()


def _run_command(command: list[str]) -> None:
    """Execute a subprocess command and propagate non-zero exit codes."""
    try:
        subprocess.run(command, cwd=project_root, check=True)
    except subprocess.CalledProcessError as exc:  # noqa: PERF203
        raise typer.Exit(exc.returncode) from exc


def _run_module(module: str, *args: str) -> None:
    """Run a Python module with the current interpreter."""
    command = [sys.executable, "-m", module]
    command.extend(args)
    _run_command(command)


def _run_script(path: Path, *args: str) -> None:
    """Run a Python script located at *path*."""
    command = [sys.executable, str(path)]
    command.extend(args)
    _run_command(command)


@app.command()
def transfer(
    reset: bool = typer.Option(False, help="--reset を付与して転送キャッシュを初期化"),
    full_rebuild: bool = typer.Option(False, help="--full-rebuild を付与して完全再構築"),
    verbose: bool = typer.Option(False, help="src.main の --verbose を付与"),
) -> None:
    """Run the primary OneDrive → SharePoint transfer flow (src/main.py)."""

    if reset and full_rebuild:
        raise typer.BadParameter("--reset と --full-rebuild は同時には指定できません。")

    options: list[str] = []
    if reset:
        options.append("--reset")
    if full_rebuild:
        options.append("--full-rebuild")
    if verbose:
        options.append("--verbose")

    _run_module("src.main", *options)


@app.command("rebuild-skiplist")
def rebuild_skiplist() -> None:
    """Rebuild the SharePoint skip list (src/rebuild_skip_list.py)."""

    _run_module("src.rebuild_skip_list")


@app.command()
def watchdog() -> None:
    """Launch the transfer watchdog (src/watchdog.py)."""

    _run_module("src.watchdog")


@app.command("quality-metrics")
def quality_metrics() -> None:
    """Generate quality metrics reports (src/quality_metrics.py)."""

    _run_module("src.quality_metrics")


@app.command("quality-alerts")
def quality_alerts() -> None:
    """Evaluate quality thresholds and emit alerts (src/quality_alerts.py)."""

    _run_module("src.quality_alerts")


@app.command("security-scan")
def security_scan() -> None:
    """Run security tooling bundle (scripts/security_scan.py)."""

    _run_script(project_root / "scripts" / "security_scan.py")


@app.command("file-crawler")
def file_crawler() -> None:
    """Open the auxiliary file crawler CLI (utils/file_crawler_cli.py)."""

    _run_module("utils.file_crawler_cli")


def _menu(ctx: typer.Context) -> None:
    entries: list[tuple[str, Callable[[], None]]] = [
        (
            "OneDrive→SharePoint 転送 (src/main.py)",
            lambda: ctx.invoke(transfer),
        ),
        (
            "スキップリスト再構築 (src/rebuild_skip_list.py)",
            lambda: ctx.invoke(rebuild_skiplist),
        ),
        (
            "ウォッチドッグ起動 (src/watchdog.py)",
            lambda: ctx.invoke(watchdog),
        ),
        (
            "品質メトリクス集計 (src/quality_metrics.py)",
            lambda: ctx.invoke(quality_metrics),
        ),
        (
            "品質アラート生成 (src/quality_alerts.py)",
            lambda: ctx.invoke(quality_alerts),
        ),
        (
            "セキュリティスキャン (scripts/security_scan.py)",
            lambda: ctx.invoke(security_scan),
        ),
        (
            "ファイルクロールユーティリティ (utils/file_crawler_cli.py)",
            lambda: ctx.invoke(file_crawler),
        ),
    ]

    console.print("[bold cyan]Bulk Migrator メニュー[/]")
    for idx, (label, _action) in enumerate(entries, start=1):
        console.print(f"  {idx}. {label}")

    choice = typer.prompt("番号を入力してください", type=int)
    if not 1 <= choice <= len(entries):
        raise typer.BadParameter("メニュー番号が正しくありません。")

    entries[choice - 1][1]()


@app.command()
def menu(ctx: typer.Context) -> None:
    """Display an interactive launcher for the main features."""

    _menu(ctx)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """Launch the menu when no sub-command is provided."""

    if ctx.invoked_subcommand is None:
        _menu(ctx)


if __name__ == "__main__":
    app()
