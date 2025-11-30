# =============================================================================
# Cosmetics Records - Model Unit Tests
# =============================================================================
# This file contains comprehensive unit tests for all Pydantic models in the
# application. These tests verify:
#   - Model validation rules work correctly
#   - Helper methods produce expected outputs
#   - Edge cases are handled properly
#   - Invalid data is rejected with appropriate errors
#
# Test Structure:
#   - TestClient: Tests for the Client model
#   - TestTreatmentRecord: Tests for the TreatmentRecord model
#   - TestProductRecord: Tests for the ProductRecord model
#   - TestInventoryItem: Tests for the InventoryItem model
#   - TestAuditLog: Tests for the AuditLog model
#
# Testing Philosophy:
#   - Each test focuses on ONE specific behavior
#   - Test both success cases (valid data) and failure cases (invalid data)
#   - Use descriptive test names that explain what's being tested
#   - Include comments explaining WHY we're testing something
# =============================================================================

from datetime import date, datetime

import pytest
from pydantic import ValidationError

from cosmetics_records.models.audit import AuditAction, AuditLog
from cosmetics_records.models.client import Client
from cosmetics_records.models.product import InventoryItem, ProductRecord
from cosmetics_records.models.treatment import TreatmentRecord


# =============================================================================
# Client Model Tests
# =============================================================================


