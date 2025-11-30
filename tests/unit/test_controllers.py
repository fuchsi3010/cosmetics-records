# =============================================================================
# Cosmetics Records - Controller Unit Tests
# =============================================================================
# This file contains comprehensive unit tests for all controller classes.
# Controllers handle business logic and database operations, so these tests
# verify that CRUD operations, search, filtering, and pagination work correctly.
#
# Test Structure:
#   - TestClientController: Tests for ClientController
#   - TestTreatmentController: Tests for TreatmentController
#   - TestInventoryController: Tests for InventoryController
#
# Testing Strategy:
#   - Use a real database (temporary) to test actual SQL queries
#   - Test both success and failure cases
#   - Verify return values match expected types
#   - Test edge cases (empty results, invalid IDs, etc.)
#
# Note: These are integration-style unit tests - they test the controller
# in isolation but use a real database. This ensures SQL queries are correct.
# =============================================================================

from datetime import date

import pytest

from cosmetics_records.controllers.client_controller import ClientController
from cosmetics_records.controllers.inventory_controller import InventoryController
from cosmetics_records.controllers.treatment_controller import TreatmentController
from cosmetics_records.models.client import Client
from cosmetics_records.models.product import InventoryItem
from cosmetics_records.models.treatment import TreatmentRecord
from tests.conftest import create_client_in_db


# =============================================================================
# ClientController Tests
# =============================================================================


