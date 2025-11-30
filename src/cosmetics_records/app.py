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

import logging
import sys
from pathlib import Path
from typing import Optional

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

# Import configuration
from cosmetics_records.config import Config

# Import theme system
from cosmetics_records.views.styles import get_theme

# Import navigation component
from cosmetics_records.views.components.navbar import NavBar

# Import database components
from cosmetics_records.database.connection import DatabaseConnection
from cosmetics_records.database.migrations.migration_manager import MigrationManager

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

    def __init__(self):
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

        # Apply theme
        self._apply_theme()

        logger.info("MainWindow initialized")

    def _init_ui(self) -> None:
        """
        Initialize the user interface.

        Sets up the window properties, navigation bar, and view container.
        """
        # Window properties
        self.setWindowTitle("Cosmetics Records v1.0")
        self.setMinimumSize(1200, 800)

        # Try to load application icon
        # WHY try/except: Icon file might not exist yet, don't crash if missing
        try:
            icon_path = Path(__file__).parent / "resources" / "icons" / "icon-256.png"
            if icon_path.exists():
                self.setWindowIcon(QIcon(str(icon_path)))
                logger.debug(f"Application icon loaded from {icon_path}")
            else:
                logger.warning(f"Application icon not found at {icon_path}")
        except Exception as e:
            logger.warning(f"Failed to load application icon: {e}")

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
        self.views = {}

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
            # Wire up back button to return to list
            client_detail_view.back_to_list.connect(
                lambda: self._navigate_to("clients")
            )
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
        """
        if view_id in self.views:
            # Update navbar
            self.navbar.set_active(view_id)

            # Switch to view
            self.stacked_widget.setCurrentWidget(self.views[view_id])

            # Special handling for client_detail view
            # WHY: Client detail should only be visible when viewing a client
            if view_id == "client_detail":
                self.navbar.set_item_visible("client_detail", True)
            elif view_id == "clients":
                # Hide client detail when returning to clients list
                self.navbar.set_item_visible("client_detail", False)

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
            stylesheet = get_theme(theme_name, ui_scale)

            # Apply to application
            # WHY apply to QApplication not MainWindow: Ensures all windows
            # and dialogs use the same theme
            QApplication.instance().setStyleSheet(stylesheet)

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
        # Update client_detail view with the client data
        if "client_detail" in self.views:
            try:
                self.views["client_detail"].load_client(client_id)
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
                    self.views["clients"].refresh()

                logger.info(f"Client added successfully: {client.full_name()}")
        except Exception as e:
            logger.error(f"Failed to add client: {e}")

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
            stylesheet = get_theme(theme, ui_scale)

            # Apply to application
            QApplication.instance().setStyleSheet(stylesheet)

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
            stylesheet = get_theme(theme_name, scale)

            # Apply to application
            QApplication.instance().setStyleSheet(stylesheet)

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
            main_layout = central_widget.layout()
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


def setup_logging() -> None:
    """
    Configure application logging.

    Sets up both console and file logging with appropriate formatting.
    """
    # Get config to determine log location
    config = Config.get_instance()
    log_dir = config.get_config_dir()
    log_file = log_dir / "cosmetics_records.log"

    # Create logging configuration
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            # Console handler
            logging.StreamHandler(sys.stdout),
            # File handler
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )

    logger.info("Logging configured")
    logger.info(f"Log file: {log_file}")


def main() -> int:
    """
    Main application entry point.

    This function:
    1. Sets up logging
    2. Creates QApplication
    3. Creates and shows MainWindow
    4. Starts event loop
    5. Returns exit code

    Returns:
        int: Application exit code (0 for success)

    Example:
        if __name__ == "__main__":
            sys.exit(main())
    """
    # Set up logging first
    setup_logging()

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
    app.setApplicationVersion("1.0.0")

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
    exit_code = app.exec()

    logger.info("Application exiting with code: %d", exit_code)
    return exit_code


# Entry point when run as a script
if __name__ == "__main__":
    sys.exit(main())