class TestClient:
    """Tests for the Client model."""

    def test_client_creation_valid(self):
        """
        Test that a client can be created with valid data.

        This is a "happy path" test - everything should work correctly when
        we provide valid, well-formed data.
        """
        # Create a client with all required fields
        client = Client(
            first_name="Jane",
            last_name="Doe",
            email="jane@example.com",
            phone="+1-555-0123",
        )

        # Verify the fields were set correctly
        assert client.first_name == "Jane"
        assert client.last_name == "Doe"
        assert client.email == "jane@example.com"
        assert client.phone == "+1-555-0123"

        # ID should be None for new clients (not yet in database)
        assert client.id is None

        # Tags should default to an empty list
        assert client.tags == []

    def test_client_creation_missing_required_fields(self):
        """
        Test that creating a client without required fields raises ValidationError.

        The Client model requires first_name and last_name. Attempting to
        create a client without these should fail with a clear error message.
        """
        # Try to create a client without first_name (should fail)
        with pytest.raises(ValidationError) as exc_info:
            Client(last_name="Doe")

        # Verify the error mentions the missing field
        error_dict = exc_info.value.errors()
        field_names = [error["loc"][0] for error in error_dict]
        assert "first_name" in field_names

        # Try to create a client without last_name (should also fail)
        with pytest.raises(ValidationError) as exc_info:
            Client(first_name="Jane")

        error_dict = exc_info.value.errors()
        field_names = [error["loc"][0] for error in error_dict]
        assert "last_name" in field_names

    def test_client_full_name(self):
        """
        Test the full_name() method returns "First Last" format.

        This is a critical method used throughout the UI for displaying
        client names consistently.
        """
        client = Client(first_name="Jane", last_name="Doe")

        # full_name() should combine first and last name with a space
        assert client.full_name() == "Jane Doe"

        # Test with different names to ensure it's not hardcoded
        client2 = Client(first_name="John", last_name="Smith")
        assert client2.full_name() == "John Smith"

    def test_client_age_calculation(self):
        """
        Test that age() correctly calculates age from date_of_birth.

        The age calculation should handle leap years and return the correct
        age based on today's date.
        """
        # Create a client born on January 1, 1990
        client = Client(
            first_name="Jane", last_name="Doe", date_of_birth=date(1990, 1, 1)
        )

        # Get the age
        age = client.age()

        # Age should be a positive integer
        assert isinstance(age, int)
        assert age > 0

        # Verify it's approximately correct (will be 34 or 35 depending on current date)
        # In 2024, someone born Jan 1 1990 would be 34
        today = date.today()
        expected_age = (
            today.year
            - 1990
            - ((today.month, today.day) < (1, 1))  # Adjust if birthday hasn't happened
        )
        assert age == expected_age

    def test_client_age_when_dob_is_none(self):
        """
        Test that age() returns None when date_of_birth is not set.

        Not all clients will have a date of birth recorded. The age() method
        should gracefully handle this by returning None.
        """
        client = Client(first_name="Jane", last_name="Doe")

        # No date of birth set, so age should be None
        assert client.age() is None

    def test_client_tags_string_conversion(self):
        """
        Test that tags_string() converts the tags list to comma-separated format.

        The database stores tags as a TEXT field with comma-separated values.
        The tags_string() method handles this conversion.
        """
        # Client with multiple tags
        client = Client(
            first_name="Jane", last_name="Doe", tags=["VIP", "Regular", "Premium"]
        )

        # Should join tags with comma and space
        assert client.tags_string() == "VIP, Regular, Premium"

        # Client with no tags
        client2 = Client(first_name="John", last_name="Smith", tags=[])
        assert client2.tags_string() == ""

        # Client with single tag
        client3 = Client(first_name="Alice", last_name="Brown", tags=["VIP"])
        assert client3.tags_string() == "VIP"

    def test_client_from_tags_string(self):
        """
        Test that from_tags_string() parses comma-separated string into a list.

        This is the inverse of tags_string() - it converts from database format
        back to Python list format.
        """
        # Parse a comma-separated string
        tags = Client.from_tags_string("VIP, Regular, Premium")
        assert tags == ["VIP", "Regular", "Premium"]

        # Parse empty string (should return empty list)
        tags = Client.from_tags_string("")
        assert tags == []

        # Parse with extra whitespace (should be trimmed)
        tags = Client.from_tags_string("  VIP  ,  Regular  ,  Premium  ")
        assert tags == ["VIP", "Regular", "Premium"]

        # Parse with double commas (should skip empty values)
        tags = Client.from_tags_string("VIP, , Premium")
        assert tags == ["VIP", "Premium"]

    def test_client_email_validation(self):
        """
        Test that email validation accepts valid emails and rejects invalid ones.

        The Client model validates email format using a regex pattern. This
        ensures we don't store malformed email addresses.
        """
        # Valid email formats should work
        client = Client(first_name="Jane", last_name="Doe", email="jane@example.com")
        assert client.email == "jane@example.com"

        client2 = Client(
            first_name="John", last_name="Smith", email="john.smith@company.co.uk"
        )
        assert client2.email == "john.smith@company.co.uk"

        # Invalid email formats should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            Client(first_name="Jane", last_name="Doe", email="not-an-email")

        # Verify the error is about email validation
        error_dict = exc_info.value.errors()
        assert any("email" in str(error).lower() for error in error_dict)

        # Email without @ should fail
        with pytest.raises(ValidationError):
            Client(first_name="Jane", last_name="Doe", email="notemail.com")

        # Email without domain should fail
        with pytest.raises(ValidationError):
            Client(first_name="Jane", last_name="Doe", email="jane@")

    def test_client_email_validation_allows_none(self):
        """
        Test that email field accepts None (email is optional).

        Not all clients need an email address. The field should accept None
        and empty strings.
        """
        # None should be accepted
        client = Client(first_name="Jane", last_name="Doe", email=None)
        assert client.email is None

        # Empty string should be converted to None
        client2 = Client(first_name="John", last_name="Smith", email="")
        assert client2.email is None

        # Whitespace-only should be converted to None
        client3 = Client(first_name="Alice", last_name="Brown", email="   ")
        assert client3.email is None

    def test_client_name_validation_strips_whitespace(self):
        """
        Test that name fields strip leading/trailing whitespace.

        Names like "  Jane  " should be automatically cleaned to "Jane".
        This prevents database clutter from accidental whitespace.
        """
        client = Client(first_name="  Jane  ", last_name="  Doe  ")

        # Names should be stripped
        assert client.first_name == "Jane"
        assert client.last_name == "Doe"

    def test_client_name_validation_rejects_empty(self):
        """
        Test that name fields reject empty or whitespace-only values.

        Names like "   " (only whitespace) should be rejected even though
        they pass the min_length check.
        """
        # Whitespace-only first name should fail
        with pytest.raises(ValidationError) as exc_info:
            Client(first_name="   ", last_name="Doe")

        error_dict = exc_info.value.errors()
        assert any("whitespace" in str(error).lower() for error in error_dict)

        # Whitespace-only last name should fail
        with pytest.raises(ValidationError):
            Client(first_name="Jane", last_name="   ")

    def test_client_tags_validation_filters_empty(self):
        """
        Test that tags validation filters out empty strings.

        Tags like ["VIP", "", "Regular"] should be cleaned to ["VIP", "Regular"].
        This prevents empty tags in the database.
        """
        client = Client(
            first_name="Jane", last_name="Doe", tags=["VIP", "   ", "Regular", ""]
        )

        # Empty and whitespace-only tags should be filtered out
        assert client.tags == ["VIP", "Regular"]

        # Tags should be stripped
        client2 = Client(
            first_name="John", last_name="Smith", tags=["  VIP  ", "  Regular  "]
        )
        assert client2.tags == ["VIP", "Regular"]


