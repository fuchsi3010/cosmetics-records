# =============================================================================
# Cosmetics Records - Date Picker Component
# =============================================================================
# This module provides a date picker with calendar popup.
#
# Key Features:
#   - QLineEdit showing formatted date
#   - Calendar popup on click
#   - Today button for quick selection
#   - Date validation
#   - Signal emission on date change
#   - Localized date formatting
#
# Design Philosophy:
#   - Shows formatted date in input (e.g., "Dec 15, 2023")
#   - Calendar popup for visual date selection
#   - Today button for common use case
#   - Prevents invalid date entry
#
# Usage Example:
#   date_picker = DatePicker()
#   date_picker.date_changed.connect(handle_date_change)
#   date_picker.set_date(date.today())
# =============================================================================

import logging
from datetime import date
from typing import Optional

from PyQt6.QtCore import QDate, Qt, pyqtSignal

from cosmetics_records.utils.time_utils import format_date_localized
from PyQt6.QtWidgets import (
    QCalendarWidget,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# Configure module logger
logger = logging.getLogger(__name__)


class CalendarPopup(QWidget):
    """
    Calendar popup widget with date selection.

    This is a popup window containing a calendar and a Today button.

    Signals:
        date_selected(date): Emitted when a date is selected

    Attributes:
        calendar: The QCalendarWidget instance
    """

    # Signal emitted when date is selected
    date_selected = pyqtSignal(date)

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the calendar popup.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        # Make this a popup window
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)

        # Set up the UI
        self._init_ui()

    def _init_ui(self) -> None:
        """
        Initialize the user interface.

        Creates a calendar widget with a Today button.
        """
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Calendar widget
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.clicked.connect(self._on_date_clicked)
        layout.addWidget(self.calendar)

        # Today button
        today_btn = QPushButton("Today")
        today_btn.clicked.connect(self._select_today)
        layout.addWidget(today_btn)

    def _on_date_clicked(self, qdate: QDate) -> None:
        """
        Handle calendar date click.

        Args:
            qdate: The QDate that was clicked
        """
        # Convert QDate to Python date
        selected_date = date(qdate.year(), qdate.month(), qdate.day())

        # Emit signal
        self.date_selected.emit(selected_date)

        # Close popup
        self.close()

    def _select_today(self) -> None:
        """
        Select today's date and close the popup.
        """
        today = date.today()
        self.date_selected.emit(today)
        self.close()

    def set_selected_date(self, d: date) -> None:
        """
        Set the selected date in the calendar.

        Args:
            d: The date to select
        """
        qdate = QDate(d.year, d.month, d.day)
        self.calendar.setSelectedDate(qdate)


class DatePicker(QWidget):
    """
    Date picker with formatted display and calendar popup.

    This widget displays a formatted date in a read-only input field.
    When clicked, it shows a calendar popup for date selection.

    Signals:
        date_changed(date): Emitted when the selected date changes

    Attributes:
        _current_date: Currently selected date (or None if not set)
        _popup: Calendar popup widget
    """

    # Signal emitted when date changes
    date_changed = pyqtSignal(date)

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the date picker.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        # State tracking
        self._current_date: Optional[date] = None

        # Create popup (initially hidden)
        self._popup: Optional[CalendarPopup] = None

        # Set up the UI
        self._init_ui()

        logger.debug("DatePicker initialized")

    def _init_ui(self) -> None:
        """
        Initialize the user interface.

        Creates a read-only input field with a calendar button.
        """
        # Horizontal layout: [date display] [calendar button]
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Date display field (read-only)
        self._date_display = QLineEdit()
        self._date_display.setReadOnly(True)
        self._date_display.setPlaceholderText("Select date...")
        self._date_display.setCursor(Qt.CursorShape.PointingHandCursor)

        # Make the entire field clickable
        # Note: We use setattr to avoid mypy method-assign error
        setattr(
            self._date_display,
            "mousePressEvent",
            lambda event: self._show_calendar(),
        )

        layout.addWidget(self._date_display, stretch=1)

        # Calendar button
        self._calendar_btn = QPushButton("📅")  # Calendar emoji
        self._calendar_btn.setFixedWidth(40)
        self._calendar_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._calendar_btn.clicked.connect(self._show_calendar)
        layout.addWidget(self._calendar_btn)

    def _show_calendar(self) -> None:
        """
        Show the calendar popup.

        Creates the popup if it doesn't exist, positions it below the widget,
        and shows it.
        """
        # Create popup if it doesn't exist
        if self._popup is None:
            self._popup = CalendarPopup(self)
            self._popup.date_selected.connect(self._on_date_selected)

        # Set current date in calendar
        if self._current_date:
            self._popup.set_selected_date(self._current_date)
        else:
            # Default to today if no date selected
            self._popup.set_selected_date(date.today())

        # Position popup below this widget
        # WHY mapToGlobal: Converts widget-local coordinates to screen coordinates
        global_pos = self.mapToGlobal(self.rect().bottomLeft())
        self._popup.move(global_pos)

        # Show popup
        self._popup.show()

        logger.debug("Calendar popup shown")

    def _on_date_selected(self, selected_date: date) -> None:
        """
        Handle date selection from calendar popup.

        Args:
            selected_date: The date selected in the calendar
        """
        self.set_date(selected_date)

        # Emit signal
        self.date_changed.emit(selected_date)

        logger.debug(f"Date selected: {selected_date}")

    def get_date(self) -> Optional[date]:
        """
        Get the currently selected date.

        Returns:
            Optional[date]: The selected date, or None if no date is set
        """
        return self._current_date

    def set_date(self, d: Optional[date]) -> None:
        """
        Set the date programmatically.

        Args:
            d: The date to set, or None to clear

        Example:
            date_picker.set_date(date.today())
            date_picker.set_date(date(2023, 12, 25))
        """
        self._current_date = d

        # Update display
        if d:
            # Use localized date format (respects user's locale setting)
            formatted = format_date_localized(d)
            self._date_display.setText(formatted)
        else:
            self._date_display.clear()

    def clear(self) -> None:
        """
        Clear the selected date.

        This is a convenience method equivalent to set_date(None).
        """
        self.set_date(None)
