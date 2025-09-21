#!/usr/bin/env python3
"""品質・セキュリティチェックヘルパー"""

import argparse
import logging
import subprocess
import sys
import tomllib
from pathlib import Path

# ログ設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def run_command(name: str, cmd: list[str], cwd: Path, verbose: bool = False) -> bool:
    """コマンドを実行し、結果を返す"""
    # CodeQLの場合は時間がかかることを通知
    if "CodeQL" in name:
        logger.info(f"📋 {name}... (数分かかる場合があります)")
    else:
        logger.info(f"📋 {name}...")

    if verbose:
        logger.info(f"コマンド: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"❌ {name}が失敗しました (終了コード: {result.returncode})")
            if result.stdout:
                logger.error(f"標準出力:\n{result.stdout}")
            if result.stderr:
                logger.error(f"エラー出力:\n{result.stderr}")
            return False

        logger.info(f"✅ {name}が完了しました")
        # verbose時のみ成功時の出力を表示
        if verbose and result.stdout:
            logger.info(f"出力:\n{result.stdout}")
        return True
    except FileNotFoundError as e:
        logger.error(f"❌ コマンドが見つかりません: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ {name}実行中にエラーが発生: {e}")
        return False


def get_format_commands(directories: list[str]) -> list[tuple[str, list[str]]]:
    """自動整形コマンドを取得"""
    return [
        ("自動整形", ["uv", "run", "ruff", "format"] + directories),
    ]


def load_pyproject_config(project_root: Path) -> dict:
    """プロジェクト設定を読み込み"""
    pyproject_path = project_root / "pyproject.toml"
    if not pyproject_path.exists():
        return {}

    try:
        with open(pyproject_path, "rb") as f:
            return tomllib.load(f)
    except Exception as e:
        logger.warning(f"⚠️ pyproject.tomlの読み込みに失敗: {e}")
        return {}


def get_default_dirs(config: dict) -> list[str]:
    """デフォルトディレクトリを取得"""
    # mypyの設定からsrc/のみを対象とするか判定
    config.get("tool", {}).get("mypy", {})

    # デフォルトはsrc/のみ、scripts/とtests/はオプション
    return ["src/"]


def get_quality_commands(
    directories: list[str], config: dict
) -> list[tuple[str, list[str]]]:
    """品質チェックコマンドを取得"""
    commands = [
        ("リンティング", ["uv", "run", "ruff", "check"] + directories),
    ]

    # mypyはsrc/のみを対象とする
    src_dirs = [d for d in directories if d.startswith("src/")]
    if src_dirs:
        commands.append(("型チェック", ["uv", "run", "mypy"] + src_dirs))

    return commands


def get_security_commands(directories: list[str]) -> list[tuple[str, list[str]]]:
    """セキュリティチェックコマンドを取得"""
    import platform

    # Windows環境ではPowerShellスクリプトを使用
    if platform.system() == "Windows":
        codeql_cmd = ["pwsh", "-File", "scripts/run_codeql.ps1"]
    else:
        codeql_cmd = ["bash", "scripts/run_codeql.sh"]

    return [
        ("セキュリティスキャン(bandit)", ["uv", "run", "bandit", "-r"] + directories),
        ("セキュリティスキャン(CodeQL)", codeql_cmd),
    ]


def setup_parser(default_dirs: list[str]) -> argparse.ArgumentParser:
    """コマンドラインパーサーを設定"""
    parser = argparse.ArgumentParser(description="品質・セキュリティチェック")
    parser.add_argument(
        "--dirs",
        nargs="+",
        default=default_dirs,
        help=f"チェック対象ディレクトリ (デフォルト: {' '.join(default_dirs)})",
    )
    parser.add_argument(
        "--no-security", action="store_true", help="セキュリティチェックをスキップ"
    )
    parser.add_argument("--codeql-only", action="store_true", help="CodeQLのみ実行")
    parser.add_argument("-v", "--verbose", action="store_true", help="詳細ログを表示")
    return parser


def run_format_checks(
    existing_dirs: list[str], project_root: Path, verbose: bool
) -> None:
    """自動整形を実行"""
    logger.info("🎨 自動整形を実行中...")
    format_commands = get_format_commands(existing_dirs)
    for name, cmd in format_commands:
        run_command(name, cmd, project_root, verbose)


def run_quality_checks(
    existing_dirs: list[str], config: dict, project_root: Path, verbose: bool
) -> bool:
    """品質チェックを実行し、失敗があったかを返す"""
    quality_commands = get_quality_commands(existing_dirs, config)
    failed = False
    for name, cmd in quality_commands:
        if not run_command(name, cmd, project_root, verbose):
            failed = True
    return failed


def run_security_checks(args, existing_dirs: list[str], project_root: Path) -> bool:
    """セキュリティチェックを実行し、失敗があったかを返す"""
    if args.no_security and not args.codeql_only:
        return False

    logger.info("🔒 セキュリティチェックを実行中...")
    security_commands = get_security_commands(existing_dirs)
    failed = False

    for name, cmd in security_commands:
        if args.codeql_only and "bandit" in name:
            continue

        if not run_command(name, cmd, project_root, args.verbose):
            if "CodeQL" in name:
                logger.warning(f"⚠️ {name}で問題が検出されましたが、処理を継続します")
            else:
                failed = True
    return failed


def main():
    """品質・セキュリティチェックを実行"""
    project_root = Path(__file__).parent.parent
    config = load_pyproject_config(project_root)
    default_dirs = get_default_dirs(config)

    parser = setup_parser(default_dirs)
    args = parser.parse_args()

    # 存在するディレクトリのみフィルタ
    existing_dirs = [d for d in args.dirs if (project_root / d).exists()]
    if not existing_dirs:
        logger.error("❌ チェック対象ディレクトリが見つかりません")
        sys.exit(1)

    logger.info(f"🔍 品質チェックを実行中: {', '.join(existing_dirs)}")

    # 各チェックを実行
    run_format_checks(existing_dirs, project_root, args.verbose)
    quality_failed = run_quality_checks(
        existing_dirs, config, project_root, args.verbose
    )
    security_failed = run_security_checks(args, existing_dirs, project_root)

    if quality_failed or security_failed:
        logger.error("❌ 一部のチェックが失敗しました")
        sys.exit(1)

    logger.info("✅ 全ての品質チェックが完了しました！")


if __name__ == "__main__":
    main()
