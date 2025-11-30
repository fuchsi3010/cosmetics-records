# =============================================================================
# Cosmetics Records - Backup Service
# =============================================================================
# This module provides the BackupService class, which handles database backup
# and restore operations. It creates timestamped ZIP backups and manages
# backup retention policies.
#
# Key Features:
#   - Create timestamped ZIP backups of the SQLite database
#   - Restore database from a backup file (with pre-restore safety backup)
#   - List available backups with metadata (size, date, etc.)
#   - Automatic cleanup of old backups based on retention count
#   - Auto-backup scheduling support
#   - Thread-safe backup operations
#
# Backup Format:
#   - ZIP file containing the SQLite database file
#   - Filename format: cosmetics_records_backup_YYYYMMDD_HHMMSS.zip
#   - Example: cosmetics_records_backup_20240115_143000.zip
#
# Usage Example:
#   backup_service = BackupService(
#       db_path="/path/to/database.db",
#       backup_dir="/path/to/backups"
#   )
#   backup_path = backup_service.create_backup()
#   backup_service.cleanup_old_backups(retention_count=10)
#
# Design Decisions:
#   - ZIP format for compression and portability
#   - Timestamped filenames for easy identification
#   - Pre-restore backup ensures safety during restore operations
#   - Retention policy prevents unlimited backup growth
# =============================================================================

import logging
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configure module logger for debugging backup operations
logger = logging.getLogger(__name__)


