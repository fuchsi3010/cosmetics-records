# =============================================================================
# Cosmetics Records - Controllers Package
# =============================================================================
# This package contains the business logic layer (Controller in MVC pattern).
#
# Controllers coordinate between:
#   - Models (data validation and structure)
#   - Views (user interface)
#   - Database (data persistence)
#   - Services (cross-cutting concerns like audit logging)
#
# Each controller handles a specific domain:
#   - ClientController: Client CRUD operations
#   - TreatmentController: Treatment record management
#   - ProductController: Product record management
#   - InventoryController: Inventory item management
# =============================================================================

from cosmetics_records.controllers.client_controller import ClientController
from cosmetics_records.controllers.treatment_controller import TreatmentController
from cosmetics_records.controllers.product_controller import ProductController
from cosmetics_records.controllers.inventory_controller import InventoryController

__all__ = [
    "ClientController",
    "TreatmentController",
    "ProductController",
    "InventoryController",
]
