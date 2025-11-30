# =============================================================================
# Cosmetics Records - Models Package
# =============================================================================
# This package contains Pydantic data models that define the structure
# and validation rules for all data in the application.
#
# Models in this package:
#   - Client: Customer information (name, contact, allergies, etc.)
#   - TreatmentRecord: Record of treatments performed
#   - ProductRecord: Record of products sold/used
#   - InventoryItem: Products in the salon's inventory
#   - AuditLog: Change tracking for all data modifications
#   - AuditAction: Enumeration of audit action types (CREATE/UPDATE/DELETE)
# =============================================================================

# Import all models for easy access
from .audit import AuditAction, AuditLog
from .client import Client
from .product import InventoryItem, ProductRecord
from .treatment import TreatmentRecord

# Define what gets exported when using "from models import *"
__all__ = [
    "Client",
    "TreatmentRecord",
    "ProductRecord",
    "InventoryItem",
    "AuditLog",
    "AuditAction",
]
