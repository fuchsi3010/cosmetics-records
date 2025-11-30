# =============================================================================
# Cosmetics Records - View Handler Unit Tests
# =============================================================================
# This file contains unit tests for button handler functions in view classes.
# These tests verify that handlers correctly interact with controllers and
# databases when dialogs are confirmed.
#
# Test Structure:
#   - TestClientDetailCalculations: Pure function tests for age calculation
#   - TestClientDetailHandlers: Tests for ClientDetailView button handlers
#   - TestInventoryViewHandlers: Tests for InventoryView button handlers
#   - TestMainWindowHandlers: Tests for MainWindow button handlers
#
# Testing Strategy:
#   - Mock dialogs and database connections at source module
#   - Verify correct methods are called with correct arguments
#   - Test both success and cancellation scenarios
# =============================================================================

from datetime import date
from unittest.mock import MagicMock, patch

import pytest


# =============================================================================
# Age Calculation Tests
# =============================================================================


class TestClientDetailCalculations:
    """Tests for pure calculation functions in ClientDetailView."""

    def test_calculate_age_basic(self):
        """Test basic age calculation."""
        from cosmetics_records.views.clients.client_detail_view import ClientDetailView

        view = ClientDetailView.__new__(ClientDetailView)

        # Calculate age for someone born 30 years ago
        birth_date = date.today().replace(year=date.today().year - 30)
        age = view._calculate_age(birth_date)
        assert age == 30

    def test_calculate_age_birthday_passed_this_year(self):
        """Test age when birthday has passed this year."""
        from cosmetics_records.views.clients.client_detail_view import ClientDetailView

        view = ClientDetailView.__new__(ClientDetailView)

        # Birthday was in January, now it's November
        today = date.today()
        birth_date = date(today.year - 25, 1, 1)

        age = view._calculate_age(birth_date)
        # If today is after Jan 1, age should be 25
        if today >= date(today.year, 1, 1):
            assert age == 25

    def test_calculate_age_birthday_not_yet_this_year(self):
        """Test age when birthday hasn't happened yet this year."""
        from cosmetics_records.views.clients.client_detail_view import ClientDetailView

        view = ClientDetailView.__new__(ClientDetailView)

        # Birthday is December 31, so if today is before that, age is one less
        today = date.today()
        birth_date = date(today.year - 25, 12, 31)

        age = view._calculate_age(birth_date)
        # If today is before Dec 31, age should be 24 (birthday hasn't happened)
        if today < date(today.year, 12, 31):
            assert age == 24
        else:
            assert age == 25

    def test_calculate_age_exact_birthday(self):
        """Test age calculation on exact birthday."""
        from cosmetics_records.views.clients.client_detail_view import ClientDetailView

        view = ClientDetailView.__new__(ClientDetailView)

        # Today is the birthday
        today = date.today()
        birth_date = date(today.year - 30, today.month, today.day)

        age = view._calculate_age(birth_date)
        assert age == 30

    def test_calculate_age_leap_year_birthday(self):
        """Test age for someone born on Feb 29 (leap year)."""
        from cosmetics_records.views.clients.client_detail_view import ClientDetailView

        view = ClientDetailView.__new__(ClientDetailView)

        # Born on Feb 29, 2000 (leap year)
        birth_date = date(2000, 2, 29)

        # Calculate age based on today
        age = view._calculate_age(birth_date)

        # The age should be calculated correctly
        today = date.today()
        expected_age = today.year - 2000
        if (today.month, today.day) < (2, 29):
            expected_age -= 1

        assert age == expected_age


# =============================================================================
# Client Detail Handler Tests
# =============================================================================


