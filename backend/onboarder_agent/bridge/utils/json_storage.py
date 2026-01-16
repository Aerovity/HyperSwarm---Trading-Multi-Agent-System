"""
Thread-safe JSON file storage manager for persistent data.
Provides atomic writes and rolling window functionality.
"""

import json
import os
from pathlib import Path
from typing import Any, List
from threading import Lock
import logging

logger = logging.getLogger(__name__)


class JSONStorage:
    """Thread-safe JSON file storage manager"""

    def __init__(self, data_dir: str = None):
        """
        Initialize JSON storage.

        Args:
            data_dir: Directory for JSON files (default from settings)
        """
        if data_dir is None:
            from django.conf import settings
            data_dir = settings.DATA_DIR

        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.locks = {}

    def _get_lock(self, filename: str) -> Lock:
        """Get or create lock for specific file"""
        if filename not in self.locks:
            self.locks[filename] = Lock()
        return self.locks[filename]

    def read(self, filename: str, default: Any = None) -> Any:
        """
        Thread-safe read from JSON file.

        Args:
            filename: Name of file to read
            default: Default value if file doesn't exist

        Returns:
            Parsed JSON data or default value
        """
        filepath = self.data_dir / filename
        lock = self._get_lock(filename)

        with lock:
            if not filepath.exists():
                return default if default is not None else []

            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                logger.error(f"Corrupted JSON file {filename}: {e}")
                return default if default is not None else []
            except Exception as e:
                logger.error(f"Failed to read {filename}: {e}")
                return default if default is not None else []

    def write(self, filename: str, data: Any):
        """
        Thread-safe write to JSON file.

        Uses atomic write pattern with temp file.

        Args:
            filename: Name of file to write
            data: Data to serialize to JSON
        """
        filepath = self.data_dir / filename
        lock = self._get_lock(filename)

        with lock:
            try:
                # Write to temp file first
                temp_path = filepath.with_suffix('.tmp')
                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, default=str)

                # Atomic rename
                temp_path.replace(filepath)
            except Exception as e:
                logger.error(f"Failed to write {filename}: {e}")
                raise

    def append(self, filename: str, item: Any, max_items: int = 1000):
        """
        Append item to JSON array file with rolling window.

        Args:
            filename: Name of file to append to
            item: Item to append (must be JSON serializable)
            max_items: Maximum items to keep (rolling window)
        """
        data = self.read(filename, default=[])
        data.insert(0, item)  # Add to front

        # Rolling window: keep only last N items
        data = data[:max_items]

        self.write(filename, data)
