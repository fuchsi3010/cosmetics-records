# =============================================================================
# Cosmetics Records - Configuration Management
# =============================================================================
# This module manages application configuration using a JSON file stored in
# the user's data directory.
#
# Key Features:
#   - Thread-safe singleton pattern ensures single config instance
#   - Automatic directory and file creation on first run
#   - Default values for all settings
#   - Type-safe access via properties
#   - Persistent storage in user data directory
#
# Configuration File Location:
#   Linux: ~/.local/share/cosmetics_records/config.json
#   Windows: %APPDATA%/cosmetics_records/config.json
#   macOS: ~/Library/Application Support/cosmetics_records/config.json
#
# Usage Example:
#   config = Config.get_instance()
#   theme = config.theme
#   config.theme = "dark"
#   config.save()
# =============================================================================

import json
import logging
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Optional

# Configure module logger
logger = logging.getLogger(__name__)


class Config:
    """
    Thread-safe singleton configuration manager.

    This class handles loading, saving, and accessing application settings.
    It uses the singleton pattern to ensure only one instance exists across
    the entire application.

    Attributes:
        theme: UI theme - "dark", "light", or "system"
        language: Application language - "en" or "de"
        ui_scale: UI scaling factor (0.8 to 2.0)
        auto_backup: Whether automatic backups are enabled
        backup_interval_minutes: How often to auto-backup (in minutes)
        backup_retention_count: How many backup files to keep
        last_backup_time: ISO timestamp of last backup
    """

    # Class-level attributes for singleton pattern
    _instance: Optional["Config"] = None
    _lock: Lock = Lock()  # Thread-safety lock for singleton creation

    # Instance attributes (type hints for mypy)
    _config_dir: Path
    _config_file: Path
    _settings: Dict[str, Any]

    def __new__(cls) -> "Config":
        """
        Implement singleton pattern with thread-safety.

        This ensures only one Config instance ever exists, even if multiple
        threads try to create instances simultaneously.

        Returns:
            Config: The singleton Config instance

        Note:
            The double-checked locking pattern is used here:
            1. Fast path: Check if instance exists (without lock)
            2. Slow path: If not, acquire lock and check again
            This minimizes lock contention after first initialization.
        """
        # Fast path: instance already exists
        if cls._instance is None:
            # Slow path: need to create instance with lock
            with cls._lock:
                # Double-check: another thread might have created it
                # while we were waiting for the lock
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """
        Initialize the configuration manager.

        This is called every time Config() is instantiated, but the actual
        initialization only happens once due to the _initialized flag.

        Note:
            WHY we need _initialized: __init__ is called every time even in
            a singleton, so we use this flag to prevent re-initialization.
        """
        # Only initialize once (singleton pattern)
        if hasattr(self, "_initialized"):
            return

        # Get the platform-appropriate user data directory
        self._config_dir = self._get_user_data_dir()
        self._config_file = self._config_dir / "config.json"

        # Internal settings dictionary
        self._settings: Dict[str, Any] = {}

        # Load existing config or create with defaults
        self._ensure_config_exists()
        self.load()

        # Mark as initialized
        self._initialized = True

        logger.info(f"Config initialized from {self._config_file}")

    @classmethod
    def get_instance(cls) -> "Config":
        """
        Get the singleton Config instance.

        This is the preferred way to access the configuration.

        Returns:
            Config: The singleton Config instance

        Example:
            config = Config.get_instance()
            print(config.theme)
        """
        return cls()

    def _get_user_data_dir(self) -> Path:
        """
        Get the platform-appropriate user data directory.

        Returns:
            Path: The directory where config.json should be stored

        Note:
            This follows the XDG Base Directory specification on Linux,
            and platform conventions on Windows/macOS.
        """
        import platform

        system = platform.system()

        if system == "Linux":
            # XDG Base Directory: ~/.local/share/cosmetics_records
            base = Path.home() / ".local" / "share"
        elif system == "Windows":
            # Windows AppData: %APPDATA%/cosmetics_records
            base = Path.home() / "AppData" / "Roaming"
        elif system == "Darwin":  # macOS
            # macOS Application Support: ~/Library/Application Support/cosmetics_records
            base = Path.home() / "Library" / "Application Support"
        else:
            # Fallback for unknown systems
            base = Path.home() / ".config"

        # Create the cosmetics_records subdirectory
        config_dir = base / "cosmetics_records"

        # Ensure the directory exists
        config_dir.mkdir(parents=True, exist_ok=True)

        return config_dir

    def _get_defaults(self) -> Dict[str, Any]:
        """
        Get default configuration values.

        Returns:
            Dict[str, Any]: Dictionary of default settings

        Note:
            These defaults are used when:
            1. Creating a new config file (first run)
            2. A setting is missing from the loaded config
        """
        return {
            # UI Theme Settings
            "theme": "system",  # Options: "dark", "light", "system"
            # Localization
            "language": "en",  # Options: "en", "de"
            "date_format": "language",  # Options: "language", "iso8601", "us", "de"
            "units_system": "metric",  # Options: "metric", "imperial"
            # UI Scaling
            "ui_scale": 1.0,  # Range: 0.8 to 2.0
            # Backup Settings
            "auto_backup": True,  # Enable automatic backups
            "backup_interval_minutes": 120,  # Backup every 2 hours
            "backup_retention_count": 25,  # Keep last 25 backups
            "last_backup_time": None,  # ISO format datetime string
            # Database Settings
            "database_path": None,  # Custom database path (None = default)
        }

    def _ensure_config_exists(self) -> None:
        """
        Ensure the config file exists, creating it with defaults if needed.

        This is called during initialization to handle first-run scenarios.

        Note:
            This method is idempotent - safe to call multiple times.
            If the file exists, it does nothing.
        """
        if not self._config_file.exists():
            logger.info(
                f"Config file not found, creating default at {self._config_file}"
            )
            # Create with default settings
            self._settings = self._get_defaults()
            self.save()
        else:
            logger.debug(f"Config file exists at {self._config_file}")

    def load(self) -> None:
        """
        Load configuration from the JSON file.

        This reads the config.json file and merges it with defaults.
        Any missing settings will use default values.

        Raises:
            RuntimeError: If the config file is corrupted or unreadable
        """
        try:
            with open(self._config_file, "r", encoding="utf-8") as f:
                loaded_settings = json.load(f)

            # Start with defaults
            self._settings = self._get_defaults()

            # Overlay loaded settings (this allows new defaults to be added
            # in future versions without breaking existing configs)
            self._settings.update(loaded_settings)

            logger.debug("Configuration loaded successfully")

        except json.JSONDecodeError as e:
            logger.error(f"Config file is corrupted: {e}")
            raise RuntimeError(
                f"Configuration file is corrupted and cannot be read. "
                f"Please delete {self._config_file} and restart the application. "
                f"Error: {e}"
            )
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise RuntimeError(f"Could not load configuration: {e}")

    def save(self) -> None:
        """
        Save current configuration to the JSON file.

        This writes the entire settings dictionary to config.json with
        pretty formatting for human readability.

        Raises:
            RuntimeError: If the config file cannot be written
        """
        try:
            with open(self._config_file, "w", encoding="utf-8") as f:
                # WHY indent=2: Makes the JSON file human-readable
                # WHY ensure_ascii=False: Allows proper UTF-8 encoding
                json.dump(self._settings, f, indent=2, ensure_ascii=False)

            logger.debug("Configuration saved successfully")

        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            raise RuntimeError(f"Could not save configuration: {e}")

    # =========================================================================
    # Property Accessors
    # =========================================================================
    # These provide type-safe access to configuration values with validation.
    # Using properties allows us to add validation logic and maintain
    # backwards compatibility if we change the internal storage format.

    @property
    def theme(self) -> str:
        """Get the current UI theme."""
        return str(self._settings.get("theme", "system"))

    @theme.setter
    def theme(self, value: str) -> None:
        """
        Set the UI theme.

        Args:
            value: Theme name - must be "dark", "light", or "system"

        Raises:
            ValueError: If value is not a valid theme
        """
        if value not in ["dark", "light", "system"]:
            raise ValueError(f"Invalid theme: {value}. Must be dark, light, or system")
        self._settings["theme"] = value

    @property
    def language(self) -> str:
        """Get the current application language."""
        return str(self._settings.get("language", "en"))

    @language.setter
    def language(self, value: str) -> None:
        """
        Set the application language.

        Args:
            value: Language code - must be "en" or "de"

        Raises:
            ValueError: If value is not a supported language
        """
        if value not in ["en", "de"]:
            raise ValueError(f"Invalid language: {value}. Must be en or de")
        self._settings["language"] = value

    @property
    def date_format(self) -> str:
        """Get the current date format setting."""
        return str(self._settings.get("date_format", "language"))

    @date_format.setter
    def date_format(self, value: str) -> None:
        """
        Set the date format.

        Args:
            value: Date format - must be "language", "iso8601", "us", or "de"

        Raises:
            ValueError: If value is not a valid date format
        """
        if value not in ["language", "iso8601", "us", "de"]:
            raise ValueError(
                f"Invalid date_format: {value}. Must be language, iso8601, us, or de"
            )
        self._settings["date_format"] = value

    @property
    def units_system(self) -> str:
        """Get the current units system (metric or imperial)."""
        return str(self._settings.get("units_system", "metric"))

    @units_system.setter
    def units_system(self, value: str) -> None:
        """
        Set the units system.

        Args:
            value: Units system - must be "metric" or "imperial"

        Raises:
            ValueError: If value is not a valid units system
        """
        if value not in ["metric", "imperial"]:
            raise ValueError(
                f"Invalid units_system: {value}. Must be metric or imperial"
            )
        self._settings["units_system"] = value

    @property
    def ui_scale(self) -> float:
        """Get the UI scaling factor."""
        return float(self._settings.get("ui_scale", 1.0))

    @ui_scale.setter
    def ui_scale(self, value: float) -> None:
        """
        Set the UI scaling factor.

        Args:
            value: Scale factor - must be between 0.8 and 2.0

        Raises:
            ValueError: If value is out of valid range
        """
        if not 0.8 <= value <= 2.0:
            raise ValueError(f"Invalid ui_scale: {value}. Must be between 0.8 and 2.0")
        self._settings["ui_scale"] = value

    @property
    def auto_backup(self) -> bool:
        """Get whether automatic backups are enabled."""
        return bool(self._settings.get("auto_backup", True))

    @auto_backup.setter
    def auto_backup(self, value: bool) -> None:
        """Set whether automatic backups are enabled."""
        self._settings["auto_backup"] = bool(value)

    @property
    def backup_interval_minutes(self) -> int:
        """Get the backup interval in minutes."""
        return int(self._settings.get("backup_interval_minutes", 120))

    @backup_interval_minutes.setter
    def backup_interval_minutes(self, value: int) -> None:
        """
        Set the backup interval in minutes.

        Args:
            value: Interval in minutes - must be positive

        Raises:
            ValueError: If value is not positive
        """
        if value <= 0:
            raise ValueError(
                f"Invalid backup_interval_minutes: {value}. Must be positive"
            )
        self._settings["backup_interval_minutes"] = value

    @property
    def backup_retention_count(self) -> int:
        """Get the number of backup files to retain."""
        return int(self._settings.get("backup_retention_count", 25))

    @backup_retention_count.setter
    def backup_retention_count(self, value: int) -> None:
        """
        Set the number of backup files to retain.

        Args:
            value: Number of backups to keep - must be positive

        Raises:
            ValueError: If value is not positive
        """
        if value <= 0:
            raise ValueError(
                f"Invalid backup_retention_count: {value}. Must be positive"
            )
        self._settings["backup_retention_count"] = value

    @property
    def last_backup_time(self) -> Optional[datetime]:
        """
        Get the last backup timestamp.

        Returns:
            Optional[datetime]: Last backup time, or None if never backed up
        """
        value = self._settings.get("last_backup_time")
        if value is None:
            return None

        # Parse ISO format datetime string
        try:
            return datetime.fromisoformat(value)
        except (ValueError, TypeError):
            logger.warning(f"Invalid last_backup_time format: {value}")
            return None

    @last_backup_time.setter
    def last_backup_time(self, value: Optional[datetime]) -> None:
        """
        Set the last backup timestamp.

        Args:
            value: Datetime to record, or None to clear
        """
        if value is None:
            self._settings["last_backup_time"] = None
        else:
            # Store as ISO format string for JSON compatibility
            self._settings["last_backup_time"] = value.isoformat()

    def reset_to_defaults(self) -> None:
        """
        Reset all settings to their default values.

        This is useful for troubleshooting or providing a "factory reset"
        feature in the settings UI.

        Note:
            This does not automatically save - call save() afterward.
        """
        self._settings = self._get_defaults()
        logger.info("Configuration reset to defaults")

    def get_config_dir(self) -> Path:
        """
        Get the configuration directory path.

        Returns:
            Path: The directory containing config.json

        Note:
            This is useful for storing other application data files
            (logs, backups, etc.) in the same location.
        """
        return self._config_dir

    @property
    def database_path(self) -> Optional[Path]:
        """
        Get the custom database path.

        Returns:
            Optional[Path]: Custom database path, or None if using default
        """
        value = self._settings.get("database_path")
        if value is None:
            return None
        return Path(value)

    @database_path.setter
    def database_path(self, value: Optional[Path]) -> None:
        """
        Set the custom database path.

        Args:
            value: Path to database file, or None to use default
        """
        if value is None:
            self._settings["database_path"] = None
        else:
            self._settings["database_path"] = str(value)

    def get_database_path(self) -> Path:
        """
        Get the effective database path.

        Returns:
            Path: The database path to use (custom or default)
        """
        custom_path = self.database_path
        if custom_path is not None:
            return custom_path
        return self._config_dir / "cosmetics_records.db"