# =============================================================================
# TreatmentRecord Model Tests
# =============================================================================


class TestTreatmentRecord:
    """Tests for the TreatmentRecord model."""

    def test_treatment_creation_valid(self):
        """
        Test that a treatment record can be created with valid data.

        This verifies the happy path - creating a treatment with all required
        fields properly set.
        """
        treatment = TreatmentRecord(
            client_id=1, treatment_date=date(2024, 1, 15), treatment_notes="Facial"
        )

        assert treatment.client_id == 1
        assert treatment.treatment_date == date(2024, 1, 15)
        assert treatment.treatment_notes == "Facial"
        assert treatment.id is None  # New record, not yet in database

    def test_treatment_date_default_today(self):
        """
        Test that treatment_date defaults to today's date.

        When creating a treatment without specifying the date, it should
        automatically use today's date for convenience.
        """
        treatment = TreatmentRecord(client_id=1, treatment_notes="Facial treatment")

        # Date should default to today
        assert treatment.treatment_date == date.today()

    def test_treatment_client_id_must_be_positive(self):
        """
        Test that client_id must be a positive integer.

        Client IDs should never be 0 or negative (database auto-increment
        starts at 1). This catches programming errors.
        """
        # Zero client_id should fail
        with pytest.raises(ValidationError) as exc_info:
            TreatmentRecord(client_id=0, treatment_notes="Facial")

        error_dict = exc_info.value.errors()
        assert any("client_id" in str(error).lower() for error in error_dict)

        # Negative client_id should fail
        with pytest.raises(ValidationError):
            TreatmentRecord(client_id=-1, treatment_notes="Facial")

    def test_treatment_notes_cannot_be_empty(self):
        """
        Test that treatment_notes cannot be empty or whitespace-only.

        Treatment notes are critical documentation - we need actual content,
        not just whitespace.
        """
        # Empty notes should fail
        with pytest.raises(ValidationError):
            TreatmentRecord(client_id=1, treatment_notes="")

        # Whitespace-only notes should fail
        with pytest.raises(ValidationError) as exc_info:
            TreatmentRecord(client_id=1, treatment_notes="   ")

        error_dict = exc_info.value.errors()
        assert any("whitespace" in str(error).lower() for error in error_dict)

    def test_treatment_date_cannot_be_future(self):
        """
        Test that treatment_date cannot be in the future.

        We don't want to record treatments that haven't happened yet. This
        prevents data entry errors.
        """
        from datetime import timedelta

        # Future date should fail
        future_date = date.today() + timedelta(days=1)

        with pytest.raises(ValidationError) as exc_info:
            TreatmentRecord(
                client_id=1, treatment_notes="Facial", treatment_date=future_date
            )

        error_dict = exc_info.value.errors()
        assert any("future" in str(error).lower() for error in error_dict)

    def test_treatment_date_can_be_today(self):
        """
        Test that treatment_date CAN be today's date.

        Today's date should be valid - treatments performed today are common.
        """
        treatment = TreatmentRecord(
            client_id=1, treatment_notes="Facial", treatment_date=date.today()
        )

        assert treatment.treatment_date == date.today()

    def test_treatment_was_edited(self):
        """
        Test the was_edited() method detects if a record was edited.

        This method checks if updated_at is significantly different from
        created_at (more than 1 second).
        """
        # Create a treatment with timestamps that are the same
        treatment = TreatmentRecord(
            client_id=1,
            treatment_notes="Original notes",
            created_at=datetime(2024, 1, 1, 10, 0, 0),
            updated_at=datetime(2024, 1, 1, 10, 0, 0),
        )

        # Should not be considered edited (timestamps are identical)
        assert treatment.was_edited() is False

        # Update the updated_at timestamp to 5 minutes later
        treatment.updated_at = datetime(2024, 1, 1, 10, 5, 0)

        # Should now be considered edited
        assert treatment.was_edited() is True

    def test_treatment_was_edited_returns_false_when_timestamps_none(self):
        """
        Test that was_edited() returns False when timestamps are None.

        New records that haven't been saved yet won't have timestamps.
        """
        treatment = TreatmentRecord(client_id=1, treatment_notes="New treatment")

        # No timestamps set, so can't determine if edited
        assert treatment.was_edited() is False