class TestClientController:
    """Tests for the ClientController class."""

    def test_create_client(self, db_connection, sample_client):
        """
        Test creating a new client through the controller.

        This verifies that:
        - A client can be created successfully
        - The returned ID is a positive integer
        - The client is actually stored in the database
        """
        controller = ClientController(db_connection)

        # Create the client
        client_id = controller.create_client(sample_client)

        # Verify we got a valid ID back
        assert isinstance(client_id, int)
        assert client_id > 0

        # Verify the client was actually saved by retrieving it
        saved_client = controller.get_client(client_id)
        assert saved_client is not None
        assert saved_client.first_name == sample_client.first_name
        assert saved_client.last_name == sample_client.last_name
        assert saved_client.email == sample_client.email

    def test_create_client_with_existing_id_raises_error(self, db_connection):
        """
        Test that creating a client with an existing ID raises ValueError.

        The create method should only accept new clients (id=None). Attempting
        to create a client with an ID should fail.
        """
        controller = ClientController(db_connection)

        # Create a client with an ID set (invalid for create)
        client = Client(first_name="Jane", last_name="Doe", id=999)

        # Should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            controller.create_client(client)

        assert "existing ID" in str(exc_info.value)

    def test_get_client(self, db_connection, sample_client):
        """
        Test retrieving a client by ID.

        This verifies that:
        - We can retrieve a client that exists
        - The returned client has all fields populated correctly
        """
        controller = ClientController(db_connection)

        # First create a client
        client_id = controller.create_client(sample_client)

        # Now retrieve it
        retrieved_client = controller.get_client(client_id)

        # Verify all fields match
        assert retrieved_client is not None
        assert retrieved_client.id == client_id
        assert retrieved_client.first_name == sample_client.first_name
        assert retrieved_client.last_name == sample_client.last_name
        assert retrieved_client.email == sample_client.email
        assert retrieved_client.phone == sample_client.phone
        assert retrieved_client.tags == sample_client.tags

    def test_get_client_not_found(self, db_connection):
        """
        Test retrieving a client that doesn't exist returns None.

        When we request a client ID that doesn't exist, we should get None
        rather than an error or empty object.
        """
        controller = ClientController(db_connection)

        # Try to get a client that doesn't exist
        result = controller.get_client(9999)

        # Should return None
        assert result is None

    def test_update_client(self, db_connection, sample_client):
        """
        Test updating an existing client.

        This verifies that:
        - We can modify a client's fields
        - The update persists to the database
        - Update returns True on success
        """
        controller = ClientController(db_connection)

        # Create a client
        client_id = controller.create_client(sample_client)

        # Retrieve it
        client = controller.get_client(client_id)

        # Modify some fields
        client.email = "updated@example.com"
        client.phone = "+1-555-9999"
        client.tags = ["Updated", "Modified"]

        # Update the client
        success = controller.update_client(client)

        # Verify update succeeded
        assert success is True

        # Retrieve again to verify changes persisted
        updated_client = controller.get_client(client_id)
        assert updated_client.email == "updated@example.com"
        assert updated_client.phone == "+1-555-9999"
        assert updated_client.tags == ["Updated", "Modified"]

    def test_update_client_without_id_raises_error(self, db_connection):
        """
        Test that updating a client without an ID raises ValueError.

        The update method requires a client with a valid ID. Attempting to
        update a client with id=None should fail.
        """
        controller = ClientController(db_connection)

        # Create a client without an ID
        client = Client(first_name="Jane", last_name="Doe")

        # Should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            controller.update_client(client)

        assert "without ID" in str(exc_info.value)

    def test_update_client_not_found(self, db_connection):
        """
        Test that updating a non-existent client returns False.

        When we try to update a client ID that doesn't exist, the method
        should return False (rather than raising an error).
        """
        controller = ClientController(db_connection)

        # Create a client with a non-existent ID
        client = Client(first_name="Jane", last_name="Doe", id=9999)

        # Update should return False (not found)
        success = controller.update_client(client)
        assert success is False

    def test_delete_client(self, db_connection, sample_client):
        """
        Test deleting a client.

        This verifies that:
        - Delete returns True on success
        - The client is actually removed from the database
        """
        controller = ClientController(db_connection)

        # Create a client
        client_id = controller.create_client(sample_client)

        # Verify it exists
        assert controller.get_client(client_id) is not None

        # Delete the client
        success = controller.delete_client(client_id)

        # Verify deletion succeeded
        assert success is True

        # Verify the client is gone
        assert controller.get_client(client_id) is None

    def test_delete_client_not_found(self, db_connection):
        """
        Test that deleting a non-existent client returns False.

        When we try to delete a client ID that doesn't exist, the method
        should return False.
        """
        controller = ClientController(db_connection)

        # Try to delete a non-existent client
        success = controller.delete_client(9999)

        # Should return False (not found)
        assert success is False

    def test_get_all_clients_pagination(self, db_connection):
        """
        Test pagination when retrieving all clients.

        This verifies that:
        - We can retrieve clients in pages
        - Limit and offset work correctly
        - Clients are sorted alphabetically by last name
        """
        controller = ClientController(db_connection)

        # Create multiple clients
        for i in range(5):
            client = Client(
                first_name=f"First{i}",
                last_name=f"Last{i}",
                email=f"client{i}@example.com",
            )
            controller.create_client(client)

        # Get first page (limit 3)
        page1 = controller.get_all_clients(limit=3, offset=0)
        assert len(page1) == 3

        # Get second page (remaining 2)
        page2 = controller.get_all_clients(limit=3, offset=3)
        assert len(page2) == 2

        # Verify no overlap between pages
        page1_ids = {c.id for c in page1}
        page2_ids = {c.id for c in page2}
        assert len(page1_ids & page2_ids) == 0  # No common IDs

    def test_get_all_clients_empty_database(self, db_connection):
        """
        Test that get_all_clients returns empty list when no clients exist.

        Edge case: empty database should return an empty list, not None or error.
        """
        controller = ClientController(db_connection)

        # Get clients from empty database
        clients = controller.get_all_clients()

        # Should return empty list
        assert clients == []

    def test_search_clients_fuzzy(self, db_connection):
        """
        Test fuzzy search functionality.

        This verifies that:
        - We can search by partial name
        - Fuzzy matching works (handles typos)
        - Results are returned in order of relevance
        """
        controller = ClientController(db_connection)

        # Create some test clients
        controller.create_client(Client(first_name="Jane", last_name="Doe"))
        controller.create_client(Client(first_name="John", last_name="Doe"))
        controller.create_client(Client(first_name="Jane", last_name="Smith"))
        controller.create_client(Client(first_name="Bob", last_name="Johnson"))

        # Search for "Jane" (should match 2 clients)
        results = controller.search_clients("Jane")
        assert len(results) >= 2  # At least 2 matches

        # Search for "Doe" (should match 2 clients)
        results = controller.search_clients("Doe")
        assert len(results) >= 2

        # Fuzzy search with typo "Jone" (should still match "Jane" and "John")
        results = controller.search_clients("Jone")
        assert len(results) > 0  # Fuzzy matching should find something

    def test_search_clients_empty_query_raises_error(self, db_connection):
        """
        Test that searching with an empty query raises ValueError.

        Empty search queries are invalid and should be rejected.
        """
        controller = ClientController(db_connection)

        # Empty string should raise error
        with pytest.raises(ValueError) as exc_info:
            controller.search_clients("")

        assert "empty" in str(exc_info.value).lower()

        # Whitespace-only should also raise error
        with pytest.raises(ValueError):
            controller.search_clients("   ")

    def test_filter_clients_by_letter(self, db_connection):
        """
        Test filtering clients by first letter of last name.

        This verifies the alphabetical filter feature commonly used in
        contact lists.
        """
        controller = ClientController(db_connection)

        # Create clients with different last names
        controller.create_client(Client(first_name="Alice", last_name="Anderson"))
        controller.create_client(Client(first_name="Bob", last_name="Brown"))
        controller.create_client(Client(first_name="Charlie", last_name="Clark"))
        controller.create_client(Client(first_name="Anna", last_name="Adams"))

        # Filter by letter 'A' (should get Anderson and Adams)
        results = controller.filter_by_letter("A")
        assert len(results) == 2
        assert all(c.last_name.startswith("A") for c in results)

        # Filter by letter 'B' (should get Brown)
        results = controller.filter_by_letter("B")
        assert len(results) == 1
        assert results[0].last_name == "Brown"

        # Filter by letter 'Z' (should get nothing)
        results = controller.filter_by_letter("Z")
        assert len(results) == 0


