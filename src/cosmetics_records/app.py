# =============================================================================
# Cosmetics Records - Main Application Entry Point
# =============================================================================
# This module is the main entry point for the Cosmetics Records application.
#
# Key Features:
#   - QApplication initialization with proper settings
#   - Main window with navigation and view switching
#   - Database initialization on startup
#   - Theme system integration
#   - Application icon loading
#   - Minimum window size enforcement
#
# Architecture:
#   - MainWindow contains:
#     - NavBar (left side, collapsible)
#     - QStackedWidget (main content area)
#     - Various view widgets (clients, inventory, etc.)
#   - Views are created once and reused (not destroyed on navigation)
#   - Database migrations run automatically on startup
#
# Usage:
#   python -m cosmetics_records.app
#   # or use the main() function from another module
# =============================================================================

import argparse
import logging
import sys
from pathlib import Path
from typing import Literal, Optional, cast

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

# Import package version
from cosmetics_records import __version__

# Import configuration
from cosmetics_records.config import Config

# Import theme system
from cosmetics_records.views.styles import get_theme

# Import navigation component
from cosmetics_records.views.components.navbar import NavBar

# Import database components
from cosmetics_records.database.connection import DatabaseConnection
from cosmetics_records.database.migrations.migration_manager import MigrationManager

# Import backup service for auto-backup
from cosmetics_records.services.backup_service import BackupService

# Import localization
from cosmetics_records.utils.localization import init_translations

# Configure module logger
logger = logging.getLogger(__name__)


class PlaceholderView(QWidget):
    """
    Placeholder view for views that haven't been implemented yet.

    This is a temporary view that shows the view name. It will be replaced
    with actual view implementations.
    """

    def __init__(self, view_name: str, parent: Optional[QWidget] = None):
        """
        Initialize the placeholder view.

        Args:
            view_name: Name of the view (for display)
            parent: Optional parent widget
        """
        super().__init__(parent)

        # Create simple centered label
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        label = QLabel(f"{view_name} View")
        label.setProperty("class", "title")  # Large title styling
        layout.addWidget(label)

        sublabel = QLabel("(Coming soon)")
        sublabel.setProperty("class", "secondary")  # Secondary text styling
        layout.addWidget(sublabel)