# =============================================================================
# ProductRecord Model Tests
# =============================================================================


class TestProductRecord:
    """Tests for the ProductRecord model."""

    def test_product_record_creation(self):
        """
        Test that a product record can be created with valid data.

        ProductRecord uses free-text for product information, so it's very
        flexible in what it accepts.
        """
        product = ProductRecord(
            client_id=1,
            product_date=date(2024, 1, 15),
            product_text="Retinol Serum 30ml",
        )

        assert product.client_id == 1
        assert product.product_date == date(2024, 1, 15)
        assert product.product_text == "Retinol Serum 30ml"
        assert product.id is None

    def test_product_record_date_defaults_to_today(self):
        """
        Test that product_date defaults to today's date.

        Similar to TreatmentRecord, the date should default to today for
        convenience.
        """
        product = ProductRecord(client_id=1, product_text="Vitamin C Serum")

        assert product.product_date == date.today()

    def test_product_record_text_cannot_be_empty(self):
        """
        Test that product_text cannot be empty or whitespace-only.

        We need actual product information, not just whitespace.
        """
        # Empty text should fail
        with pytest.raises(ValidationError):
            ProductRecord(client_id=1, product_text="")

        # Whitespace-only text should fail
        with pytest.raises(ValidationError) as exc_info:
            ProductRecord(client_id=1, product_text="   ")

        error_dict = exc_info.value.errors()
        assert any("whitespace" in str(error).lower() for error in error_dict)

    def test_product_record_client_id_must_be_positive(self):
        """
        Test that client_id must be a positive integer.

        Same validation as TreatmentRecord - client IDs should be positive.
        """
        with pytest.raises(ValidationError):
            ProductRecord(client_id=0, product_text="Serum")

        with pytest.raises(ValidationError):
            ProductRecord(client_id=-1, product_text="Serum")

    def test_product_record_date_cannot_be_future(self):
        """
        Test that product_date cannot be in the future.

        We don't want to record product sales/usage that hasn't happened yet.
        """
        from datetime import timedelta

        future_date = date.today() + timedelta(days=1)

        with pytest.raises(ValidationError) as exc_info:
            ProductRecord(client_id=1, product_text="Serum", product_date=future_date)

        error_dict = exc_info.value.errors()
        assert any("future" in str(error).lower() for error in error_dict)

    def test_product_record_was_edited(self):
        """
        Test the was_edited() method for ProductRecord.

        This is identical logic to TreatmentRecord.was_edited().
        """
        product = ProductRecord(
            client_id=1,
            product_text="Serum",
            created_at=datetime(2024, 1, 1, 10, 0, 0),
            updated_at=datetime(2024, 1, 1, 10, 0, 0),
        )

        assert product.was_edited() is False

        product.updated_at = datetime(2024, 1, 1, 11, 0, 0)
        assert product.was_edited() is True


# =============================================================================
# InventoryItem Model Tests
# =============================================================================