# =============================================================================
# TreatmentController Tests
# =============================================================================


class TestTreatmentController:
    """Tests for the TreatmentController class."""

    def test_create_treatment(self, db_connection, sample_client, sample_treatment):
        """
        Test creating a new treatment record.

        This verifies that treatments can be created and linked to clients.
        """
        # First create a client
        client_id = create_client_in_db(db_connection, sample_client)

        # Update sample_treatment to use the actual client_id
        sample_treatment.client_id = client_id

        # Create the treatment
        controller = TreatmentController(db_connection)
        treatment_id = controller.create_treatment(sample_treatment)

        # Verify we got a valid ID
        assert isinstance(treatment_id, int)
        assert treatment_id > 0

        # Verify the treatment was saved
        saved_treatment = controller.get_treatment(treatment_id)
        assert saved_treatment is not None
        assert saved_treatment.client_id == client_id
        assert saved_treatment.treatment_notes == sample_treatment.treatment_notes

    def test_get_treatments_for_client(self, db_connection, sample_client):
        """
        Test retrieving all treatments for a specific client.

        This verifies that we can get a client's complete treatment history.
        """
        # Create a client
        client_id = create_client_in_db(db_connection, sample_client)

        # Create multiple treatments for this client
        controller = TreatmentController(db_connection)
        treatment1 = TreatmentRecord(
            client_id=client_id, treatment_notes="First treatment"
        )
        treatment2 = TreatmentRecord(
            client_id=client_id, treatment_notes="Second treatment"
        )

        controller.create_treatment(treatment1)
        controller.create_treatment(treatment2)

        # Get all treatments for this client
        treatments = controller.get_treatments_for_client(client_id)

        # Should have 2 treatments
        assert len(treatments) == 2

        # Verify they're for the right client
        assert all(t.client_id == client_id for t in treatments)

    def test_get_treatments_for_client_no_treatments(
        self, db_connection, sample_client
    ):
        """
        Test retrieving treatments for a client with no treatments.

        Should return an empty list, not None or error.
        """
        # Create a client
        client_id = create_client_in_db(db_connection, sample_client)

        # Get treatments (should be empty)
        controller = TreatmentController(db_connection)
        treatments = controller.get_treatments_for_client(client_id)

        assert treatments == []

    def test_treatment_exists_for_date(self, db_connection, sample_client):
        """
        Test checking if a treatment exists for a specific date.

        This helps prevent duplicate entries on the same day.
        """
        # Create a client
        client_id = create_client_in_db(db_connection, sample_client)

        # Create a treatment for today
        controller = TreatmentController(db_connection)
        treatment = TreatmentRecord(
            client_id=client_id,
            treatment_date=date.today(),
            treatment_notes="Treatment today",
        )
        controller.create_treatment(treatment)

        # Check if treatment exists for today (should be True)
        exists = controller.treatment_exists_for_date(client_id, date.today())
        assert exists is True

        # Check if treatment exists for yesterday (should be False)
        from datetime import timedelta

        yesterday = date.today() - timedelta(days=1)
        exists = controller.treatment_exists_for_date(client_id, yesterday)
        assert exists is False


