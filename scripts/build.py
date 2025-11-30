#!/usr/bin/env python3
# =============================================================================
# Cosmetics Records - Build Script
# =============================================================================
# This script automates the complete build process for creating standalone
# executables. It performs the following steps:
#   1. Run code quality checks (formatting, linting)
#   2. Run tests to ensure everything works
#   3. Compile translations
#   4. Run PyInstaller to create executable
#   5. Verify the executable was created successfully
#
# Usage:
#   python scripts/build.py
#   python scripts/build.py --skip-tests  # Skip test execution
#   python scripts/build.py --skip-checks # Skip code quality checks
#
# Requirements:
#   - All dev dependencies installed (pytest, black, PyInstaller, etc.)
#   - Clean working directory (no uncommitted changes recommended)
#
# Output:
#   - Executable in dist/ directory
#   - Build logs in build/ directory
# =============================================================================

import argparse
import subprocess
import sys
from pathlib import Path
from datetime import datetime


class Colors:
    """ANSI color codes for terminal output."""

    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def print_header(message):
    """Print a formatted header message."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{message}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}\n")


def print_success(message):
    """Print a success message."""
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")


def print_error(message):
    """Print an error message."""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")


def print_warning(message):
    """Print a warning message."""
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")


def print_info(message):
    """Print an info message."""
    print(f"{Colors.OKCYAN}ℹ {message}{Colors.ENDC}")


def run_command(command, description, cwd=None):
    """
    Run a command and handle errors.

    Args:
        command: Command to run (list of strings)
        description: Human-readable description of what the command does
        cwd: Working directory (None = current directory)

    Returns:
        bool: True if command succeeded, False otherwise
    """
    print_info(f"{description}...")

    try:
        result = subprocess.run(
            command, cwd=cwd, capture_output=True, text=True, check=True
        )

        # Print stdout if there's output
        if result.stdout.strip():
            print(result.stdout)

        print_success(f"{description} completed successfully")
        return True

    except subprocess.CalledProcessError as e:
        print_error(f"{description} failed!")
        print(f"\nCommand: {' '.join(command)}")
        print(f"\nExit code: {e.returncode}")

        if e.stdout:
            print(f"\nStdout:\n{e.stdout}")

        if e.stderr:
            print(f"\nStderr:\n{e.stderr}")

        return False

    except FileNotFoundError:
        print_error(f"Command not found: {command[0]}")
        print_info(f"Make sure {command[0]} is installed and in your PATH")
        return False


def check_code_formatting():
    """Check if code is properly formatted with black."""
    print_header("Step 1: Checking Code Formatting")

    # Check if black is installed
    try:
        subprocess.run(["black", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_warning("black is not installed, skipping formatting check")
        return True

    # Run black in check mode (don't modify files)
    success = run_command(
        ["black", "--check", "src/", "tests/", "scripts/"],
        "Checking code formatting with black",
    )

    if not success:
        print_warning(
            "Code formatting issues found. Run 'black src/ tests/ scripts/' to fix."
        )

    return success


def run_linting():
    """Run flake8 linting checks."""
    print_header("Step 2: Running Linting Checks")

    # Check if flake8 is installed
    try:
        subprocess.run(["flake8", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_warning("flake8 is not installed, skipping linting check")
        return True

    # Run flake8
    success = run_command(
        ["flake8", "src/", "tests/", "--max-line-length=88", "--extend-ignore=E203"],
        "Running flake8 linting",
    )

    if not success:
        print_warning("Linting issues found. Review the output above.")

    return success


def run_tests():
    """Run pytest test suite."""
    print_header("Step 3: Running Tests")

    # Check if pytest is installed
    try:
        subprocess.run(["pytest", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_error("pytest is not installed")
        print_info("Install with: pip install pytest pytest-cov pytest-qt")
        return False

    # Run pytest with verbose output
    success = run_command(
        ["pytest", "tests/", "-v", "--tb=short"], "Running test suite"
    )

    if not success:
        print_error("Tests failed! Fix the failing tests before building.")

    return success


def compile_translations():
    """Compile translation files."""
    print_header("Step 4: Compiling Translations")

    # Check if pybabel is installed
    try:
        subprocess.run(["pybabel", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_warning("pybabel is not installed, skipping translation compilation")
        print_info("Translations will still work, but won't reflect latest changes")
        return True

    # Find all .po files and compile them
    locales_dir = Path("src/cosmetics_records/locales")

    if not locales_dir.exists():
        print_warning("Locales directory not found, skipping translation compilation")
        return True

    po_files = list(locales_dir.rglob("*.po"))

    if not po_files:
        print_info("No translation files found to compile")
        return True

    # Compile each .po file to .mo
    all_success = True
    for po_file in po_files:
        mo_file = po_file.with_suffix(".mo")
        success = run_command(
            ["pybabel", "compile", "-i", str(po_file), "-o", str(mo_file)],
            f"Compiling {po_file.name}",
        )
        all_success = all_success and success

    return all_success


def run_pyinstaller():
    """Run PyInstaller to create executable."""
    print_header("Step 5: Building Executable with PyInstaller")

    # Check if PyInstaller is installed
    try:
        subprocess.run(["pyinstaller", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_error("PyInstaller is not installed")
        print_info("Install with: pip install pyinstaller")
        return False

    # Clean previous builds
    print_info("Cleaning previous builds...")
    import shutil

    for dir_name in ["build", "dist"]:
        if Path(dir_name).exists():
            shutil.rmtree(dir_name)
            print_info(f"Removed {dir_name}/")

    # Run PyInstaller
    success = run_command(
        ["pyinstaller", "cosmetics_records.spec", "--clean"],
        "Building executable with PyInstaller",
    )

    return success


def verify_build():
    """Verify that the executable was created successfully."""
    print_header("Step 6: Verifying Build")

    dist_dir = Path("dist")

    if not dist_dir.exists():
        print_error("dist/ directory not found")
        return False

    # Look for the executable
    executables = list(dist_dir.glob("CosmeticsRecords*"))

    if not executables:
        print_error("Executable not found in dist/ directory")
        return False

    executable = executables[0]
    print_success(f"Executable created: {executable}")

    # Check file size
    size_bytes = executable.stat().st_size
    size_mb = size_bytes / (1024 * 1024)
    print_info(f"Size: {size_mb:.2f} MB")

    return True


def main():
    """Main build process."""
    parser = argparse.ArgumentParser(description="Build Cosmetics Records executable")
    parser.add_argument("--skip-tests", action="store_true", help="Skip running tests")
    parser.add_argument(
        "--skip-checks", action="store_true", help="Skip code quality checks"
    )

    args = parser.parse_args()

    # Record start time
    start_time = datetime.now()

    print(f"{Colors.BOLD}")
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║        Cosmetics Records - Build Script                         ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}")

    # Change to project root directory
    project_root = Path(__file__).parent.parent
    import os

    os.chdir(project_root)
    print_info(f"Working directory: {project_root}")

    # Track success of each step
    steps_passed = 0
    total_steps = 6

    # Step 1: Code formatting
    if not args.skip_checks:
        if check_code_formatting():
            steps_passed += 1
    else:
        print_warning("Skipping code formatting check")
        steps_passed += 1

    # Step 2: Linting
    if not args.skip_checks:
        if run_linting():
            steps_passed += 1
    else:
        print_warning("Skipping linting check")
        steps_passed += 1

    # Step 3: Tests
    if not args.skip_tests:
        if not run_tests():
            print_error("Build aborted due to test failures")
            sys.exit(1)
        steps_passed += 1
    else:
        print_warning("Skipping tests")
        steps_passed += 1

    # Step 4: Compile translations
    if compile_translations():
        steps_passed += 1

    # Step 5: Run PyInstaller
    if not run_pyinstaller():
        print_error("Build failed during PyInstaller step")
        sys.exit(1)
    steps_passed += 1

    # Step 6: Verify build
    if not verify_build():
        print_error("Build verification failed")
        sys.exit(1)
    steps_passed += 1

    # Calculate build time
    end_time = datetime.now()
    build_time = (end_time - start_time).total_seconds()

    # Print summary
    print_header("Build Summary")
    print_success(f"Build completed successfully! ({build_time:.1f} seconds)")
    print_info(f"Steps passed: {steps_passed}/{total_steps}")
    print_info("Executable location: dist/CosmeticsRecords")

    print(f"\n{Colors.BOLD}Next steps:{Colors.ENDC}")
    print("  1. Test the executable: ./dist/CosmeticsRecords")
    print("  2. Test on a clean system (without Python installed)")
    print("  3. Create installer/package for distribution")

    return 0


if __name__ == "__main__":
    sys.exit(main())