class TestInventoryItem:
    """Tests for the InventoryItem model."""

    def test_inventory_item_creation(self):
        """
        Test that an inventory item can be created with valid data.

        InventoryItem has strict validation for unit (must be ml, g, or Pc.)
        and capacity (must be positive).
        """
        item = InventoryItem(
            name="Retinol Serum",
            description="Anti-aging formula",
            capacity=30.0,
            unit="ml",
        )

        assert item.name == "Retinol Serum"
        assert item.description == "Anti-aging formula"
        assert item.capacity == 30.0
        assert item.unit == "ml"
        assert item.id is None

    def test_inventory_item_display_name(self):
        """
        Test the display_name() method formats name with capacity and unit.

        This creates user-friendly strings like "Retinol Serum (30 ml)" for
        display in dropdowns and lists.
        """
        item = InventoryItem(name="Retinol Serum", capacity=30.0, unit="ml")
        assert item.display_name() == "Retinol Serum (30 ml)"

        item2 = InventoryItem(name="Face Cream", capacity=50.0, unit="g")
        assert item2.display_name() == "Face Cream (50 g)"

        item3 = InventoryItem(name="Cotton Pads", capacity=1.0, unit="Pc.")
        assert item3.display_name() == "Cotton Pads (1 Pc.)"

        # Test with decimal capacity
        item4 = InventoryItem(name="Sample", capacity=2.5, unit="ml")
        assert item4.display_name() == "Sample (2.5 ml)"

    def test_inventory_item_invalid_unit(self):
        """
        Test that invalid units are rejected.

        Only "ml", "g", and "Pc." are allowed. Anything else should fail.
        """
        # Invalid unit should fail
        with pytest.raises(ValidationError) as exc_info:
            InventoryItem(name="Product", capacity=30.0, unit="liters")

        error_dict = exc_info.value.errors()
        # Check that the error is related to unit validation
        assert any("unit" in str(error) for error in error_dict)

        # Try other invalid units
        with pytest.raises(ValidationError):
            InventoryItem(name="Product", capacity=30.0, unit="kg")

        with pytest.raises(ValidationError):
            InventoryItem(name="Product", capacity=30.0, unit="oz")

    def test_inventory_item_valid_units(self):
        """
        Test that all three valid units are accepted.

        "ml", "g", and "Pc." should all work.
        """
        # ml should work
        item1 = InventoryItem(name="Serum", capacity=30.0, unit="ml")
        assert item1.unit == "ml"

        # g should work
        item2 = InventoryItem(name="Cream", capacity=50.0, unit="g")
        assert item2.unit == "g"

        # Pc. should work
        item3 = InventoryItem(name="Pads", capacity=1.0, unit="Pc.")
        assert item3.unit == "Pc."

    def test_inventory_item_capacity_validation(self):
        """
        Test that capacity must be greater than 0.

        Zero or negative capacity doesn't make sense for a product.
        """
        # Zero capacity should fail
        with pytest.raises(ValidationError) as exc_info:
            InventoryItem(name="Product", capacity=0.0, unit="ml")

        error_dict = exc_info.value.errors()
        assert any("capacity" in str(error).lower() for error in error_dict)

        # Negative capacity should fail
        with pytest.raises(ValidationError):
            InventoryItem(name="Product", capacity=-10.0, unit="ml")

    def test_inventory_item_name_cannot_be_empty(self):
        """
        Test that name cannot be empty or whitespace-only.

        Product names are required and must have actual content.
        """
        # Empty name should fail
        with pytest.raises(ValidationError):
            InventoryItem(name="", capacity=30.0, unit="ml")

        # Whitespace-only name should fail
        with pytest.raises(ValidationError) as exc_info:
            InventoryItem(name="   ", capacity=30.0, unit="ml")

        error_dict = exc_info.value.errors()
        assert any("whitespace" in str(error).lower() for error in error_dict)

    def test_inventory_item_description_optional(self):
        """
        Test that description is optional and converts empty strings to None.

        Description is an optional field. Empty strings should be normalized
        to None for database consistency.
        """
        # No description should be fine
        item1 = InventoryItem(name="Product", capacity=30.0, unit="ml")
        assert item1.description is None

        # Empty string should be converted to None
        item2 = InventoryItem(name="Product", capacity=30.0, unit="ml", description="")
        assert item2.description is None

        # Whitespace-only should be converted to None
        item3 = InventoryItem(
            name="Product", capacity=30.0, unit="ml", description="   "
        )
        assert item3.description is None

        # Actual description should be preserved
        item4 = InventoryItem(
            name="Product", capacity=30.0, unit="ml", description="Good stuff"
        )
        assert item4.description == "Good stuff"


# =============================================================================
# AuditLog Model Tests
# =============================================================================