class TestClientDetailHandlers:
    """Tests for ClientDetailView button handler functions."""

    def test_load_client_calls_controller(self):
        """Test that load_client fetches from database correctly."""
        from cosmetics_records.views.clients.client_detail_view import ClientDetailView

        view = ClientDetailView.__new__(ClientDetailView)
        view._client_id = None
        view._client_data = None
        view._update_ui = MagicMock()
        view._load_history = MagicMock()

        # Create mock client
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.first_name = "Jane"
        mock_client.last_name = "Doe"
        mock_client.date_of_birth = date(1990, 5, 15)
        mock_client.allergies = "Latex"
        mock_client.planned_treatment = "Facial"
        mock_client.notes = "VIP client"
        mock_client.full_name.return_value = "Jane Doe"

        # Mock controller
        mock_controller = MagicMock()
        mock_controller.get_client.return_value = mock_client

        # Patch at source - the actual module where the import comes from
        with patch(
            "cosmetics_records.database.connection.DatabaseConnection"
        ) as mock_db_class:
            mock_db = MagicMock()
            mock_db_class.return_value.__enter__ = MagicMock(return_value=mock_db)
            mock_db_class.return_value.__exit__ = MagicMock(return_value=False)

            with patch(
                "cosmetics_records.controllers.client_controller.ClientController",
                return_value=mock_controller,
            ):
                view.load_client(1)

        # Verify client data was loaded
        assert view._client_id == 1
        assert view._client_data is not None
        assert view._client_data["first_name"] == "Jane"
        assert view._client_data["last_name"] == "Doe"

        # Verify UI was updated
        view._update_ui.assert_called_once()
        view._load_history.assert_called_once()

    def test_load_client_handles_not_found(self):
        """Test load_client behavior when client doesn't exist."""
        from cosmetics_records.views.clients.client_detail_view import ClientDetailView

        view = ClientDetailView.__new__(ClientDetailView)
        view._client_id = None
        view._client_data = None
        view._update_ui = MagicMock()
        view._load_history = MagicMock()

        # Mock controller returning None
        mock_controller = MagicMock()
        mock_controller.get_client.return_value = None

        with patch(
            "cosmetics_records.database.connection.DatabaseConnection"
        ) as mock_db_class:
            mock_db = MagicMock()
            mock_db_class.return_value.__enter__ = MagicMock(return_value=mock_db)
            mock_db_class.return_value.__exit__ = MagicMock(return_value=False)

            with patch(
                "cosmetics_records.controllers.client_controller.ClientController",
                return_value=mock_controller,
            ):
                view.load_client(99999)

        # Client data should be None
        assert view._client_data is None

    def test_on_add_treatment_creates_treatment(self):
        """Test that _on_add_treatment creates a treatment record."""
        from cosmetics_records.views.clients.client_detail_view import ClientDetailView

        view = ClientDetailView.__new__(ClientDetailView)
        view._client_id = 1
        view._load_history = MagicMock()
        view.client_updated = MagicMock()
        view.client_updated.emit = MagicMock()

        # Mock dialog
        mock_dialog = MagicMock()
        mock_dialog.exec.return_value = True
        mock_dialog.get_treatment_data.return_value = {
            "client_id": 1,
            "date": date.today(),
            "notes": "Test treatment notes",
        }

        # Mock controller
        mock_controller = MagicMock()
        mock_controller.create_treatment.return_value = 1

        with patch(
            "cosmetics_records.views.dialogs.add_treatment_dialog.AddTreatmentDialog",
            return_value=mock_dialog,
        ):
            with patch(
                "cosmetics_records.database.connection.DatabaseConnection"
            ) as mock_db_class:
                mock_db = MagicMock()
                mock_db_class.return_value.__enter__ = MagicMock(return_value=mock_db)
                mock_db_class.return_value.__exit__ = MagicMock(return_value=False)

                with patch(
                    "cosmetics_records.controllers.treatment_controller.TreatmentController",
                    return_value=mock_controller,
                ):
                    view._on_add_treatment()

        # Verify treatment was created
        mock_controller.create_treatment.assert_called_once()
        treatment_arg = mock_controller.create_treatment.call_args[0][0]
        assert treatment_arg.client_id == 1
        assert treatment_arg.treatment_notes == "Test treatment notes"

        # Verify history was reloaded
        view._load_history.assert_called_once()
        view.client_updated.emit.assert_called_once()

    def test_on_add_treatment_dialog_cancelled(self):
        """Test that cancelling add treatment dialog doesn't create treatment."""
        from cosmetics_records.views.clients.client_detail_view import ClientDetailView

        view = ClientDetailView.__new__(ClientDetailView)
        view._client_id = 1
        view._load_history = MagicMock()

        # Mock dialog - cancelled
        mock_dialog = MagicMock()
        mock_dialog.exec.return_value = False

        with patch(
            "cosmetics_records.views.dialogs.add_treatment_dialog.AddTreatmentDialog",
            return_value=mock_dialog,
        ):
            view._on_add_treatment()

        # History should not be reloaded
        view._load_history.assert_not_called()

    def test_on_add_treatment_no_client_loaded(self):
        """Test that _on_add_treatment does nothing when no client is loaded."""
        from cosmetics_records.views.clients.client_detail_view import ClientDetailView

        view = ClientDetailView.__new__(ClientDetailView)
        view._client_id = None  # No client loaded

        # Should not raise, just return early
        view._on_add_treatment()

    def test_on_add_product_creates_product(self):
        """Test that _on_add_product creates a product record."""
        from cosmetics_records.views.clients.client_detail_view import ClientDetailView

        view = ClientDetailView.__new__(ClientDetailView)
        view._client_id = 1
        view._load_history = MagicMock()
        view.client_updated = MagicMock()
        view.client_updated.emit = MagicMock()

        # Mock dialog
        mock_dialog = MagicMock()
        mock_dialog.exec.return_value = True
        mock_dialog.get_product_record_data.return_value = {
            "client_id": 1,
            "date": date.today(),
            "product_text": "Test product text",
        }

        # Mock controllers
        mock_inv_controller = MagicMock()
        mock_inv_controller.get_all_names.return_value = ["Product A", "Product B"]
        mock_prod_controller = MagicMock()
        mock_prod_controller.create_product.return_value = 1

        with patch(
            "cosmetics_records.views.dialogs.add_product_record_dialog.AddProductRecordDialog",
            return_value=mock_dialog,
        ):
            with patch(
                "cosmetics_records.database.connection.DatabaseConnection"
            ) as mock_db_class:
                mock_db = MagicMock()
                mock_db_class.return_value.__enter__ = MagicMock(return_value=mock_db)
                mock_db_class.return_value.__exit__ = MagicMock(return_value=False)

                with patch(
                    "cosmetics_records.controllers.inventory_controller.InventoryController",
                    return_value=mock_inv_controller,
                ):
                    with patch(
                        "cosmetics_records.controllers.product_controller.ProductController",
                        return_value=mock_prod_controller,
                    ):
                        view._on_add_product()

        # Verify product was created
        mock_prod_controller.create_product.assert_called_once()
        product_arg = mock_prod_controller.create_product.call_args[0][0]
        assert product_arg.client_id == 1
        assert product_arg.product_text == "Test product text"

        # Verify history was reloaded
        view._load_history.assert_called_once()

    def test_on_planned_treatment_saved(self):
        """Test that auto-save updates planned treatment in database."""
        from cosmetics_records.views.clients.client_detail_view import ClientDetailView

        view = ClientDetailView.__new__(ClientDetailView)
        view._client_id = 1
        view.client_updated = MagicMock()
        view.client_updated.emit = MagicMock()

        # Mock client and controller
        mock_client = MagicMock()
        mock_controller = MagicMock()
        mock_controller.get_client.return_value = mock_client

        with patch(
            "cosmetics_records.database.connection.DatabaseConnection"
        ) as mock_db_class:
            mock_db = MagicMock()
            mock_db_class.return_value.__enter__ = MagicMock(return_value=mock_db)
            mock_db_class.return_value.__exit__ = MagicMock(return_value=False)

            with patch(
                "cosmetics_records.controllers.client_controller.ClientController",
                return_value=mock_controller,
            ):
                view._on_planned_treatment_saved("Updated planned treatment")

        # Verify client was updated
        assert mock_client.planned_treatment == "Updated planned treatment"
        mock_controller.update_client.assert_called_once_with(mock_client)
        view.client_updated.emit.assert_called_once()

    def test_on_personal_notes_saved(self):
        """Test that auto-save updates personal notes in database."""
        from cosmetics_records.views.clients.client_detail_view import ClientDetailView

        view = ClientDetailView.__new__(ClientDetailView)
        view._client_id = 1
        view.client_updated = MagicMock()
        view.client_updated.emit = MagicMock()

        # Mock client and controller
        mock_client = MagicMock()
        mock_controller = MagicMock()
        mock_controller.get_client.return_value = mock_client

        with patch(
            "cosmetics_records.database.connection.DatabaseConnection"
        ) as mock_db_class:
            mock_db = MagicMock()
            mock_db_class.return_value.__enter__ = MagicMock(return_value=mock_db)
            mock_db_class.return_value.__exit__ = MagicMock(return_value=False)

            with patch(
                "cosmetics_records.controllers.client_controller.ClientController",
                return_value=mock_controller,
            ):
                view._on_personal_notes_saved("Updated notes")

        # Verify client was updated
        assert mock_client.notes == "Updated notes"
        mock_controller.update_client.assert_called_once_with(mock_client)


