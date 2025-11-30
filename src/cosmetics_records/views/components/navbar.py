# =============================================================================
# Cosmetics Records - Collapsible Navigation Bar
# =============================================================================
# This module provides a collapsible side navigation bar with smooth animations.
#
# Key Features:
#   - Fixed position on left side of window
#   - Collapsible: 60px (icons only) or 180px (icons + labels)
#   - Smooth width animation using QPropertyAnimation
#   - Active item highlighting
#   - Unicode icons for visual clarity
#   - Signal emission for navigation
#   - Dynamic visibility (e.g., Client Detail only shown when viewing client)
#
# Design Philosophy:
#   - Icons provide visual anchors even when collapsed
#   - Animation makes the transition feel smooth and intentional
#   - Active highlighting helps users know where they are
#   - Settings at bottom follows common UI patterns
#
# Usage Example:
#   navbar = NavBar()
#   navbar.nav_clicked.connect(handle_navigation)
#   navbar.set_active("clients")
# =============================================================================

import logging
from typing import Optional

from PyQt6.QtCore import QPropertyAnimation, QSize, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from cosmetics_records.utils.localization import _

# Configure module logger
logger = logging.getLogger(__name__)


class NavBar(QFrame):
    """
    Collapsible navigation bar for the main application window.

    This widget provides a vertical navigation menu on the left side of the
    application. It can be collapsed to show only icons or expanded to show
    icons with text labels.

    Signals:
        nav_clicked(str): Emitted when a navigation item is clicked.
                         Passes the item ID (e.g., "clients", "inventory")

    Attributes:
        is_expanded: Whether the navbar is currently expanded
        active_item: The currently active navigation item ID
    """

    # Signal emitted when navigation item is clicked
    # Argument is the item ID (e.g., "clients", "inventory")
    nav_clicked = pyqtSignal(str)

    # Width constants
    WIDTH_COLLAPSED = 60  # Icon-only mode
    WIDTH_EXPANDED = 180  # Icon + text mode

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the navigation bar.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        # State tracking
        self.is_expanded = True  # Start expanded so users see all options
        self.active_item: Optional[str] = None

        # Store references to nav buttons for styling and visibility control
        self._nav_buttons: dict[str, QPushButton] = {}

        # Set up the UI
        self._init_ui()

        logger.debug("NavBar initialized")

    def _init_ui(self) -> None:
        """
        Initialize the user interface.

        Sets up the layout, creates all navigation buttons, and configures
        the initial appearance.
        """
        # Configure the frame itself
        self.setFixedWidth(self.WIDTH_EXPANDED)
        self.setFrameShape(QFrame.Shape.StyledPanel)

        # Main vertical layout - top to bottom
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Create navigation items
        # WHY this order: Most common tasks first, settings at bottom
        self._add_nav_button("clients", "☰", _("Clients"), layout)
        self._add_nav_button("client_detail", "☺", _("Client Detail"), layout)
        self._add_nav_button("inventory", "■", _("Inventory"), layout)
        self._add_nav_button("audit", "⟲", _("Audit Log"), layout)

        # Add spacer to push settings to bottom
        layout.addStretch()

        # Settings at bottom (common UI pattern)
        self._add_nav_button("settings", "⚙", _("Settings"), layout)

        # Toggle button at very bottom
        self._create_toggle_button(layout)

        # Hide client detail by default (only shown when viewing a client)
        self.set_item_visible("client_detail", False)

    def _add_nav_button(
        self, item_id: str, icon: str, label: str, layout: QVBoxLayout
    ) -> None:
        """
        Create and add a navigation button to the layout.

        Args:
            item_id: Unique identifier for this nav item (e.g., "clients")
            icon: Unicode character to use as icon
            label: Text label to show when expanded
            layout: Layout to add the button to

        Note:
            The button text will be set to just the icon when collapsed,
            or "icon label" when expanded.
        """
        button = QPushButton()
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setFixedHeight(50)
        button.setProperty("nav_item", True)  # CSS class for styling

        # Store the icon and label for use when toggling
        # WHY "nav_icon" not "icon": PyQt may confuse "icon" with built-in property
        button.setProperty("nav_icon", icon)
        button.setProperty("nav_label", label)

        # Set initial text (expanded mode)
        button.setText(f"{icon}  {label}")

        # Connect click handler
        # WHY lambda: Captures item_id for this specific button
        button.clicked.connect(lambda: self._on_nav_clicked(item_id))

        # Store reference for later access
        self._nav_buttons[item_id] = button

        # Add to layout
        layout.addWidget(button)

    def _create_toggle_button(self, layout: QVBoxLayout) -> None:
        """
        Create the expand/collapse toggle button.

        Args:
            layout: Layout to add the button to

        Note:
            This button uses ◀/▶ arrows to indicate the direction of expansion.
            The arrow direction changes based on current state.
        """
        self._toggle_btn = QPushButton("◀")
        self._toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle_btn.setFixedHeight(40)
        self._toggle_btn.setProperty("toggle_nav", True)  # CSS class

        # Connect to toggle handler
        self._toggle_btn.clicked.connect(self._toggle_expand)

        layout.addWidget(self._toggle_btn)

    def _on_nav_clicked(self, item_id: str) -> None:
        """
        Handle navigation button click.

        Args:
            item_id: ID of the clicked navigation item

        Note:
            This sets the active state and emits the nav_clicked signal
            for the main window to handle the actual navigation.
        """
        logger.debug(f"Navigation clicked: {item_id}")

        # Update active state
        self.set_active(item_id)

        # Emit signal for main window to handle
        self.nav_clicked.emit(item_id)

    def _toggle_expand(self) -> None:
        """
        Toggle between expanded and collapsed states with animation.

        This creates a smooth width animation that takes 200ms.
        The button text is updated after the animation completes.
        """
        # Determine target width
        target_width = self.WIDTH_COLLAPSED if self.is_expanded else self.WIDTH_EXPANDED

        # Create smooth animation
        # WHY QPropertyAnimation: Provides smooth, native-feeling transitions
        self._animation = QPropertyAnimation(self, b"maximumWidth")
        self._animation.setDuration(200)  # 200ms feels snappy but smooth
        self._animation.setStartValue(self.width())
        self._animation.setEndValue(target_width)

        # Update button text after animation completes
        self._animation.finished.connect(self._update_button_text)

        # Start animation
        self._animation.start()

        # Update state
        self.is_expanded = not self.is_expanded

        # Update toggle button arrow immediately
        self._toggle_btn.setText("▶" if self.is_expanded else "◀")

        logger.debug(f"NavBar toggled: expanded={self.is_expanded}")

    def _update_button_text(self) -> None:
        """
        Update button text based on expanded/collapsed state.

        When collapsed, shows only icons.
        When expanded, shows icons + labels.
        """
        for button in self._nav_buttons.values():
            icon = button.property("nav_icon")
            label = button.property("nav_label")

            if self.is_expanded:
                button.setText(f"{icon}  {label}")
            else:
                button.setText(str(icon) if icon else "")

    def set_active(self, item_id: str) -> None:
        """
        Set the active navigation item.

        This highlights the specified item and un-highlights all others.

        Args:
            item_id: ID of the item to make active

        Note:
            The active state is set via a property so it can be styled with QSS.
        """
        # Remove active state from all buttons
        for button_id, button in self._nav_buttons.items():
            is_active = button_id == item_id
            button.setProperty("active", is_active)
            # Force style refresh
            # WHY this is needed: Qt doesn't automatically refresh styles when
            # properties change, so we need to manually trigger a re-polish
            button.style().unpolish(button)
            button.style().polish(button)

        self.active_item = item_id
        logger.debug(f"Active nav item set to: {item_id}")

    def set_item_visible(self, item_id: str, visible: bool) -> None:
        """
        Show or hide a navigation item.

        This is used for conditional navigation items like "Client Detail"
        which should only be visible when viewing a specific client.

        Args:
            item_id: ID of the item to show/hide
            visible: True to show, False to hide

        Example:
            # Show client detail when viewing a client
            navbar.set_item_visible("client_detail", True)

            # Hide it when returning to clients list
            navbar.set_item_visible("client_detail", False)
        """
        if item_id in self._nav_buttons:
            self._nav_buttons[item_id].setVisible(visible)
            logger.debug(f"NavBar item '{item_id}' visibility set to {visible}")
        else:
            logger.warning(f"Attempted to set visibility of unknown item: {item_id}")

    def get_active_item(self) -> Optional[str]:
        """
        Get the currently active navigation item ID.

        Returns:
            Optional[str]: The active item ID, or None if no item is active
        """
        return self.active_item

    # Override sizeHint to prevent layout issues
    def sizeHint(self) -> QSize:
        """
        Provide a size hint for layout management.

        Returns:
            QSize: Recommended size for this widget
        """
        width = self.WIDTH_EXPANDED if self.is_expanded else self.WIDTH_COLLAPSED
        return QSize(width, 600)  # Height is flexible
