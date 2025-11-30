# =============================================================================
# Cosmetics Records - Database Migrations Package
# =============================================================================
# This package contains database migration scripts that manage schema changes.
#
# Migration files are named with a version prefix (v001_, v002_, etc.) and
# are applied in sequential order. Each migration can upgrade the schema
# and optionally provide a downgrade path.
#
# The migration_manager.py module handles:
#   - Tracking which migrations have been applied
#   - Applying new migrations in order
#   - Creating backups before migrations
# =============================================================================