# =============================================================================
# Inventory View Handler Tests
# =============================================================================


class TestInventoryViewHandlers:
    """Tests for InventoryView button handler functions."""

    def test_on_add_item_creates_item(self):
        """Test that _on_add_item creates an inventory item."""
        from cosmetics_records.views.inventory.inventory_view import InventoryView

        view = InventoryView.__new__(InventoryView)
        view.refresh = MagicMock()
        view.item_updated = MagicMock()
        view.item_updated.emit = MagicMock()

        # Mock dialog
        mock_dialog = MagicMock()
        mock_dialog.exec.return_value = True
        mock_dialog.get_item_data.return_value = {
            "name": "New Test Item",
            "description": "Test description",
            "capacity": 50.0,
            "unit": "ml",
        }

        # Mock controller
        mock_controller = MagicMock()
        mock_controller.create_item.return_value = 1

        with patch(
            "cosmetics_records.views.dialogs.add_inventory_dialog.AddInventoryDialog",
            return_value=mock_dialog,
        ):
            with patch(
                "cosmetics_records.database.connection.DatabaseConnection"
            ) as mock_db_class:
                mock_db = MagicMock()
                mock_db_class.return_value.__enter__ = MagicMock(return_value=mock_db)
                mock_db_class.return_value.__exit__ = MagicMock(return_value=False)

                with patch(
                    "cosmetics_records.controllers.inventory_controller.InventoryController",
                    return_value=mock_controller,
                ):
                    view._on_add_item()

        # Verify item was created
        mock_controller.create_item.assert_called_once()
        item_arg = mock_controller.create_item.call_args[0][0]
        assert item_arg.name == "New Test Item"
        assert item_arg.capacity == 50.0

        # Verify refresh was called
        view.refresh.assert_called_once()
        view.item_updated.emit.assert_called_once()

    def test_on_add_item_dialog_cancelled(self):
        """Test that cancelling add item dialog doesn't create item."""
        from cosmetics_records.views.inventory.inventory_view import InventoryView

        view = InventoryView.__new__(InventoryView)
        view.refresh = MagicMock()

        # Mock dialog - cancelled
        mock_dialog = MagicMock()
        mock_dialog.exec.return_value = False

        with patch(
            "cosmetics_records.views.dialogs.add_inventory_dialog.AddInventoryDialog",
            return_value=mock_dialog,
        ):
            view._on_add_item()

        # Refresh should not be called
        view.refresh.assert_not_called()

    def test_on_item_clicked_updates_item(self):
        """Test that clicking an item and editing updates the database."""
        from cosmetics_records.views.inventory.inventory_view import InventoryView

        view = InventoryView.__new__(InventoryView)
        view.refresh = MagicMock()
        view.item_updated = MagicMock()
        view.item_updated.emit = MagicMock()

        # Mock existing item
        mock_item = MagicMock()
        mock_item.id = 1

        # Mock dialog
        mock_dialog = MagicMock()
        mock_dialog.exec.return_value = True
        mock_dialog.get_item_data.return_value = {
            "name": "Updated Item Name",
            "description": "Updated description",
            "capacity": 100.0,
            "unit": "g",
        }

        # Mock controller
        mock_controller = MagicMock()
        mock_controller.get_item.return_value = mock_item

        with patch(
            "cosmetics_records.views.dialogs.edit_inventory_dialog.EditInventoryDialog",
            return_value=mock_dialog,
        ):
            with patch(
                "cosmetics_records.database.connection.DatabaseConnection"
            ) as mock_db_class:
                mock_db = MagicMock()
                mock_db_class.return_value.__enter__ = MagicMock(return_value=mock_db)
                mock_db_class.return_value.__exit__ = MagicMock(return_value=False)

                with patch(
                    "cosmetics_records.controllers.inventory_controller.InventoryController",
                    return_value=mock_controller,
                ):
                    view._on_item_clicked(1)

        # Verify item was updated
        assert mock_item.name == "Updated Item Name"
        assert mock_item.capacity == 100.0
        assert mock_item.unit == "g"
        mock_controller.update_item.assert_called_once_with(mock_item)

        # Verify refresh was called
        view.refresh.assert_called_once()

    def test_on_item_clicked_item_not_found(self):
        """Test that clicking non-existent item doesn't crash."""
        from cosmetics_records.views.inventory.inventory_view import InventoryView

        view = InventoryView.__new__(InventoryView)
        view.refresh = MagicMock()

        # Mock controller returning None
        mock_controller = MagicMock()
        mock_controller.get_item.return_value = None

        with patch(
            "cosmetics_records.database.connection.DatabaseConnection"
        ) as mock_db_class:
            mock_db = MagicMock()
            mock_db_class.return_value.__enter__ = MagicMock(return_value=mock_db)
            mock_db_class.return_value.__exit__ = MagicMock(return_value=False)

            with patch(
                "cosmetics_records.controllers.inventory_controller.InventoryController",
                return_value=mock_controller,
            ):
                view._on_item_clicked(99999)

        # Refresh should not be called
        view.refresh.assert_not_called()

    def test_load_more_items_fetches_from_database(self):
        """Test that _load_more_items fetches items from database."""
        from cosmetics_records.views.inventory.inventory_view import InventoryView

        view = InventoryView.__new__(InventoryView)
        view._loading = False
        view._loaded_items = []
        view._current_search = ""
        view._current_filter = "All"
        view._has_more = True
        view.add_items = MagicMock()
        view.ITEMS_PER_PAGE = 20

        # Create mock items
        mock_items = [
            MagicMock(id=i, name=f"Item {i}", capacity=10.0, unit="ml", description="")
            for i in range(5)
        ]

        # Mock controller
        mock_controller = MagicMock()
        mock_controller.get_all_items.return_value = mock_items

        with patch(
            "cosmetics_records.database.connection.DatabaseConnection"
        ) as mock_db_class:
            mock_db = MagicMock()
            mock_db_class.return_value.__enter__ = MagicMock(return_value=mock_db)
            mock_db_class.return_value.__exit__ = MagicMock(return_value=False)

            with patch(
                "cosmetics_records.controllers.inventory_controller.InventoryController",
                return_value=mock_controller,
            ):
                view._load_more_items()

        # Verify add_items was called with items
        view.add_items.assert_called_once()
        items_arg = view.add_items.call_args[0][0]
        assert len(items_arg) == 5

    def test_load_more_items_with_search(self):
        """Test that _load_more_items respects search filter."""
        from cosmetics_records.views.inventory.inventory_view import InventoryView

        view = InventoryView.__new__(InventoryView)
        view._loading = False
        view._loaded_items = []
        view._current_search = "Serum"
        view._current_filter = "All"
        view._has_more = True
        view.add_items = MagicMock()
        view.ITEMS_PER_PAGE = 20

        # Create mock items
        mock_items = [
            MagicMock(id=1, name="Serum A", capacity=10.0, unit="ml", description=""),
            MagicMock(id=2, name="Serum B", capacity=10.0, unit="ml", description=""),
        ]

        # Mock controller
        mock_controller = MagicMock()
        mock_controller.search_inventory.return_value = mock_items

        with patch(
            "cosmetics_records.database.connection.DatabaseConnection"
        ) as mock_db_class:
            mock_db = MagicMock()
            mock_db_class.return_value.__enter__ = MagicMock(return_value=mock_db)
            mock_db_class.return_value.__exit__ = MagicMock(return_value=False)

            with patch(
                "cosmetics_records.controllers.inventory_controller.InventoryController",
                return_value=mock_controller,
            ):
                view._load_more_items()

        # Verify search_inventory was called
        mock_controller.search_inventory.assert_called_once_with("Serum", limit=20)

        # Verify items were returned
        view.add_items.assert_called_once()
        items_arg = view.add_items.call_args[0][0]
        assert len(items_arg) == 2


