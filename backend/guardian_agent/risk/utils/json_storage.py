"""
Thread-safe JSON file storage for Guardian Agent.
Provides persistent cold storage for historical data.
"""

import json
import os
import logging
import threading
from typing import Any, Optional, List
from django.conf import settings

logger = logging.getLogger(__name__)


class JSONStorage:
    """Thread-safe JSON file storage manager"""

    def __init__(self):
        """Initialize storage with data directory from settings"""
        self.data_dir = getattr(settings, 'DATA_DIR', './data')
        self._locks = {}
        self._locks_lock = threading.Lock()

        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
        logger.info(f"JSON storage initialized at {self.data_dir}")

    def _get_lock(self, filename: str) -> threading.Lock:
        """Get or create lock for a specific file"""
        with self._locks_lock:
            if filename not in self._locks:
                self._locks[filename] = threading.Lock()
            return self._locks[filename]

    def _get_filepath(self, filename: str) -> str:
        """Get full file path"""
        return os.path.join(self.data_dir, filename)

    def read(self, filename: str, default: Any = None) -> Any:
        """
        Thread-safe JSON file read.

        Args:
            filename: Name of file to read
            default: Default value if file doesn't exist

        Returns:
            Parsed JSON data or default
        """
        filepath = self._get_filepath(filename)
        lock = self._get_lock(filename)

        with lock:
            try:
                if not os.path.exists(filepath):
                    return default

                with open(filepath, 'r') as f:
                    return json.load(f)

            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error in {filename}: {e}")
                return default
            except Exception as e:
                logger.error(f"Error reading {filename}: {e}")
                return default

    def write(self, filename: str, data: Any):
        """
        Atomic write to JSON file.
        Uses temp file + rename pattern for atomicity.

        Args:
            filename: Name of file to write
            data: Data to serialize as JSON
        """
        filepath = self._get_filepath(filename)
        temp_filepath = filepath + '.tmp'
        lock = self._get_lock(filename)

        with lock:
            try:
                # Write to temp file
                with open(temp_filepath, 'w') as f:
                    json.dump(data, f, indent=2, default=str)

                # Atomic rename
                os.replace(temp_filepath, filepath)
                logger.debug(f"Wrote {filename}")

            except Exception as e:
                logger.error(f"Error writing {filename}: {e}")
                # Clean up temp file if it exists
                if os.path.exists(temp_filepath):
                    os.remove(temp_filepath)

    def append(self, filename: str, item: Any, max_items: int = 1000):
        """
        Append item to JSON array file with rolling window.

        Args:
            filename: Name of file (should contain array)
            item: Item to append
            max_items: Maximum items to keep (rolling window)
        """
        filepath = self._get_filepath(filename)
        lock = self._get_lock(filename)

        with lock:
            try:
                # Read existing data
                data = []
                if os.path.exists(filepath):
                    try:
                        with open(filepath, 'r') as f:
                            data = json.load(f)
                        if not isinstance(data, list):
                            data = []
                    except (json.JSONDecodeError, Exception):
                        data = []

                # Prepend new item (most recent first)
                data.insert(0, item)

                # Trim to max_items (rolling window)
                data = data[:max_items]

                # Write back
                temp_filepath = filepath + '.tmp'
                with open(temp_filepath, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
                os.replace(temp_filepath, filepath)

            except Exception as e:
                logger.error(f"Error appending to {filename}: {e}")

    def get_recent(self, filename: str, limit: int = 50) -> List[Any]:
        """
        Get recent items from JSON array file.

        Args:
            filename: Name of file (should contain array)
            limit: Maximum items to return

        Returns:
            List of recent items
        """
        data = self.read(filename, default=[])
        if isinstance(data, list):
            return data[:limit]
        return []


# Singleton instance
_storage_instance = None


def get_storage() -> JSONStorage:
    """Get or create JSON storage singleton"""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = JSONStorage()
    return _storage_instance