class MainWindow(QMainWindow):
    """
    Main application window.

    This is the primary window that contains the navigation bar and all views.
    It manages navigation between different sections of the application.

    Attributes:
        navbar: The navigation bar widget
        stacked_widget: Container for view widgets
        views: Dictionary mapping view IDs to view widgets
        config: Application configuration
    """

    def __init__(self) -> None:
        """
        Initialize the main window.
        """
        super().__init__()

        # Load configuration
        self.config = Config.get_instance()

        # Initialize UI
        self._init_ui()

        # Initialize database
        self._init_database()

        # Check and perform auto-backup if needed
        self._check_auto_backup()

        # Apply theme
        self._apply_theme()

        logger.info("MainWindow initialized")

    def _init_ui(self) -> None:
        """
        Initialize the user interface.

        Sets up the window properties, navigation bar, and view container.
        """
        # Window properties
        self.setWindowTitle(f"Cosmetics Records v{__version__}")
        self.setMinimumSize(1200, 800)

        # Note: Application icon is set on QApplication in main() for proper
        # desktop integration (app switchers, taskbars, launchers). All windows
        # inherit that icon automatically.

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout: [NavBar][Content Area]
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Navigation bar
        self.navbar = NavBar()
        self.navbar.nav_clicked.connect(self._on_navigation)
        main_layout.addWidget(self.navbar)

        # Stacked widget for views
        # WHY QStackedWidget: Allows switching between views without
        # destroying/recreating them, which is faster and preserves state
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget, stretch=1)

        # Create views
        self._create_views()

        # Set initial view to clients list
        self._navigate_to("clients")

    def _create_views(self) -> None:
        """
        Create all view widgets and add them to the stacked widget.

        Creates actual view implementations and wires them to controllers.
        """
        # Import views
        from cosmetics_records.views.clients.client_list_view import ClientListView
        from cosmetics_records.views.clients.client_detail_view import ClientDetailView
        from cosmetics_records.views.inventory.inventory_view import InventoryView
        from cosmetics_records.views.audit.audit_log_view import AuditLogView
        from cosmetics_records.views.settings.settings_view import SettingsView

        # Dictionary to store view references
        # WHY store references: Allows us to access views later for updates
        self.views: dict[str, QWidget] = {}

        # Create clients list view
        try:
            clients_view = ClientListView()
            # Wire up client selection to show detail view
            clients_view.client_selected.connect(self.show_client_detail)
            # Wire up add client to show add dialog
            clients_view.add_client_clicked.connect(self._on_add_client_clicked)
            self.views["clients"] = clients_view
            self.stacked_widget.addWidget(clients_view)
            logger.debug("ClientListView created and connected")
        except Exception as e:
            logger.error(f"Failed to create ClientListView: {e}")
            # Fall back to placeholder
            self.views["clients"] = PlaceholderView("Clients")
            self.stacked_widget.addWidget(self.views["clients"])

        # Create client detail view
        try:
            client_detail_view = ClientDetailView()
            # Wire up back button to return to list and refresh it
            # (refresh is needed when client is deleted)
            client_detail_view.back_to_list.connect(self._on_back_to_client_list)
            self.views["client_detail"] = client_detail_view
            self.stacked_widget.addWidget(client_detail_view)
            logger.debug("ClientDetailView created and connected")
        except Exception as e:
            logger.error(f"Failed to create ClientDetailView: {e}")
            # Fall back to placeholder
            self.views["client_detail"] = PlaceholderView("Client Detail")
            self.stacked_widget.addWidget(self.views["client_detail"])

        # Create inventory view
        try:
            inventory_view = InventoryView()
            self.views["inventory"] = inventory_view
            self.stacked_widget.addWidget(inventory_view)
            logger.debug("InventoryView created")
        except Exception as e:
            logger.error(f"Failed to create InventoryView: {e}")
            # Fall back to placeholder
            self.views["inventory"] = PlaceholderView("Inventory")
            self.stacked_widget.addWidget(self.views["inventory"])

        # Create audit log view
        try:
            audit_view = AuditLogView()
            self.views["audit"] = audit_view
            self.stacked_widget.addWidget(audit_view)
            logger.debug("AuditLogView created")
        except Exception as e:
            logger.error(f"Failed to create AuditLogView: {e}")
            # Fall back to placeholder
            self.views["audit"] = PlaceholderView("Audit Log")
            self.stacked_widget.addWidget(self.views["audit"])

        # Create settings view
        try:
            settings_view = SettingsView()
            # Wire up theme changes to apply immediately
            settings_view.theme_changed.connect(self._on_theme_changed)
            # Wire up scale changes to apply immediately
            settings_view.scale_changed.connect(self._on_scale_changed)
            # Wire up language changes to apply immediately
            settings_view.language_changed.connect(self._on_language_changed)
            # Wire up data import to refresh client list
            settings_view.data_imported.connect(self._on_data_imported)
            self.views["settings"] = settings_view
            self.stacked_widget.addWidget(settings_view)
            logger.debug("SettingsView created and connected")
        except Exception as e:
            logger.error(f"Failed to create SettingsView: {e}")
            # Fall back to placeholder
            self.views["settings"] = PlaceholderView("Settings")
            self.stacked_widget.addWidget(self.views["settings"])

        logger.debug(f"Created {len(self.views)} views")

    def _on_navigation(self, view_id: str) -> None:
        """
        Handle navigation item click.

        Args:
            view_id: ID of the view to navigate to
        """
        logger.info(f"Navigation to: {view_id}")
        self._navigate_to(view_id)

    def _navigate_to(self, view_id: str) -> None:
        """
        Navigate to a specific view.

        Args:
            view_id: ID of the view to show

        Note:
            This updates both the navbar active state and the visible view.
            Client detail nav item stays visible once a client is viewed.
        """
        if view_id in self.views:
            # Update navbar
            self.navbar.set_active(view_id)

            # Switch to view
            self.stacked_widget.setCurrentWidget(self.views[view_id])

            logger.debug(f"Navigated to view: {view_id}")
        else:
            logger.error(f"Unknown view ID: {view_id}")

    def _init_database(self) -> None:
        """
        Initialize the database.

        Creates database connection and runs pending migrations.

        Note:
            This is called during startup. Any migration failures will be
            logged but won't prevent the app from starting (though it may
            not work correctly).
        """
        try:
            logger.info("Initializing database...")

            # Create database connection
            # WHY default connection: Uses standard database location
            db = DatabaseConnection()

            # Run migrations
            migration_manager = MigrationManager(db)
            migrations_applied = migration_manager.apply_migrations()

            if migrations_applied > 0:
                logger.info(f"Applied {migrations_applied} database migrations")
            else:
                logger.info("Database is up to date")

            # Get current schema version
            version = migration_manager.get_current_version()
            logger.info(f"Database schema version: {version}")

        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            # Don't crash the app, but it probably won't work correctly
            # TODO: Show error dialog to user

    def _check_auto_backup(self) -> None:
        """
        Check if auto-backup is due and create one if needed.

        Called during startup. Checks the backup settings and last backup
        time to determine if a backup should be created automatically.

        Note:
            This method will not crash the app if backup fails. Backup
            failures are logged but do not prevent normal operation.
        """
        try:
            # Check if auto-backup is enabled
            if not self.config.auto_backup:
                logger.debug("Auto-backup is disabled")
                return

            # Initialize backup service
            config_dir = self.config.get_config_dir()
            backup_dir = config_dir / "backups"
            db_path = config_dir / "cosmetics_records.db"
            backup_service = BackupService(str(db_path), str(backup_dir))

            # Check if backup is due
            if backup_service.should_auto_backup(
                self.config.backup_interval_minutes,
                self.config.last_backup_time,
            ):
                logger.info("Auto-backup is due, creating backup...")

                # Create backup
                backup_path = backup_service.create_backup()

                # Update last backup time
                from datetime import datetime

                self.config.last_backup_time = datetime.now()
                self.config.save()

                # Cleanup old backups based on retention setting
                deleted = backup_service.cleanup_old_backups(
                    self.config.backup_retention_count
                )
                if deleted > 0:
                    logger.info(f"Cleaned up {deleted} old backups")

                logger.info(f"Auto-backup created: {backup_path}")
            else:
                logger.debug("Auto-backup not due yet")

        except Exception as e:
            logger.error(f"Auto-backup failed: {e}")
            # Don't crash the app if auto-backup fails

    def _apply_theme(self) -> None:
        """
        Apply the current theme to the application.

        Reads the theme setting from config and applies the appropriate
        stylesheet with the current UI scale.
        """
        try:
            # Get theme name and scale from config
            theme_name = self.config.theme
            ui_scale = self.config.ui_scale

            # Get stylesheet with scale applied
            stylesheet = get_theme(
                cast(Literal["dark", "light", "system"], theme_name), ui_scale
            )

            # Apply to application
            # WHY apply to QApplication not MainWindow: Ensures all windows
            # and dialogs use the same theme
            app = QApplication.instance()
            if app is not None and isinstance(app, QApplication):
                app.setStyleSheet(stylesheet)

            # Update navbar icon colors based on theme
            is_dark = self._is_dark_theme(theme_name)
            self.navbar.update_icon_colors(is_dark)

            logger.info(f"Applied theme: {theme_name} at scale {ui_scale:.0%}")

        except Exception as e:
            logger.error(f"Failed to apply theme: {e}")

    def show_client_detail(self, client_id: int) -> None:
        """
        Navigate to the client detail view for a specific client.

        This is a helper method that other parts of the application can call
        to navigate to a specific client's detail page.

        Args:
            client_id: ID of the client to show

        Example:
            # From clients list view when user clicks a client
            main_window.show_client_detail(123)
        """
        from cosmetics_records.database.connection import DatabaseConnection
        from cosmetics_records.controllers.client_controller import ClientController

        # Update client_detail view with the client data
        if "client_detail" in self.views:
            try:
                from cosmetics_records.views.clients.client_detail_view import (
                    ClientDetailView,
                )

                view = self.views["client_detail"]
                if isinstance(view, ClientDetailView):
                    view.load_client(client_id)

                # Get client name for nav label
                with DatabaseConnection() as db:
                    controller = ClientController(db)
                    client = controller.get_client(client_id)
                    if client:
                        # Update nav button label with client name
                        self.navbar.set_item_label("client_detail", client.full_name())
                        # Make client detail nav item visible
                        self.navbar.set_item_visible("client_detail", True)

            except Exception as e:
                logger.error(f"Failed to load client {client_id}: {e}")

        # Navigate to the view
        self._navigate_to("client_detail")

        logger.info(f"Showing client detail for ID: {client_id}")

    def _on_add_client_clicked(self) -> None:
        """
        Handle add client button click.

        Opens the add client dialog, saves the client to the database,
        and refreshes the list on success.
        """
        from cosmetics_records.views.dialogs.add_client_dialog import AddClientDialog
        from cosmetics_records.database.connection import DatabaseConnection
        from cosmetics_records.controllers.client_controller import ClientController
        from cosmetics_records.models.client import Client

        try:
            dialog = AddClientDialog(self)
            if dialog.exec():
                # Get the client data from the dialog
                client_data = dialog.get_client_data()

                # Create Client model from the data
                client = Client(
                    first_name=client_data["first_name"],
                    last_name=client_data["last_name"],
                    email=client_data["email"] or None,
                    phone=client_data["phone"] or None,
                    address=client_data["address"] or None,
                    date_of_birth=client_data["date_of_birth"],
                    allergies=client_data["allergies"] or None,
                    tags=client_data["tags"],
                )

                # Save to database
                with DatabaseConnection() as db:
                    controller = ClientController(db)
                    client_id = controller.create_client(client)
                    logger.info(f"Client created with ID: {client_id}")

                # Refresh the list to show the new client
                if "clients" in self.views:
                    view = self.views["clients"]
                    if hasattr(view, "refresh"):
                        view.refresh()

                logger.info(f"Client added successfully: {client.full_name()}")
        except Exception as e:
            logger.error(f"Failed to add client: {e}")

    def _on_back_to_client_list(self) -> None:
        """
        Handle returning to client list from detail view.

        Navigates back to the clients list and refreshes it.
        This ensures deleted clients are removed from the UI.
        """
        self._navigate_to("clients")

        # Hide the client detail navbar item since no client is selected
        self.navbar.set_item_visible("client_detail", False)

        # Refresh the list to reflect any changes (e.g., deleted client)
        if "clients" in self.views:
            view = self.views["clients"]
            if hasattr(view, "refresh"):
                view.refresh()

        logger.debug("Returned to client list and refreshed")

    def _on_data_imported(self) -> None:
        """
        Handle data import completion.

        Refreshes the client list to show newly imported clients.
        """
        logger.info("Data imported, refreshing client list")

        # Refresh the client list to show imported clients
        if "clients" in self.views:
            view = self.views["clients"]
            if hasattr(view, "refresh"):
                view.refresh()

    def _is_dark_theme(self, theme_name: str) -> bool:
        """
        Determine if the given theme name results in a dark theme.

        Args:
            theme_name: Theme name ("dark", "light", or "system")

        Returns:
            True if the theme is dark, False if light
        """
        if theme_name == "dark":
            return True
        elif theme_name == "light":
            return False
        else:  # "system"
            from cosmetics_records.views.styles import detect_system_theme

            return detect_system_theme() == "dark"

    def _on_theme_changed(self, theme: str) -> None:
        """
        Handle theme change from settings.

        Applies the new theme to the application immediately with current scale.

        Args:
            theme: Theme name ("dark", "light", or "system")
        """
        logger.info(f"Applying theme change: {theme}")

        try:
            # Get current scale from config
            ui_scale = self.config.ui_scale

            # Get stylesheet for new theme with scale
            stylesheet = get_theme(
                cast(Literal["dark", "light", "system"], theme), ui_scale
            )

            # Apply to application
            app = QApplication.instance()
            if app is not None and isinstance(app, QApplication):
                app.setStyleSheet(stylesheet)

            # Update navbar icon colors based on theme
            is_dark = self._is_dark_theme(theme)
            self.navbar.update_icon_colors(is_dark)

            logger.info(f"Theme applied: {theme} at scale {ui_scale:.0%}")

        except Exception as e:
            logger.error(f"Failed to apply theme: {e}")

    def _on_scale_changed(self, scale: float) -> None:
        """
        Handle UI scale change from settings.

        Applies the new scale to the application immediately by regenerating
        the stylesheet with scaled font sizes.

        Args:
            scale: Scale factor (e.g., 1.0 for 100%, 1.5 for 150%)
        """
        logger.info(f"Applying scale change: {scale:.0%}")

        try:
            # Get current theme from config
            theme_name = self.config.theme

            # Get stylesheet with new scale applied
            stylesheet = get_theme(
                cast(Literal["dark", "light", "system"], theme_name), scale
            )

            # Apply to application
            app = QApplication.instance()
            if app is not None and isinstance(app, QApplication):
                app.setStyleSheet(stylesheet)

            logger.info(f"Scale applied: {scale:.0%} with theme {theme_name}")

        except Exception as e:
            logger.error(f"Failed to apply scale: {e}")

    def _on_language_changed(self, language: str) -> None:
        """
        Handle language change from settings.

        Reinitializes translations and recreates all views to apply the new
        language immediately.

        Args:
            language: Language code ("en" or "de")
        """
        logger.info(f"Applying language change: {language}")

        try:
            # Reinitialize translations with new language
            init_translations(language)

            # Store current view before recreation
            current_view_id = None
            for view_id, view in self.views.items():
                if self.stacked_widget.currentWidget() == view:
                    current_view_id = view_id
                    break

            # Clear existing views
            while self.stacked_widget.count():
                widget = self.stacked_widget.widget(0)
                self.stacked_widget.removeWidget(widget)
                if widget is not None:
                    widget.deleteLater()
            self.views.clear()

            # Recreate all views with new language
            self._create_views()

            # Recreate navbar with new translations
            old_navbar = self.navbar
            self.navbar = NavBar()
            self.navbar.nav_clicked.connect(self._on_navigation)

            # Replace old navbar in layout
            central_widget = self.centralWidget()
            if central_widget is not None:
                main_layout = central_widget.layout()
                if main_layout is not None:
                    main_layout.replaceWidget(old_navbar, self.navbar)
            old_navbar.deleteLater()

            # Navigate to the previously selected view (or default to clients)
            if current_view_id and current_view_id in self.views:
                self._navigate_to(current_view_id)
            else:
                self._navigate_to("clients")

            logger.info(f"Language applied: {language}")

        except Exception as e:
            logger.error(f"Failed to apply language change: {e}")