# =============================================================================
# Main Window Handler Tests
# =============================================================================


class TestMainWindowHandlers:
    """Tests for MainWindow button handler functions."""

    def test_on_add_client_clicked_creates_client(self):
        """Test that _on_add_client_clicked creates a client in database."""
        from cosmetics_records.app import MainWindow

        window = MainWindow.__new__(MainWindow)
        window.views = {"clients": MagicMock()}
        window.views["clients"].refresh = MagicMock()

        # Mock dialog
        mock_dialog = MagicMock()
        mock_dialog.exec.return_value = True
        mock_dialog.get_client_data.return_value = {
            "first_name": "Test",
            "last_name": "Client",
            "email": "test@example.com",
            "phone": None,
            "address": None,
            "date_of_birth": date(1990, 5, 15),
            "allergies": None,
            "tags": ["Test"],
        }

        # Mock controller
        mock_controller = MagicMock()
        mock_controller.create_client.return_value = 1

        with patch(
            "cosmetics_records.views.dialogs.add_client_dialog.AddClientDialog",
            return_value=mock_dialog,
        ):
            with patch(
                "cosmetics_records.database.connection.DatabaseConnection"
            ) as mock_db_class:
                mock_db = MagicMock()
                mock_db_class.return_value.__enter__ = MagicMock(return_value=mock_db)
                mock_db_class.return_value.__exit__ = MagicMock(return_value=False)

                with patch(
                    "cosmetics_records.controllers.client_controller.ClientController",
                    return_value=mock_controller,
                ):
                    window._on_add_client_clicked()

        # Verify client was created
        mock_controller.create_client.assert_called_once()
        client_arg = mock_controller.create_client.call_args[0][0]
        assert client_arg.first_name == "Test"
        assert client_arg.last_name == "Client"

        # Verify list was refreshed
        window.views["clients"].refresh.assert_called_once()

    def test_on_add_client_clicked_dialog_cancelled(self):
        """Test that cancelling add client dialog doesn't create client."""
        from cosmetics_records.app import MainWindow

        window = MainWindow.__new__(MainWindow)
        window.views = {"clients": MagicMock()}

        # Mock dialog - cancelled
        mock_dialog = MagicMock()
        mock_dialog.exec.return_value = False

        with patch(
            "cosmetics_records.views.dialogs.add_client_dialog.AddClientDialog",
            return_value=mock_dialog,
        ):
            window._on_add_client_clicked()

        # Refresh should not be called
        window.views["clients"].refresh.assert_not_called()

    def test_show_client_detail_loads_client(self):
        """Test that show_client_detail loads the client and navigates."""
        from cosmetics_records.app import MainWindow

        window = MainWindow.__new__(MainWindow)
        window.views = {"client_detail": MagicMock()}
        window.navbar = MagicMock()
        window._navigate_to = MagicMock()

        # Mock client
        mock_client = MagicMock()
        mock_client.full_name.return_value = "Jane Doe"

        # Mock controller
        mock_controller = MagicMock()
        mock_controller.get_client.return_value = mock_client

        with patch(
            "cosmetics_records.database.connection.DatabaseConnection"
        ) as mock_db_class:
            mock_db = MagicMock()
            mock_db_class.return_value.__enter__ = MagicMock(return_value=mock_db)
            mock_db_class.return_value.__exit__ = MagicMock(return_value=False)

            with patch(
                "cosmetics_records.controllers.client_controller.ClientController",
                return_value=mock_controller,
            ):
                window.show_client_detail(1)

        # Verify client was loaded
        window.views["client_detail"].load_client.assert_called_once_with(1)

        # Verify navbar was updated with client name
        window.navbar.set_item_label.assert_called_once_with("client_detail", "Jane Doe")
        window.navbar.set_item_visible.assert_called_once_with("client_detail", True)

        # Verify navigation happened
        window._navigate_to.assert_called_once_with("client_detail")


