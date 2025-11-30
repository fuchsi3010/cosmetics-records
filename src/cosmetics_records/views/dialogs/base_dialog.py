# =============================================================================
# Cosmetics Records - Base Dialog Component
# =============================================================================
# This module provides a base class for modal dialogs with consistent styling.
#
# Key Features:
#   - Semi-transparent dark overlay behind dialog
#   - Centered content frame with rounded corners
#   - Title bar with close button
#   - Escape key to close
#   - Enter key to submit (if submit button focused)
#   - Helper for OK/Cancel button rows
#   - Abstract methods for subclasses
#
# Design Philosophy:
#   - Consistent dialog appearance across the application
#   - Accessible keyboard shortcuts (Esc to close, Enter to submit)
#   - Clean, modern appearance
#   - Easy to subclass for specific dialogs
#
# Usage Example:
#   class MyDialog(BaseDialog):
#       def _create_content(self, layout):
#           layout.addWidget(QLabel("Dialog content"))
#
#   dialog = MyDialog("My Dialog Title")
#   if dialog.exec() == QDialog.DialogCode.Accepted:
#       # User clicked OK
# =============================================================================

import logging
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QFrame,
)

# Configure module logger
logger = logging.getLogger(__name__)


class BaseDialog(QDialog):
    """
    Base class for modal dialogs with consistent styling.

    This class provides the common structure and functionality for all
    dialogs in the application. Subclasses should implement _create_content()
    to add their specific content.

    Attributes:
        _title: Dialog title text
        _content_layout: Layout where subclasses add content
    """

    def __init__(
        self,
        title: str,
        parent: Optional[QWidget] = None,
        width: int = 500,
        height: int = 400,
    ):
        """
        Initialize the base dialog.

        Args:
            title: Dialog title to display
            parent: Optional parent widget
            width: Dialog width in pixels (default: 500)
            height: Dialog height in pixels (default: 400)
        """
        super().__init__(parent)

        self._title = title

        # Configure dialog window
        self.setWindowTitle(title)
        self.setFixedSize(width, height)
        self.setModal(True)  # Block interaction with parent window

        # Remove default window frame - we'll create our own
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)

        # Set up the UI
        self._init_ui()

        logger.debug(f"BaseDialog initialized: {title}")

    def _init_ui(self) -> None:
        """
        Initialize the user interface.

        Creates the dialog structure:
        - Semi-transparent overlay background
        - Centered content frame
        - Title bar with close button
        - Content area (populated by subclasses)
        """
        # Main layout - fills entire dialog
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Content frame - rounded corners, elevated appearance
        self._content_frame = QFrame()
        self._content_frame.setProperty("dialog_frame", True)  # CSS class
        main_layout.addWidget(self._content_frame)

        # Content frame layout
        frame_layout = QVBoxLayout(self._content_frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.setSpacing(0)

        # Title bar
        self._create_title_bar(frame_layout)

        # Content area (populated by subclasses)
        self._content_layout = QVBoxLayout()
        self._content_layout.setContentsMargins(20, 20, 20, 20)
        self._content_layout.setSpacing(16)
        frame_layout.addLayout(self._content_layout)

        # Call subclass method to add specific content
        self._create_content(self._content_layout)

    def _create_title_bar(self, layout: QVBoxLayout) -> None:
        """
        Create the title bar with title text and close button.

        Args:
            layout: Layout to add the title bar to
        """
        # Title bar container
        title_bar = QWidget()
        title_bar.setProperty("dialog_title_bar", True)  # CSS class
        title_bar.setFixedHeight(50)
        layout.addWidget(title_bar)

        # Title bar layout
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(20, 0, 20, 0)
        title_layout.setSpacing(0)

        # Title label
        title_label = QLabel(self._title)
        title_label.setProperty("dialog_title", True)  # CSS class
        title_layout.addWidget(title_label)

        # Spacer
        title_layout.addStretch()

        # Close button
        close_btn = QPushButton("×")  # Multiplication sign looks like X
        close_btn.setFixedSize(30, 30)
        close_btn.setProperty("dialog_close", True)  # CSS class
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.reject)
        title_layout.addWidget(close_btn)

    def _create_content(self, layout: QVBoxLayout) -> None:
        """
        Create the dialog content.

        This is an abstract method that subclasses should override to add
        their specific content.

        Args:
            layout: Layout to add content to

        Note:
            Subclasses MUST implement this method to provide dialog content.
        """
        raise NotImplementedError("Subclasses must implement _create_content() method")

    def create_button_row(
        self,
        ok_text: str = "OK",
        cancel_text: str = "Cancel",
        show_cancel: bool = True,
    ) -> QHBoxLayout:
        """
        Create a standard OK/Cancel button row.

        This is a helper method for subclasses to easily create a button row
        at the bottom of their dialog.

        Args:
            ok_text: Text for the OK button (default: "OK")
            cancel_text: Text for the cancel button (default: "Cancel")
            show_cancel: Whether to show the cancel button (default: True)

        Returns:
            QHBoxLayout: Layout containing the buttons

        Example:
            def _create_content(self, layout):
                # Add your content widgets
                layout.addWidget(QLabel("Content"))

                # Add button row at bottom
                button_row = self.create_button_row("Save", "Cancel")
                layout.addLayout(button_row)
        """
        # Horizontal layout for buttons
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(8)

        # Spacer to push buttons to the right
        button_layout.addStretch()

        # Cancel button (optional)
        if show_cancel:
            cancel_btn = QPushButton(cancel_text)
            cancel_btn.setProperty("class", "secondary")  # Secondary styling
            cancel_btn.clicked.connect(self.reject)
            cancel_btn.setFixedWidth(100)
            button_layout.addWidget(cancel_btn)

        # OK button
        ok_btn = QPushButton(ok_text)
        ok_btn.clicked.connect(self.accept)
        ok_btn.setFixedWidth(100)
        ok_btn.setDefault(True)  # Enter key triggers this button
        button_layout.addWidget(ok_btn)

        return button_layout

    def keyPressEvent(self, event) -> None:
        """
        Handle key press events.

        Allows Escape key to close the dialog.

        Args:
            event: The key press event
        """
        # Escape key closes dialog
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            # Pass to base class for default handling
            super().keyPressEvent(event)

    def accept(self) -> None:
        """
        Accept the dialog (OK button clicked).

        Subclasses can override this to add validation or custom logic
        before closing.
        """
        logger.debug(f"Dialog accepted: {self._title}")
        super().accept()

    def reject(self) -> None:
        """
        Reject the dialog (Cancel button or X clicked).

        Subclasses can override this to add custom cleanup logic.
        """
        logger.debug(f"Dialog rejected: {self._title}")
        super().reject()