class TestAuditLog:
    """Tests for the AuditLog model."""

    def test_audit_log_creation(self):
        """
        Test that an audit log can be created with valid data.

        AuditLog tracks all data changes in the application.
        """
        log = AuditLog(
            table_name="clients",
            record_id=1,
            action=AuditAction.UPDATE,
            field_name="email",
            old_value="old@example.com",
            new_value="new@example.com",
            ui_location="ClientEditView",
        )

        assert log.table_name == "clients"
        assert log.record_id == 1
        assert log.action == AuditAction.UPDATE
        assert log.field_name == "email"
        assert log.old_value == "old@example.com"
        assert log.new_value == "new@example.com"
        assert log.ui_location == "ClientEditView"

    def test_audit_log_get_description_create(self):
        """
        Test get_description() for CREATE actions.

        CREATE actions should generate descriptions like
        "New treatment added for Jane Doe".
        """
        # Test creating a treatment
        log = AuditLog(
            table_name="treatment_records",
            record_id=1,
            action=AuditAction.CREATE,
            new_value="Facial treatment",
            ui_location="TreatmentHistoryView",
        )

        desc = log.get_description("Jane Doe")
        assert "treatment" in desc.lower()
        assert "Jane Doe" in desc

        # Test creating a client (shouldn't include client name since it IS the client)
        log2 = AuditLog(
            table_name="clients",
            record_id=1,
            action=AuditAction.CREATE,
            new_value="Jane Doe",
            ui_location="ClientEditView",
        )

        desc2 = log2.get_description("Jane Doe")
        assert "client" in desc2.lower()
        assert "created" in desc2.lower()

    def test_audit_log_get_description_update(self):
        """
        Test get_description() for UPDATE actions.

        UPDATE actions should show what field changed and the old/new values.
        """
        log = AuditLog(
            table_name="clients",
            record_id=1,
            action=AuditAction.UPDATE,
            field_name="email",
            old_value="old@example.com",
            new_value="new@example.com",
            ui_location="ClientEditView",
        )

        desc = log.get_description("Jane Doe")
        assert "email" in desc.lower()
        assert "old@example.com" in desc
        assert "new@example.com" in desc
        assert "updated" in desc.lower()

    def test_audit_log_get_description_delete(self):
        """
        Test get_description() for DELETE actions.

        DELETE actions should show what was deleted.
        """
        log = AuditLog(
            table_name="product_records",
            record_id=1,
            action=AuditAction.DELETE,
            old_value="Retinol Serum 30ml",
            ui_location="ProductHistoryView",
        )

        desc = log.get_description("Jane Doe")
        assert "deleted" in desc.lower()
        assert "Retinol Serum 30ml" in desc

    def test_audit_log_record_id_must_be_positive(self):
        """
        Test that record_id must be a positive integer.

        Record IDs should never be 0 or negative.
        """
        with pytest.raises(ValidationError):
            AuditLog(
                table_name="clients",
                record_id=0,
                action=AuditAction.CREATE,
                ui_location="ClientEditView",
            )

        with pytest.raises(ValidationError):
            AuditLog(
                table_name="clients",
                record_id=-1,
                action=AuditAction.CREATE,
                ui_location="ClientEditView",
            )

    def test_audit_log_table_name_cannot_be_empty(self):
        """
        Test that table_name cannot be empty or whitespace-only.

        Table name is critical for the audit trail.
        """
        with pytest.raises(ValidationError):
            AuditLog(
                table_name="",
                record_id=1,
                action=AuditAction.CREATE,
                ui_location="ClientEditView",
            )

        with pytest.raises(ValidationError):
            AuditLog(
                table_name="   ",
                record_id=1,
                action=AuditAction.CREATE,
                ui_location="ClientEditView",
            )

    def test_audit_log_ui_location_cannot_be_empty(self):
        """
        Test that ui_location cannot be empty or whitespace-only.

        UI location helps track where changes originated.
        """
        with pytest.raises(ValidationError):
            AuditLog(
                table_name="clients",
                record_id=1,
                action=AuditAction.CREATE,
                ui_location="",
            )

        with pytest.raises(ValidationError):
            AuditLog(
                table_name="clients",
                record_id=1,
                action=AuditAction.CREATE,
                ui_location="   ",
            )
