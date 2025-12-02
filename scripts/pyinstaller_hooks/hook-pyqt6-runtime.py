# =============================================================================
# PyQt6 Runtime Hook for PyInstaller
# =============================================================================
# This hook runs before the application starts and ensures Qt can find its
# plugins on Windows. Without this, you may see:
#   "DLL load failed while importing QtCore"
#   "This application failed to start because no Qt platform plugin could be
#    initialized"
# =============================================================================

import os
import sys


def _setup_qt_plugins():
    """Configure Qt plugin paths for frozen applications."""
    if not getattr(sys, "frozen", False):
        return  # Not running as frozen executable

    # Get the directory containing the executable
    if sys.platform == "win32":
        # On Windows, Qt plugins are in PyQt6/Qt6/plugins relative to the exe
        base_path = sys._MEIPASS  # PyInstaller's temp directory
        plugin_path = os.path.join(base_path, "PyQt6", "Qt6", "plugins")

        if os.path.exists(plugin_path):
            os.environ["QT_PLUGIN_PATH"] = plugin_path

        # Also set QT_QPA_PLATFORM_PLUGIN_PATH for the platforms folder
        platforms_path = os.path.join(plugin_path, "platforms")
        if os.path.exists(platforms_path):
            os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = platforms_path


_setup_qt_plugins()