class SimpleMessageDialog(BaseDialog):
    """
    Simple message dialog with OK button.

    This is a concrete implementation of BaseDialog for displaying
    simple messages to the user.

    Example:
        dialog = SimpleMessageDialog("Success", "Record saved successfully!")
        dialog.exec()
    """

    def __init__(
        self,
        title: str,
        message: str,
        parent: Optional[QWidget] = None,
        width: int = 400,
        height: int = 200,
    ):
        """
        Initialize the message dialog.

        Args:
            title: Dialog title
            message: Message to display
            parent: Optional parent widget
            width: Dialog width (default: 400)
            height: Dialog height (default: 200)
        """
        self._message = message
        super().__init__(title, parent, width, height)

    def _create_content(self, layout: QVBoxLayout) -> None:
        """
        Create the message content.

        Args:
            layout: Layout to add content to
        """
        # Message label
        message_label = QLabel(self._message)
        message_label.setWordWrap(True)
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(message_label)

        # Add stretch to push button to bottom
        layout.addStretch()

        # OK button only (no cancel)
        button_row = self.create_button_row(show_cancel=False)
        layout.addLayout(button_row)


class ConfirmDialog(BaseDialog):
    """
    Confirmation dialog with OK/Cancel buttons.

    This is a concrete implementation of BaseDialog for getting
    user confirmation before proceeding with an action.

    Example:
        dialog = ConfirmDialog("Delete Client", "Are you sure you want to delete this client?")
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # User clicked OK
            delete_client()
    """

    def __init__(
        self,
        title: str,
        message: str,
        ok_text: str = "OK",
        cancel_text: str = "Cancel",
        parent: Optional[QWidget] = None,
        width: int = 400,
        height: int = 200,
    ):
        """
        Initialize the confirmation dialog.

        Args:
            title: Dialog title
            message: Confirmation message
            ok_text: Text for OK button (default: "OK")
            cancel_text: Text for cancel button (default: "Cancel")
            parent: Optional parent widget
            width: Dialog width (default: 400)
            height: Dialog height (default: 200)
        """
        self._message = message
        self._ok_text = ok_text
        self._cancel_text = cancel_text
        super().__init__(title, parent, width, height)

    def _create_content(self, layout: QVBoxLayout) -> None:
        """
        Create the confirmation content.

        Args:
            layout: Layout to add content to
        """
        # Message label
        message_label = QLabel(self._message)
        message_label.setWordWrap(True)
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(message_label)

        # Add stretch to push buttons to bottom
        layout.addStretch()

        # OK/Cancel buttons
        button_row = self.create_button_row(self._ok_text, self._cancel_text)
        layout.addLayout(button_row)