# =============================================================================
# Load History Tests
# =============================================================================


class TestLoadHistory:
    """Tests for history loading functionality."""

    def test_load_history_fetches_treatments_and_products(self):
        """Test that _load_history fetches both treatments and products."""
        from cosmetics_records.views.clients.client_detail_view import ClientDetailView

        view = ClientDetailView.__new__(ClientDetailView)
        view._client_id = 1
        view._treatment_history = MagicMock()
        view._product_history = MagicMock()

        # Create mock treatments
        mock_treatment = MagicMock()
        mock_treatment.id = 1
        mock_treatment.treatment_date = date.today()
        mock_treatment.treatment_notes = "Test treatment"
        mock_treatment.created_at = None
        mock_treatment.updated_at = None

        # Create mock product
        mock_product = MagicMock()
        mock_product.id = 1
        mock_product.product_date = date.today()
        mock_product.product_text = "Test product"
        mock_product.created_at = None
        mock_product.updated_at = None

        # Mock controllers
        mock_treatment_controller = MagicMock()
        mock_treatment_controller.get_treatments_for_client.return_value = [mock_treatment]
        mock_product_controller = MagicMock()
        mock_product_controller.get_products_for_client.return_value = [mock_product]

        with patch(
            "cosmetics_records.database.connection.DatabaseConnection"
        ) as mock_db_class:
            mock_db = MagicMock()
            mock_db_class.return_value.__enter__ = MagicMock(return_value=mock_db)
            mock_db_class.return_value.__exit__ = MagicMock(return_value=False)

            with patch(
                "cosmetics_records.controllers.treatment_controller.TreatmentController",
                return_value=mock_treatment_controller,
            ):
                with patch(
                    "cosmetics_records.controllers.product_controller.ProductController",
                    return_value=mock_product_controller,
                ):
                    view._load_history()

        # Verify both histories were cleared and populated
        view._treatment_history.clear_items.assert_called_once()
        view._product_history.clear_items.assert_called_once()
        view._treatment_history.add_items.assert_called_once()
        view._product_history.add_items.assert_called_once()

        # Verify correct items were passed
        treatment_items = view._treatment_history.add_items.call_args[0][0]
        assert len(treatment_items) == 1
        assert treatment_items[0]["notes"] == "Test treatment"

        product_items = view._product_history.add_items.call_args[0][0]
        assert len(product_items) == 1
        assert product_items[0]["notes"] == "Test product"


# =============================================================================
# AutoSaveTextEdit Tests
# =============================================================================


class TestAutoSaveTextEdit:
    """Tests for AutoSaveTextEdit widget."""

    def test_autosave_delay_constant(self):
        """Test that autosave delay is 1 second (1000ms)."""
        from cosmetics_records.views.clients.client_detail_view import AutoSaveTextEdit

        assert AutoSaveTextEdit.AUTOSAVE_DELAY == 1000
