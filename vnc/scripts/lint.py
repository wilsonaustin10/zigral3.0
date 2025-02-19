"""
Linting and formatting script for the Zigral project.
"""

import subprocess
import sys


def run_command(command: list[str], description: str) -> bool:
    """Run a command and return True if it succeeds."""
    print(f"\nRunning {description}...")
    try:
        subprocess.run(command, check=True)
        print(f"{description} passed!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"{description} failed with exit code {e.returncode}")
        return False


def run_black(check_only: bool = True) -> bool:
    """Run black formatter."""
    cmd = ["black", ".", "--target-version", "py312"]
    if check_only:
        cmd.append("--check")
    return run_command(cmd, "black")


def run_isort(check_only: bool = True) -> bool:
    """Run isort import sorter."""
    cmd = ["isort", "."]
    if check_only:
        cmd.append("--check-only")
        cmd.append("--diff")
    return run_command(cmd, "isort")


def run_flake8() -> bool:
    """Run flake8 linter."""
    return run_command(["flake8"], "flake8")


def run_all() -> None:
    """Run all linters in check mode."""
    success = all(
        [run_black(check_only=True), run_isort(check_only=True), run_flake8()]
    )
    sys.exit(0 if success else 1)


def format_all() -> None:
    """Format code with all formatters."""
    success = all([run_black(check_only=False), run_isort(check_only=False)])
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    run_all()