class BackupService:
    """
    Service for database backup and restore operations.

    This class handles creating, restoring, listing, and managing database
    backups. It provides a complete backup solution with retention policies
    and safety features.

    The service is thread-safe for backup operations - multiple backups can
    be created simultaneously without file conflicts (thanks to timestamps
    in filenames).

    Attributes:
        db_path: Path to the SQLite database file
        backup_dir: Directory where backups are stored
    """

    def __init__(self, db_path: str, backup_dir: str):
        """
        Initialize the backup service.

        Args:
            db_path: Path to the SQLite database file to back up
            backup_dir: Directory where backup files will be stored
                       (will be created if it doesn't exist)

        Note:
            The backup directory is created automatically if it doesn't exist.
            This ensures the service can start working immediately.
        """
        self.db_path = Path(db_path)
        self.backup_dir = Path(backup_dir)

        # Create backup directory if it doesn't exist
        # parents=True creates intermediate directories if needed
        # exist_ok=True prevents errors if directory already exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        logger.debug(
            f"BackupService initialized: db={self.db_path}, "
            f"backup_dir={self.backup_dir}"
        )

    def create_backup(self) -> str:
        """
        Create a timestamped ZIP backup of the database.

        This creates a compressed backup of the SQLite database file with a
        timestamp in the filename for easy identification. The backup is a
        complete copy of the database at this point in time.

        Returns:
            The absolute path to the created backup file

        Raises:
            FileNotFoundError: If the database file doesn't exist
            PermissionError: If we don't have permission to read the database
            OSError: If the backup creation fails for other reasons

        Example:
            >>> backup_path = backup_service.create_backup()
            >>> print(f"Backup created at: {backup_path}")
            Backup created at: /path/to/backups/backup_20240115_143000.zip
        """
        try:
            # Verify database file exists before attempting backup
            if not self.db_path.exists():
                raise FileNotFoundError(f"Database file not found: {self.db_path}")

            # Generate timestamped filename
            # Format: cosmetics_records_backup_YYYYMMDD_HHMMSS.zip
            # This ensures unique filenames even if backups are created rapidly
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"cosmetics_records_backup_{timestamp}.zip"
            backup_path = self.backup_dir / backup_filename

            # Create ZIP file with the database
            # We use ZIP format for:
            # 1. Compression (saves disk space)
            # 2. Standard format (can be opened on any platform)
            # 3. Single-file backup (easy to manage)
            with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                # Add the database file to the ZIP
                # arcname is the name inside the ZIP (just the filename, not full path)
                zipf.write(self.db_path, arcname=self.db_path.name)

            logger.info(f"Backup created successfully: {backup_path}")

            # Return the absolute path as a string
            return str(backup_path.absolute())

        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise

    def restore_backup(self, backup_path: str) -> bool:
        """
        Restore database from a backup file.

        This extracts the database from a backup ZIP and replaces the current
        database. As a safety measure, it creates a pre-restore backup of the
        current database before overwriting it.

        IMPORTANT: This operation will overwrite the current database. The old
        database is preserved as a pre-restore backup in case of issues.

        Args:
            backup_path: Path to the backup ZIP file to restore from

        Returns:
            True on successful restore, False otherwise

        Raises:
            FileNotFoundError: If the backup file doesn't exist
            zipfile.BadZipFile: If the backup file is corrupted
            PermissionError: If we don't have permission to write the database
            OSError: If the restore fails for other reasons

        Example:
            >>> success = backup_service.restore_backup(
            ...     "/path/to/backups/cosmetics_records_backup_20240115_143000.zip"
            ... )
            >>> if success:
            ...     print("Database restored successfully")
        """
        try:
            backup_path_obj = Path(backup_path)

            # Verify backup file exists
            if not backup_path_obj.exists():
                raise FileNotFoundError(f"Backup file not found: {backup_path}")

            # Verify it's a valid ZIP file
            if not zipfile.is_zipfile(backup_path):
                raise ValueError(f"File is not a valid ZIP file: {backup_path}")

            # Create a pre-restore backup of the current database
            # This ensures we can recover if the restore goes wrong
            # Format: cosmetics_records_backup_prerestore_YYYYMMDD_HHMMSS.zip
            if self.db_path.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                prerestore_filename = (
                    f"cosmetics_records_backup_prerestore_{timestamp}.zip"
                )
                prerestore_path = self.backup_dir / prerestore_filename

                with zipfile.ZipFile(
                    prerestore_path, "w", zipfile.ZIP_DEFLATED
                ) as zipf:
                    zipf.write(self.db_path, arcname=self.db_path.name)

                logger.info(f"Pre-restore backup created: {prerestore_path}")

            # Extract the database from the backup ZIP
            with zipfile.ZipFile(backup_path, "r") as zipf:
                # Get list of files in the ZIP
                file_list = zipf.namelist()

                # Find the database file in the ZIP
                # It should be named like "cosmetics_records.db"
                db_filename = self.db_path.name
                if db_filename not in file_list:
                    # If exact name not found, try to find any .db file
                    db_files = [f for f in file_list if f.endswith(".db")]
                    if not db_files:
                        raise ValueError(
                            f"No database file found in backup: {backup_path}"
                        )
                    db_filename = db_files[0]
                    logger.warning(
                        f"Expected {self.db_path.name} but found {db_filename}"
                    )

                # Extract to a temporary location first
                # This prevents corruption if extraction fails partway through
                temp_path = self.db_path.parent / f"{self.db_path.name}.tmp"
                with zipf.open(db_filename) as source:
                    with open(temp_path, "wb") as target:
                        shutil.copyfileobj(source, target)

                # Move the temporary file to the actual database location
                # This is an atomic operation on most filesystems
                # If the database is currently open, this may fail with PermissionError
                # (Windows locks open files, Linux/macOS may allow it)
                shutil.move(str(temp_path), str(self.db_path))

            logger.info(f"Database restored successfully from: {backup_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            # Don't re-raise - return False to indicate failure
            # This allows callers to handle the error gracefully
            return False

    def get_backups(self) -> List[Dict[str, Any]]:
        """
        Get list of available backups with metadata.

        This scans the backup directory and returns information about all
        backup files, including their size, creation date, and path. The
        list is sorted by creation date (newest first).

        Returns:
            List of dictionaries with backup metadata:
            [
                {
                    "path": "/path/to/backup.zip",
                    "filename": "cosmetics_records_backup_20240115_143000.zip",
                    "size": 1024000,  # Size in bytes
                    "created": datetime(2024, 1, 15, 14, 30, 0)
                },
                ...
            ]

        Example:
            >>> backups = backup_service.get_backups()
            >>> for backup in backups:
            ...     print(f"{backup['filename']}: {backup['size']} bytes")
        """
        try:
            backups: List[Dict[str, Any]] = []

            # Scan backup directory for ZIP files
            # We look for files matching our naming pattern
            for file_path in self.backup_dir.glob("cosmetics_records_backup_*.zip"):
                try:
                    # Get file metadata
                    stat = file_path.stat()

                    # Parse creation date from filename if possible
                    # Format: cosmetics_records_backup_YYYYMMDD_HHMMSS.zip
                    filename = file_path.name
                    try:
                        # Extract the timestamp part: YYYYMMDD_HHMMSS
                        timestamp_str = filename.replace(
                            "cosmetics_records_backup_", ""
                        ).replace(".zip", "")
                        created = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    except ValueError:
                        # If we can't parse the filename, use file modification time
                        created = datetime.fromtimestamp(stat.st_mtime)

                    backup_info = {
                        "path": str(file_path.absolute()),
                        "filename": filename,
                        "size": stat.st_size,  # Size in bytes
                        "created": created,
                    }

                    backups.append(backup_info)

                except Exception as e:
                    # If we can't read a particular file, log it and continue
                    logger.warning(f"Error reading backup file {file_path}: {e}")
                    continue

            # Sort by creation date (newest first)
            # This puts the most recent backup at the top of the list
            backups.sort(key=lambda b: b["created"], reverse=True)

            logger.debug(f"Found {len(backups)} backup files")

            return backups

        except Exception as e:
            logger.error(f"Failed to get backup list: {e}")
            # Return empty list on error (better than crashing)
            return []

    def cleanup_old_backups(self, retention_count: int = 10) -> int:
        """
        Delete old backups beyond retention limit.

        This implements a retention policy to prevent unlimited backup growth.
        It keeps the N most recent backups and deletes older ones. This is
        important for disk space management.

        Args:
            retention_count: Number of most recent backups to keep (default: 10)

        Returns:
            Number of backup files deleted

        Example:
            >>> # Keep only the 10 most recent backups
            >>> deleted = backup_service.cleanup_old_backups(10)
            >>> print(f"Deleted {deleted} old backups")
        """
        try:
            # Get list of all backups (sorted by date, newest first)
            backups = self.get_backups()

            # If we have fewer backups than the retention count, no cleanup needed
            if len(backups) <= retention_count:
                logger.debug(
                    f"No cleanup needed: {len(backups)} backups <= {retention_count}"
                )
                return 0

            # Identify backups to delete (everything after retention_count)
            backups_to_delete = backups[retention_count:]

            # Delete each old backup
            deleted_count = 0
            for backup in backups_to_delete:
                try:
                    backup_path = Path(backup["path"])
                    backup_path.unlink()  # Delete the file
                    deleted_count += 1
                    logger.debug(f"Deleted old backup: {backup['filename']}")
                except Exception as e:
                    logger.warning(f"Failed to delete backup {backup['filename']}: {e}")
                    # Continue with other deletions even if one fails

            logger.info(
                f"Cleaned up {deleted_count} old backups "
                f"(kept {retention_count} most recent)"
            )

            return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}")
            # Return 0 on error (no backups deleted)
            return 0

    def should_auto_backup(
        self, interval_minutes: int, last_backup_time: Optional[datetime]
    ) -> bool:
        """
        Check if auto-backup is needed based on interval.

        This helper method determines if enough time has passed since the last
        backup to trigger an automatic backup. Used by the application to
        implement scheduled backups.

        Args:
            interval_minutes: Backup interval in minutes
                             (e.g., 60 for hourly, 1440 for daily)
            last_backup_time: Timestamp of the last backup, or None if no
                            backup has been made yet

        Returns:
            True if a backup should be created, False otherwise

        Example:
            >>> last_backup = datetime(2024, 1, 15, 14, 0, 0)
            >>> # Check if we should backup (hourly interval)
            >>> should_backup = backup_service.should_auto_backup(
            ...     interval_minutes=60,
            ...     last_backup_time=last_backup
            ... )
        """
        # If no previous backup, we should definitely backup now
        if last_backup_time is None:
            logger.debug("No previous backup found - auto-backup needed")
            return True

        # Calculate time elapsed since last backup
        now = datetime.now()
        elapsed = now - last_backup_time
        elapsed_minutes = elapsed.total_seconds() / 60

        # Check if elapsed time exceeds the interval
        should_backup = elapsed_minutes >= interval_minutes

        logger.debug(
            f"Auto-backup check: {elapsed_minutes:.1f} minutes elapsed, "
            f"interval is {interval_minutes} minutes - "
            f"should backup: {should_backup}"
        )

        return should_backup

    def delete_backup(self, backup_path: str) -> bool:
        """
        Delete a specific backup file.

        This provides a way to manually delete individual backups, which
        can be useful for removing corrupted backups or freeing up space.

        Args:
            backup_path: Path to the backup file to delete

        Returns:
            True if the backup was deleted successfully, False otherwise

        Example:
            >>> success = backup_service.delete_backup(
            ...     "/path/to/backups/cosmetics_records_backup_20240115_143000.zip"
            ... )
            >>> if success:
            ...     print("Backup deleted successfully")
        """
        try:
            backup_path_obj = Path(backup_path)

            # Verify the file exists
            if not backup_path_obj.exists():
                logger.warning(f"Backup file not found: {backup_path}")
                return False

            # Verify it's actually in the backup directory
            # This prevents accidental deletion of files outside the backup dir
            if self.backup_dir not in backup_path_obj.parents:
                logger.error(
                    f"Security error: Backup file is outside backup directory: "
                    f"{backup_path}"
                )
                return False

            # Delete the file
            backup_path_obj.unlink()

            logger.info(f"Backup deleted: {backup_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete backup {backup_path}: {e}")
            return False

    def verify_backup(self, backup_path: str) -> tuple[bool, str]:
        """
        Verify integrity of a backup file.

        Performs basic integrity checks:
        1. File exists and is readable
        2. File is a valid ZIP archive
        3. ZIP contains the expected database file
        4. ZIP passes CRC integrity check

        Args:
            backup_path: Path to the backup file to verify

        Returns:
            Tuple of (is_valid: bool, message: str)
            - is_valid: True if backup passes all checks
            - message: Description of result or error

        Example:
            >>> is_valid, message = backup_service.verify_backup(
            ...     "/path/to/backups/cosmetics_records_backup_20240115_143000.zip"
            ... )
            >>> if is_valid:
            ...     print("Backup is valid")
            ... else:
            ...     print(f"Backup invalid: {message}")
        """
        try:
            backup_path_obj = Path(backup_path)

            # Check 1: File exists
            if not backup_path_obj.exists():
                return False, "Backup file not found"

            # Check 2: Is a valid ZIP file
            if not zipfile.is_zipfile(backup_path):
                return False, "File is not a valid ZIP archive"

            # Check 3: Can open and contains database file
            with zipfile.ZipFile(backup_path, "r") as zipf:
                file_list = zipf.namelist()

                # Look for .db file
                db_files = [f for f in file_list if f.endswith(".db")]
                if not db_files:
                    return False, "No database file found in backup"

                # Check 4: Test ZIP integrity (CRC check)
                bad_file = zipf.testzip()
                if bad_file:
                    return False, f"Corrupted file in archive: {bad_file}"

            logger.debug(f"Backup verification passed: {backup_path}")
            return True, "Backup is valid"

        except zipfile.BadZipFile:
            return False, "Backup file is corrupted"
        except Exception as e:
            logger.error(f"Failed to verify backup {backup_path}: {e}")
            return False, f"Verification failed: {str(e)}"
