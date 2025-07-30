#!/usr/bin/env python3
"""
Development automation scripts for the MFA Passport Bot project.
"""

import subprocess  # nosec B404
import sys
from pathlib import Path

import click
import pytest
from mypy import api as mypy_api


@click.group()
def cli() -> None:
    """Development tools for MFA Passport Bot."""
    pass


@cli.command()
def setup() -> None:
    """Set up the development environment."""
    click.echo("🔧 Setting up development environment...")

    commands = [
        ["poetry", "install", "--with", "dev"],
        ["pre-commit", "install"],
        ["playwright", "install", "chromium"],
    ]

    for cmd in commands:
        click.echo(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)  # nosec B603
        if result.returncode != 0:
            click.echo(f"❌ Command failed: {result.stderr}")
            sys.exit(1)

    click.echo("✅ Development environment set up successfully!")


@cli.command()
@click.option("--fix", is_flag=True, help="Automatically fix issues")
def lint(fix: bool) -> None:
    """Run linting checks."""
    click.echo("🔍 Running linting checks...")

    commands = []
    if fix:
        commands = [
            ["ruff", "check", "--fix", "bot/"],
            ["ruff", "format", "bot/"],
            ["black", "bot/"],
        ]
    else:
        commands = [
            ["ruff", "check", "bot/"],
            ["black", "--check", "bot/"],
        ]

    failed = False
    for cmd in commands:
        click.echo(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd)  # nosec B603
        if result.returncode != 0:
            failed = True

    if failed:
        click.echo("❌ Linting checks failed")
        sys.exit(1)
    else:
        click.echo("✅ All linting checks passed")


@cli.command()
def typecheck() -> None:
    """Run type checking with mypy."""
    click.echo("🏷️  Running type checking...")
    stdout, stderr, exit_status = mypy_api.run(["bot/"])
    if stdout:
        click.echo(stdout)
    if stderr:
        click.echo(stderr)
    if exit_status != 0:
        click.echo("❌ Type checking failed")
        sys.exit(exit_status)
    click.echo("✅ Type checking passed")


@cli.command()
def security() -> None:
    """Run security checks with bandit."""
    click.echo("🔒 Running security checks...")
    from bandit.cli.main import main as bandit_main  # type: ignore[import-not-found]

    rc = bandit_main(["-r", "bot/", "-f", "json"])
    if rc != 0:
        click.echo("❌ Security checks failed")
        sys.exit(rc)
    click.echo("✅ Security checks passed")


@cli.command()
@click.option("--cov", is_flag=True, help="Run with coverage")
@click.option("--html", is_flag=True, help="Generate HTML coverage report")
def test(cov: bool, html: bool) -> None:
    """Run tests."""
    click.echo("🧪 Running tests...")

    cmd = ["pytest"]
    if cov:
        cmd.extend(["--cov=bot", "--cov-report=term-missing"])
        if html:
            cmd.append("--cov-report=html")

    rc = pytest.main(cmd[1:])
    if rc != 0:
        click.echo("❌ Tests failed")
        sys.exit(rc)
    click.echo("✅ All tests passed")


@cli.command()
def check() -> None:
    """Run all checks (lint, typecheck, security, test)."""
    click.echo("🔍 Running all quality checks...")

    checks = [
        (lint, {"fix": False}),
        (typecheck, {}),
        (security, {}),
        (test, {"cov": True, "html": False}),
    ]

    failed_checks = []

    for check_func, kwargs in checks:
        try:
            ctx = click.Context(check_func)
            check_func.invoke(ctx, **kwargs)
        except SystemExit as e:
            if e.code != 0:
                failed_checks.append(check_func.name or "unknown")

    if failed_checks:
        click.echo(f"❌ Failed checks: {', '.join(failed_checks)}")
        sys.exit(1)
    else:
        click.echo("✅ All quality checks passed!")


@cli.command()
def clean() -> None:
    """Clean up temporary files and caches."""
    click.echo("🧹 Cleaning up temporary files...")

    patterns = [
        "**/__pycache__",
        "**/*.pyc",
        "**/*.pyo",
        ".pytest_cache",
        ".mypy_cache",
        ".coverage",
        "htmlcov",
        "*.log",
        "logs/*.log",
    ]

    for pattern in patterns:
        for path in Path(".").glob(pattern):
            if path.is_file():
                path.unlink()
                click.echo(f"Removed file: {path}")
            elif path.is_dir():
                import shutil

                shutil.rmtree(path)
                click.echo(f"Removed directory: {path}")

    click.echo("✅ Cleanup completed")


@cli.command()
@click.argument("version")
def release(version: str) -> None:
    """Prepare a new release."""
    click.echo(f"📦 Preparing release {version}...")

    # Update version in pyproject.toml
    pyproject_path = Path("pyproject.toml")
    content = pyproject_path.read_text()
    content = content.replace('version = "0.2.1"', f'version = "{version}"')
    pyproject_path.write_text(content)

    # Run all checks
    ctx = click.Context(check)
    try:
        check.invoke(ctx)
    except SystemExit as e:
        if e.code != 0:
            click.echo("❌ Pre-release checks failed")
            sys.exit(1)

    click.echo(f"✅ Release {version} prepared successfully!")
    click.echo("Next steps:")
    click.echo("1. git add -A")
    click.echo(f"2. git commit -m 'Release {version}'")
    click.echo(f"3. git tag v{version}")
    click.echo("4. git push origin main --tags")


if __name__ == "__main__":
    cli()
