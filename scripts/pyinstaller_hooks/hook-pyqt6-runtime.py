# =============================================================================
# PyQt6 Runtime Hook for PyInstaller
# =============================================================================
# This hook runs before the application starts and ensures Qt can find its
# plugins and DLLs on Windows. Without this, you may see:
#   "DLL load failed while importing QtCore"
#   "This application failed to start because no Qt platform plugin could be
#    initialized"
# =============================================================================

import os
import sys


def _setup_qt_plugins():
    """Configure Qt plugin and DLL paths for frozen applications."""
    if not getattr(sys, "frozen", False):
        return  # Not running as frozen executable

    # Get the directory containing the executable
    base_path = sys._MEIPASS  # PyInstaller's temp directory

    if sys.platform == "win32":
        # On Windows, Qt6 DLLs and plugins need to be found
        # Try multiple possible locations for Qt6 files
        possible_qt_paths = [
            os.path.join(base_path, "PyQt6", "Qt6"),
            os.path.join(base_path, "PyQt6", "Qt"),
            os.path.join(base_path, "Qt6"),
            base_path,
        ]

        for qt_path in possible_qt_paths:
            bin_path = os.path.join(qt_path, "bin")
            plugin_path = os.path.join(qt_path, "plugins")

            # Add Qt6 bin directory to PATH so DLLs can be found
            if os.path.exists(bin_path):
                os.environ["PATH"] = bin_path + os.pathsep + os.environ.get("PATH", "")

            # Set plugin path
            if os.path.exists(plugin_path):
                os.environ["QT_PLUGIN_PATH"] = plugin_path

                # Also set platform plugin path
                platforms_path = os.path.join(plugin_path, "platforms")
                if os.path.exists(platforms_path):
                    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = platforms_path
                break

        # Also check for DLLs directly in the base path
        if os.path.exists(os.path.join(base_path, "Qt6Core.dll")):
            os.environ["PATH"] = base_path + os.pathsep + os.environ.get("PATH", "")


_setup_qt_plugins()