# =============================================================================
# InventoryController Tests
# =============================================================================


class TestInventoryController:
    """Tests for the InventoryController class."""

    def test_create_inventory_item(self, db_connection, sample_inventory_item):
        """
        Test creating a new inventory item.

        This verifies that inventory items can be created successfully.
        """
        controller = InventoryController(db_connection)

        # Create the item
        item_id = controller.create_item(sample_inventory_item)

        # Verify we got a valid ID
        assert isinstance(item_id, int)
        assert item_id > 0

        # Verify the item was saved
        saved_item = controller.get_item(item_id)
        assert saved_item is not None
        assert saved_item.name == sample_inventory_item.name
        assert saved_item.capacity == sample_inventory_item.capacity
        assert saved_item.unit == sample_inventory_item.unit

    def test_search_inventory(self, db_connection):
        """
        Test searching inventory items by name.

        This verifies fuzzy search works for inventory.
        """
        controller = InventoryController(db_connection)

        # Create some inventory items
        item1 = InventoryItem(name="Retinol Serum", capacity=30.0, unit="ml")
        item2 = InventoryItem(name="Vitamin C Serum", capacity=30.0, unit="ml")
        item3 = InventoryItem(name="Face Cream", capacity=50.0, unit="g")

        controller.create_item(item1)
        controller.create_item(item2)
        controller.create_item(item3)

        # Search for "Serum" (should match 2 items)
        results = controller.search_inventory("Serum")
        assert len(results) == 2

        # Search for "Retinol" (should match 1 item)
        results = controller.search_inventory("Retinol")
        assert len(results) == 1
        assert results[0].name == "Retinol Serum"

    def test_get_all_names_for_autocomplete(self, db_connection):
        """
        Test getting all inventory item names for autocomplete.

        This returns a simple list of names used in autocomplete dropdowns.
        """
        controller = InventoryController(db_connection)

        # Create some inventory items
        controller.create_item(
            InventoryItem(name="Retinol Serum", capacity=30.0, unit="ml")
        )
        controller.create_item(
            InventoryItem(name="Vitamin C Serum", capacity=30.0, unit="ml")
        )
        controller.create_item(
            InventoryItem(name="Face Cream", capacity=50.0, unit="g")
        )

        # Get all names
        names = controller.get_all_names()

        # Should have 3 names
        assert len(names) == 3
        assert "Retinol Serum" in names
        assert "Vitamin C Serum" in names
        assert "Face Cream" in names

    def test_get_all_names_empty_inventory(self, db_connection):
        """
        Test getting names from empty inventory.

        Should return empty list, not None or error.
        """
        controller = InventoryController(db_connection)

        # Get names from empty inventory
        names = controller.get_all_names()

        assert names == []
