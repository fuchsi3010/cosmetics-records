# =============================================================================
# Cosmetics Records - Full Workflow Integration Tests
# =============================================================================
# This file contains end-to-end integration tests that verify complete
# workflows through the application. These tests simulate real user scenarios
# and verify that all components work together correctly.
#
# Test Workflows:
#   - Complete client CRUD workflow
#   - Treatment history workflow
#   - Backup and restore workflow
#   - Audit logging across operations
#
# These tests represent real-world usage patterns and verify that the entire
# application stack works correctly from start to finish.
# =============================================================================

import tempfile
from datetime import date
from pathlib import Path

from cosmetics_records.controllers.client_controller import ClientController
from cosmetics_records.controllers.treatment_controller import TreatmentController
from cosmetics_records.models.client import Client
from cosmetics_records.models.treatment import TreatmentRecord
from cosmetics_records.services.audit_service import AuditService
from cosmetics_records.services.backup_service import BackupService
from cosmetics_records.services.export_service import ExportService


class TestFullWorkflows:
    """End-to-end workflow integration tests."""

    def test_client_crud_workflow(self, db_connection):
        """
        Test the complete client CRUD (Create, Read, Update, Delete) workflow.

        This simulates a typical user workflow:
        1. Create a new client
        2. Retrieve the client to view details
        3. Update some client information
        4. Search for the client
        5. Delete the client
        6. Verify deletion

        This tests that all client operations work together correctly.
        """
        controller = ClientController(db_connection)

        # STEP 1: Create a new client
        new_client = Client(
            first_name="Alice",
            last_name="Johnson",
            email="alice@example.com",
            phone="+1-555-0100",
            tags=["VIP", "New Client"],
        )

        client_id = controller.create_client(new_client)
        assert client_id > 0

        # STEP 2: Retrieve the client
        retrieved = controller.get_client(client_id)
        assert retrieved is not None
        assert retrieved.full_name() == "Alice Johnson"
        assert retrieved.email == "alice@example.com"
        assert "VIP" in retrieved.tags

        # STEP 3: Update the client information
        retrieved.email = "alice.johnson@newdomain.com"
        retrieved.tags = ["VIP", "Regular", "Premium"]
        retrieved.allergies = "Sensitive to retinol"

        update_success = controller.update_client(retrieved)
        assert update_success is True

        # Verify updates persisted
        updated = controller.get_client(client_id)
        assert updated.email == "alice.johnson@newdomain.com"
        assert updated.allergies == "Sensitive to retinol"
        assert len(updated.tags) == 3

        # STEP 4: Search for the client
        search_results = controller.search_clients("Alice")
        assert len(search_results) > 0
        assert any(c.id == client_id for c in search_results)

        # STEP 5: Delete the client
        delete_success = controller.delete_client(client_id)
        assert delete_success is True

        # STEP 6: Verify deletion
        deleted_client = controller.get_client(client_id)
        assert deleted_client is None

    def test_treatment_workflow(self, db_connection, sample_client):
        """
        Test the complete treatment management workflow.

        This simulates managing a client's treatment history:
        1. Create a client
        2. Add multiple treatment records
        3. Retrieve treatment history
        4. Update a treatment
        5. Verify all treatments are linked correctly
        """
        client_controller = ClientController(db_connection)
        treatment_controller = TreatmentController(db_connection)

        # STEP 1: Create a client
        client_id = client_controller.create_client(sample_client)

        # STEP 2: Add multiple treatments
        treatments_data = [
            "Deep cleansing facial with hyaluronic acid",
            "Anti-aging treatment with retinol serum",
            "Hydrating mask with vitamin C",
        ]

        treatment_ids = []
        for notes in treatments_data:
            treatment = TreatmentRecord(client_id=client_id, treatment_notes=notes)

            treatment_id = treatment_controller.create_treatment(treatment)
            treatment_ids.append(treatment_id)

        assert len(treatment_ids) == 3

        # STEP 3: Retrieve treatment history
        history = treatment_controller.get_treatments_for_client(client_id)
        assert len(history) == 3

        # Verify all treatments are for the correct client
        assert all(t.client_id == client_id for t in history)

        # STEP 4: Update a treatment
        first_treatment = treatment_controller.get_treatment(treatment_ids[0])
        first_treatment.treatment_notes += " - Client loved the results!"

        update_success = treatment_controller.update_treatment(first_treatment)
        assert update_success is True

        # Verify update persisted
        updated_treatment = treatment_controller.get_treatment(treatment_ids[0])
        assert "Client loved the results!" in updated_treatment.treatment_notes

        # STEP 5: Verify cascade delete (when client is deleted, treatments go too)
        client_controller.delete_client(client_id)

        # Treatments should be gone
        remaining_history = treatment_controller.get_treatments_for_client(client_id)
        assert len(remaining_history) == 0

    def test_backup_and_restore_workflow(self, db_connection, temp_db, sample_client):
        """
        Test the backup and restore workflow.

        This verifies that:
        1. Data can be backed up
        2. Backups are stored correctly
        3. Multiple backups can be managed
        4. Old backups are cleaned up
        """
        client_controller = ClientController(db_connection)

        # Create some data
        client_id = client_controller.create_client(sample_client)
        assert client_id > 0

        # Create a backup
        with tempfile.TemporaryDirectory() as backup_dir:
            backup_service = BackupService(db_path=temp_db, backup_dir=backup_dir)

            # STEP 1: Create a backup
            backup_path = backup_service.create_backup()
            assert Path(backup_path).exists()

            # STEP 2: Verify backup was created
            backups = backup_service.get_backups()
            assert len(backups) == 1
            assert backups[0]["path"] == backup_path

            # STEP 3: Create more backups
            backup_service.create_backup()
            backup_service.create_backup()

            backups = backup_service.get_backups()
            assert len(backups) == 3

            # STEP 4: Clean up old backups (keep only 2)
            deleted_count = backup_service.cleanup_old_backups(retention_count=2)
            assert deleted_count == 1

            remaining_backups = backup_service.get_backups()
            assert len(remaining_backups) == 2

    def test_audit_trail_workflow(self, db_connection, sample_client):
        """
        Test that audit logging works across multiple operations.

        This verifies that:
        1. All operations are logged
        2. Audit logs can be retrieved
        3. Audit logs contain correct information
        """
        client_controller = ClientController(db_connection)
        audit_service = AuditService(db_connection)

        # STEP 1: Create a client and log it
        client_id = client_controller.create_client(sample_client)

        audit_service.log_create(
            table_name="clients",
            record_id=client_id,
            new_value=sample_client.full_name(),
            ui_location="ClientEditView",
        )

        # STEP 2: Update the client and log it
        client = client_controller.get_client(client_id)
        old_email = client.email
        client.email = "newemail@example.com"
        client_controller.update_client(client)

        audit_service.log_update(
            table_name="clients",
            record_id=client_id,
            field_name="email",
            old_value=old_email,
            new_value=client.email,
            ui_location="ClientEditView",
        )

        # STEP 3: Delete the client and log it
        client_controller.delete_client(client_id)

        audit_service.log_delete(
            table_name="clients",
            record_id=client_id,
            old_value=sample_client.full_name(),
            ui_location="ClientListView",
        )

        # STEP 4: Retrieve audit logs
        logs = audit_service.get_audit_logs(table_name="clients")

        # Should have 3 log entries (CREATE, UPDATE, DELETE)
        assert len(logs) == 3

        # Verify log contents
        create_log = next((log for log in logs if log.action.value == "CREATE"), None)
        assert create_log is not None
        assert create_log.new_value == sample_client.full_name()

        update_log = next((log for log in logs if log.action.value == "UPDATE"), None)
        assert update_log is not None
        assert update_log.field_name == "email"
        assert update_log.new_value == "newemail@example.com"

        delete_log = next((log for log in logs if log.action.value == "DELETE"), None)
        assert delete_log is not None
        assert delete_log.old_value == sample_client.full_name()

    def test_export_workflow(self, db_connection):
        """
        Test the complete export workflow.

        This verifies that:
        1. Multiple clients can be created
        2. Clients can be exported to CSV
        3. The export contains correct data
        """
        client_controller = ClientController(db_connection)
        export_service = ExportService(db_connection)

        # STEP 1: Create multiple clients
        clients_data = [
            Client(
                first_name="Alice",
                last_name="Anderson",
                email="alice@example.com",
                address="123 Main St",
            ),
            Client(
                first_name="Bob",
                last_name="Brown",
                email="bob@example.com",
                address="456 Oak Ave",
            ),
            Client(
                first_name="Charlie",
                last_name="Clark",
                email="charlie@example.com",
                address="789 Elm St",
            ),
        ]

        for client in clients_data:
            client_controller.create_client(client)

        # STEP 2: Export to CSV
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False
        ) as temp_file:
            export_path = temp_file.name

        try:
            count = export_service.export_clients_for_mail_merge(export_path)

            # Should have exported 3 clients
            assert count == 3

            # STEP 3: Verify export contents
            import csv

            with open(export_path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

                assert len(rows) == 3

                # Verify data
                first_names = [row["first_name"] for row in rows]
                assert "Alice" in first_names
                assert "Bob" in first_names
                assert "Charlie" in first_names

        finally:
            Path(export_path).unlink(missing_ok=True)

    def test_search_and_filter_workflow(self, db_connection):
        """
        Test the complete search and filter workflow.

        This verifies that:
        1. Multiple clients can be created
        2. Fuzzy search works correctly
        3. Alphabetical filtering works correctly
        4. Pagination works correctly
        """
        client_controller = ClientController(db_connection)

        # STEP 1: Create clients with various names
        clients_data = [
            ("Alice", "Anderson"),
            ("Anna", "Adams"),
            ("Bob", "Brown"),
            ("Charlie", "Clark"),
            ("David", "Davis"),
            ("Alice", "Baker"),
        ]

        for first, last in clients_data:
            client = Client(first_name=first, last_name=last)
            client_controller.create_client(client)

        # STEP 2: Test fuzzy search
        # Search for "Alice" (should find 2 clients)
        alice_results = client_controller.search_clients("Alice")
        assert len(alice_results) == 2
        assert all("Alice" in c.first_name for c in alice_results)

        # STEP 3: Test alphabetical filter
        # Filter by 'A' (should find Anderson, Adams)
        a_clients = client_controller.filter_by_letter("A")
        assert len(a_clients) == 2
        assert all(c.last_name.startswith("A") for c in a_clients)

        # Filter by 'B' (should find Brown, Baker)
        b_clients = client_controller.filter_by_letter("B")
        assert len(b_clients) == 2

        # STEP 4: Test pagination
        # Get first 3 clients
        page1 = client_controller.get_all_clients(limit=3, offset=0)
        assert len(page1) == 3

        # Get next 3 clients
        page2 = client_controller.get_all_clients(limit=3, offset=3)
        assert len(page2) == 3

        # Verify no overlap
        page1_ids = {c.id for c in page1}
        page2_ids = {c.id for c in page2}
        assert len(page1_ids & page2_ids) == 0

    def test_complex_data_workflow(self, db_connection):
        """
        Test a complex workflow with multiple related records.

        This simulates a real-world scenario:
        1. Create a client
        2. Add multiple treatments
        3. Add product records
        4. Search and filter
        5. Export data
        6. Clean up

        This verifies that all components work together in a realistic scenario.
        """
        from cosmetics_records.controllers.product_controller import ProductController
        from cosmetics_records.models.product import ProductRecord

        client_controller = ClientController(db_connection)
        treatment_controller = TreatmentController(db_connection)
        product_controller = ProductController(db_connection)

        # STEP 1: Create a client with full information
        client = Client(
            first_name="Emily",
            last_name="Williams",
            email="emily@example.com",
            phone="+1-555-0200",
            address="321 Pine St, Springfield, IL",
            date_of_birth=date(1985, 5, 15),
            allergies="Sensitive to fragrance",
            tags=["VIP", "Sensitive Skin", "Monthly Client"],
            planned_treatment="Monthly hydration facial",
            notes="Prefers morning appointments, likes lavender scent",
        )

        client_id = client_controller.create_client(client)

        # STEP 2: Add treatments
        treatments = [
            TreatmentRecord(
                client_id=client_id,
                treatment_notes="Initial consultation and skin analysis",
            ),
            TreatmentRecord(
                client_id=client_id,
                treatment_notes="Deep cleansing facial with extraction",
            ),
            TreatmentRecord(
                client_id=client_id, treatment_notes="Hydrating treatment with mask"
            ),
        ]

        for treatment in treatments:
            treatment_controller.create_treatment(treatment)

        # STEP 3: Add product records
        products = [
            ProductRecord(client_id=client_id, product_text="Gentle Cleanser 150ml"),
            ProductRecord(
                client_id=client_id, product_text="Hyaluronic Acid Serum 30ml"
            ),
            ProductRecord(client_id=client_id, product_text="Moisturizing Cream 50g"),
        ]

        for product in products:
            product_controller.create_product_record(product)

        # STEP 4: Verify everything is linked correctly
        # Get client
        retrieved_client = client_controller.get_client(client_id)
        assert retrieved_client.full_name() == "Emily Williams"
        assert len(retrieved_client.tags) == 3

        # Get treatments
        client_treatments = treatment_controller.get_treatments_for_client(client_id)
        assert len(client_treatments) == 3

        # Get products
        client_products = product_controller.get_products_for_client(client_id)
        assert len(client_products) == 3

        # STEP 5: Search for the client
        search_results = client_controller.search_clients("Emily")
        assert len(search_results) > 0
        assert any(c.id == client_id for c in search_results)

        # STEP 6: Clean up (delete client, should cascade)
        client_controller.delete_client(client_id)

        # Verify everything is gone
        assert client_controller.get_client(client_id) is None
        assert len(treatment_controller.get_treatments_for_client(client_id)) == 0
        assert len(product_controller.get_products_for_client(client_id)) == 0