def setup_logging(console_level: int = logging.WARNING) -> None:
    """
    Configure application logging.

    Sets up both console and file logging with appropriate formatting.
    Console defaults to WARNING level to reduce noise, file always logs DEBUG.

    Args:
        console_level: Logging level for console output (default: WARNING)
    """
    # Get config to determine log location
    config = Config.get_instance()
    log_dir = config.get_config_dir()
    log_file = log_dir / "cosmetics_records.log"

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Console handler - uses specified level
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)

    # File handler - always DEBUG for full diagnostics
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture all, handlers filter
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    logger.info("Logging configured")
    logger.info(f"Log file: {log_file}")
    logger.info(f"Console log level: {logging.getLevelName(console_level)}")


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Cosmetics Records - Client and treatment management"
    )

    parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error"],
        default="warning",
        help="Console log level (default: warning). File always logs debug.",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output (same as --log-level=debug)",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"Cosmetics Records {__version__}",
    )

    return parser.parse_args()


def main() -> int:
    """
    Main application entry point.

    This function:
    1. Parses command-line arguments
    2. Sets up logging
    3. Creates QApplication
    4. Creates and shows MainWindow
    5. Starts event loop
    6. Returns exit code

    Returns:
        int: Application exit code (0 for success)

    Example:
        if __name__ == "__main__":
            sys.exit(main())
    """
    # Parse command-line arguments
    args = parse_args()

    # Determine log level
    if args.verbose:
        console_level = logging.DEBUG
    else:
        level_map = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
        }
        console_level = level_map[args.log_level]

    # Set up logging
    setup_logging(console_level)

    logger.info("=" * 80)
    logger.info("Cosmetics Records Application Starting")
    logger.info("=" * 80)

    # Enable high DPI scaling BEFORE creating QApplication
    # WHY: Qt requires this to be set before QGuiApplication is created
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # Create Qt Application
    # WHY sys.argv: Allows Qt to process command-line arguments
    app = QApplication(sys.argv)

    # Application metadata
    app.setApplicationName("Cosmetics Records")
    app.setOrganizationName("Cosmetics Records")
    app.setApplicationVersion(__version__)

    # Set application icon (for app switchers, taskbars, launchers)
    # WHY set on QApplication: Ensures all windows inherit the icon
    try:
        # Handle PyInstaller bundled resources
        # WHY _MEIPASS: PyInstaller extracts bundled files to a temp directory
        # and sets sys._MEIPASS to that path. In development, we use __file__.
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            # Running from PyInstaller bundle
            base_path = Path(sys._MEIPASS) / "cosmetics_records"
        else:
            # Running in development
            base_path = Path(__file__).parent

        icon_path = base_path / "resources" / "icons" / "icon-256.png"
        if icon_path.exists():
            app.setWindowIcon(QIcon(str(icon_path)))
            logger.debug(f"Application icon set from {icon_path}")
        else:
            logger.warning(f"Application icon not found at {icon_path}")
    except Exception as e:
        logger.warning(f"Failed to set application icon: {e}")

    # Initialize translations before creating any UI
    # Load language from config (defaults to English)
    config = Config.get_instance()
    init_translations(config.language)
    logger.info(f"Translations initialized for language: {config.language}")

    # Create and show main window
    window = MainWindow()
    window.show()

    # Start event loop
    # WHY exec() not exec: Python 3 renamed exec to exec() to avoid keyword conflict
    exit_code: int = app.exec()

    logger.info("Application exiting with code: %d", exit_code)
    return exit_code


# Entry point when run as a script
if __name__ == "__main__":
    sys.exit(main())
