# -*- mode: python ; coding: utf-8 -*-
# =============================================================================
# PyInstaller Specification File for Cosmetics Records
# =============================================================================
# This file defines how PyInstaller should bundle the Cosmetics Records
# application into a standalone executable. It specifies:
#   - Entry point (app.py)
#   - Data files to include (locales, resources/icons)
#   - Hidden imports (dependencies that PyInstaller might miss)
#   - Binary dependencies
#   - Executable configuration (name, icon, etc.)
#
# Usage:
#   pyinstaller cosmetics_records.spec
#
# Output:
#   dist/CosmticsRecords (or CosmeticsRecords.exe on Windows)
#
# Platform Support:
#   - Linux: Produces a single executable
#   - Windows: Produces .exe with icon
#   - macOS: Produces .app bundle
# =============================================================================

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Get the project root directory (where this spec file is located)
project_root = Path(SPECPATH)
src_dir = project_root / "src"

# =============================================================================
# PyQt6 Data Collection
# =============================================================================
# PyQt6 requires Qt plugins (platforms, styles, imageformats) to be bundled.
# On Windows, missing plugins cause "DLL load failed" errors.

pyqt6_datas = collect_data_files("PyQt6", include_py_files=False)
pyqt6_hiddenimports = collect_submodules("PyQt6")

# =============================================================================
# Analysis - Collect all Python files and dependencies
# =============================================================================

a = Analysis(
    # Entry point - the main application file
    [str(src_dir / "cosmetics_records" / "app.py")],

    # Path to search for imports
    pathex=[str(src_dir)],

    # Binary files to include (none for this pure-Python project)
    binaries=[],

    # Data files to include (non-Python files needed at runtime)
    datas=[
        # Include locale files for internationalization
        (str(src_dir / "cosmetics_records" / "locales"), "cosmetics_records/locales"),

        # Include resource files (icons, images, etc.)
        (str(src_dir / "cosmetics_records" / "resources"), "cosmetics_records/resources"),
    ] + pyqt6_datas,  # Include PyQt6 plugins (platforms, styles, etc.)

    # Hidden imports - modules that PyInstaller might not detect automatically
    # These are typically imported dynamically (e.g., via importlib)
    hiddenimports=[
        # Pydantic is used for data validation
        "pydantic",
        "pydantic.fields",
        "pydantic.main",

        # Babel is used for internationalization
        "babel",
        "babel.numbers",
        "babel.dates",

        # thefuzz (formerly fuzzywuzzy) for fuzzy string matching
        "thefuzz",
        "thefuzz.fuzz",

        # python-Levenshtein speeds up thefuzz
        "Levenshtein",

        # darkdetect for system theme detection
        "darkdetect",

        # SQLite3 (built-in but sometimes needs explicit inclusion)
        "sqlite3",

        # JSON logging
        "pythonjsonlogger",
    ] + pyqt6_hiddenimports,  # Include all PyQt6 submodules

    # Hook files directory (custom PyInstaller hooks)
    hookspath=[],

    # Additional hook directories (use defaults)
    hooksconfig={},

    # Runtime hooks (code to run before the app starts)
    runtime_hooks=[
        str(project_root / "scripts" / "pyinstaller_hooks" / "hook-pyqt6-runtime.py"),
    ],

    # Modules to exclude (to reduce bundle size)
    excludes=[
        # Development/testing tools (not needed in production)
        "pytest",
        "pytest_cov",
        "pytest_qt",
        "black",
        "flake8",
        "mypy",

        # Documentation tools
        "sphinx",
        "docutils",

        # Unused standard library modules
        "tkinter",  # We use PyQt6, not tkinter
        "matplotlib",  # Not used
        "numpy",  # Not used
        "pandas",  # Not used
    ],

    # Don't traverse into these directories
    noarchive=False,
)

# =============================================================================
# PYZ - Create a compressed archive of Python modules
# =============================================================================

pyz = PYZ(
    a.pure,  # Pure Python modules
    a.zipped_data,  # Data files to include in the archive
)

# =============================================================================
# EXE - Create the executable
# =============================================================================

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],

    # Executable name (platform-specific)
    name="CosmeticsRecords",

    # Debug options
    debug=False,  # Set to True for debugging PyInstaller issues
    bootloader_ignore_signals=False,
    strip=False,  # Don't strip symbols (for better error messages)

    # UPX compression (disabled for compatibility)
    upx=False,  # UPX can cause issues on some systems

    # Console window
    console=False,  # No console window (GUI application)

    # Disable traceback collection (security)
    disable_windowed_traceback=False,

    # Target architecture
    target_arch=None,  # Use current platform architecture

    # Code signing (platform-specific)
    codesign_identity=None,
    entitlements_file=None,

    # Icon file (platform-specific)
    # Note: You'll need to provide icon files for each platform
    # icon="resources/icons/app_icon.ico",  # Windows
    # icon="resources/icons/app_icon.icns",  # macOS
    # icon="resources/icons/app_icon.png",  # Linux
)

# =============================================================================
# Platform-Specific Configuration
# =============================================================================

# macOS: Create an application bundle (.app)
if sys.platform == "darwin":
    app = BUNDLE(
        exe,
        name="CosmeticsRecords.app",
        icon=None,  # Add icon path if available
        bundle_identifier="com.example.cosmeticsrecords",
        info_plist={
            "NSPrincipalClass": "NSApplication",
            "NSHighResolutionCapable": "True",
            "CFBundleName": "Cosmetics Records",
            "CFBundleDisplayName": "Cosmetics Records",
            "CFBundleVersion": "1.0.0",
            "CFBundleShortVersionString": "1.0.0",
            "NSHumanReadableCopyright": "Copyright © 2024. All rights reserved.",
        },
    )

# =============================================================================
# Build Configuration Notes
# =============================================================================

"""
Platform-Specific Build Instructions:

LINUX:
  1. Install dependencies:
     sudo apt-get install python3-dev
  2. Build:
     pyinstaller cosmetics_records.spec
  3. Output:
     dist/CosmeticsRecords (single executable)
  4. Test:
     ./dist/CosmeticsRecords

WINDOWS:
  1. Install dependencies:
     pip install pyinstaller pywin32
  2. Build:
     pyinstaller cosmetics_records.spec
  3. Output:
     dist/CosmeticsRecords.exe
  4. Test:
     dist\CosmeticsRecords.exe

MACOS:
  1. Install dependencies:
     pip install pyinstaller
  2. Build:
     pyinstaller cosmetics_records.spec
  3. Output:
     dist/CosmeticsRecords.app
  4. Test:
     open dist/CosmeticsRecords.app

Troubleshooting:

1. Missing modules:
   Add them to hiddenimports list

2. Missing data files:
   Add them to datas list

3. Size too large:
   Add unused modules to excludes list

4. Runtime errors:
   Set debug=True and console=True to see errors

5. Import errors:
   Check that all dependencies are installed in the build environment

Build Optimization:

- Use virtual environment for clean builds
- Remove __pycache__ before building
- Use upx=True for smaller executables (if no compatibility issues)
- Use strip=True on Linux for smaller binaries

Testing:

- Always test the built executable on a clean system
- Test on the target platform (don't cross-compile)
- Verify all features work (file I/O, database, UI, etc.)
- Check that locales and resources are accessible
"""
