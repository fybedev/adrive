"""
LightDB - Dictionary-like interface for SQLite database
Translates dict operations to SQL automatically
"""

import sqlite3
import json
from typing import Any, Iterator


class ListProxy(list):
    """
    A list proxy that automatically saves changes back to the database.
    Intercepts mutation methods to trigger database updates.
    """
    
    def __init__(self, data, db, key):
        super().__init__(data)
        self._db = db
        self._key = key
    
    def _save(self):
        """Save the current state back to the database."""
        self._db[self._key] = list(self)
    
    def append(self, item):
        super().append(item)
        self._save()
    
    def extend(self, items):
        super().extend(items)
        self._save()
    
    def insert(self, index, item):
        super().insert(index, item)
        self._save()
    
    def remove(self, item):
        super().remove(item)
        self._save()
    
    def pop(self, index=-1):
        result = super().pop(index)
        self._save()
        return result
    
    def clear(self):
        super().clear()
        self._save()
    
    def sort(self, *args, **kwargs):
        super().sort(*args, **kwargs)
        self._save()
    
    def reverse(self):
        super().reverse()
        self._save()
    
    def __setitem__(self, index, value):
        super().__setitem__(index, value)
        self._save()
    
    def __delitem__(self, index):
        super().__delitem__(index)
        self._save()
    
    def __iadd__(self, other):
        result = super().__iadd__(other)
        self._save()
        return result
    
    def __imul__(self, other):
        result = super().__imul__(other)
        self._save()
        return result


class DictProxy(dict):
    """
    A dict proxy that automatically saves changes back to the database.
    Intercepts mutation methods to trigger database updates.
    """
    
    def __init__(self, data, db, key):
        super().__init__(data)
        self._db = db
        self._key = key
    
    def _save(self):
        """Save the current state back to the database."""
        self._db[self._key] = dict(self)
    
    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self._save()
    
    def __delitem__(self, key):
        super().__delitem__(key)
        self._save()
    
    def pop(self, *args):
        result = super().pop(*args)
        self._save()
        return result
    
    def popitem(self):
        result = super().popitem()
        self._save()
        return result
    
    def clear(self):
        super().clear()
        self._save()
    
    def update(self, *args, **kwargs):
        super().update(*args, **kwargs)
        self._save()
    
    def setdefault(self, key, default=None):
        result = super().setdefault(key, default)
        self._save()
        return result


class LightDB:
    """
    A dictionary-like interface for SQLite database.
    
    Usage:
        from lightdb import LightDB
        
        db = LightDB()
        db['key'] = 'value'          # Insert/Update
        value = db['key']            # Retrieve
        del db['key']                # Delete
        'key' in db                  # Check existence
        len(db)                      # Count entries
    """
    
    def __init__(self, connection=None, table_name='keyvalue'):
        """
        Initialize LightDB instance.
        
        Args:
            connection: SQLite connection object (if None, creates from config)
            table_name: Name of the table to use for key-value storage
        """
        if connection is None:
            from .dbconnect import get_connection
            connection = get_connection()
        
        self.conn = connection
        self.table_name = self._validate_table_name(table_name)
        self._initialize_table()
    
    def _validate_table_name(self, table_name: str) -> str:
        """
        Validate and sanitize table name to prevent SQL injection.
        Table names must be alphanumeric with underscores only.
        """
        if not table_name:
            raise ValueError("Table name cannot be empty")
        
        # Allow only alphanumeric characters and underscores
        if not all(c.isalnum() or c == '_' for c in table_name):
            raise ValueError(
                f"Invalid table name '{table_name}'. "
                "Table names can only contain letters, numbers, and underscores."
            )
        
        # Prevent table names starting with numbers (SQLite limitation)
        if table_name[0].isdigit():
            raise ValueError("Table name cannot start with a number")
        
        return table_name
    
    def _initialize_table(self):
        """Create the key-value table if it doesn't exist."""
        cursor = self.conn.cursor()
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        ''')
        self.conn.commit()
    
    def _serialize_value(self, value: Any) -> str:
        """Convert Python value to JSON string for storage."""
        return json.dumps(value)
    
    def _deserialize_value(self, value: str) -> Any:
        """Convert JSON string back to Python value."""
        return json.loads(value)
    
    def __setitem__(self, key: str, value: Any):
        """
        Set a key-value pair in the database.
        Translates to: INSERT OR REPLACE INTO table (key, value) VALUES (?, ?)
        """
        cursor = self.conn.cursor()
        serialized_value = self._serialize_value(value)
        cursor.execute(
            f'INSERT OR REPLACE INTO {self.table_name} (key, value) VALUES (?, ?)',
            (key, serialized_value)
        )
        self.conn.commit()
    
    def __getitem__(self, key: str) -> Any:
        """
        Get a value by key from the database.
        Translates to: SELECT value FROM table WHERE key = ?
        Raises KeyError if key doesn't exist.
        Returns ListProxy for lists and DictProxy for dicts to enable auto-saving.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            f'SELECT value FROM {self.table_name} WHERE key = ?',
            (key,)
        )
        result = cursor.fetchone()
        
        if result is None:
            raise KeyError(key)
        
        value = self._deserialize_value(result[0])
        
        # Return proxies for mutable types to enable auto-saving
        if isinstance(value, list):
            return ListProxy(value, self, key)
        elif isinstance(value, dict):
            return DictProxy(value, self, key)
        
        return value
    
    def __delitem__(self, key: str):
        """
        Delete a key-value pair from the database.
        Translates to: DELETE FROM table WHERE key = ?
        Raises KeyError if key doesn't exist.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            f'DELETE FROM {self.table_name} WHERE key = ?',
            (key,)
        )
        
        if cursor.rowcount == 0:
            raise KeyError(key)
        
        self.conn.commit()
    
    def __contains__(self, key: str) -> bool:
        """
        Check if a key exists in the database.
        Translates to: SELECT 1 FROM table WHERE key = ? LIMIT 1
        """
        cursor = self.conn.cursor()
        cursor.execute(
            f'SELECT 1 FROM {self.table_name} WHERE key = ? LIMIT 1',
            (key,)
        )
        return cursor.fetchone() is not None
    
    def __len__(self) -> int:
        """
        Return the number of key-value pairs in the database.
        Translates to: SELECT COUNT(*) FROM table
        """
        cursor = self.conn.cursor()
        cursor.execute(f'SELECT COUNT(*) FROM {self.table_name}')
        return cursor.fetchone()[0]
    
    def __iter__(self) -> Iterator[str]:
        """
        Iterate over all keys in the database.
        Translates to: SELECT key FROM table
        """
        cursor = self.conn.cursor()
        cursor.execute(f'SELECT key FROM {self.table_name}')
        for row in cursor:
            yield row[0]
    
    def keys(self) -> list:
        """Return a list of all keys."""
        return list(self.__iter__())
    
    def values(self) -> list:
        """Return a list of all values."""
        cursor = self.conn.cursor()
        cursor.execute(f'SELECT value FROM {self.table_name}')
        return [self._deserialize_value(row[0]) for row in cursor]
    
    def items(self) -> list:
        """Return a list of (key, value) tuples."""
        cursor = self.conn.cursor()
        cursor.execute(f'SELECT key, value FROM {self.table_name}')
        return [(row[0], self._deserialize_value(row[1])) for row in cursor]
    
    def get(self, key: str, default=None) -> Any:
        """
        Get a value by key, returning default if key doesn't exist.
        Returns ListProxy for lists and DictProxy for dicts to enable auto-saving.
        """
        try:
            return self[key]
        except KeyError:
            # If default is a mutable type and key doesn't exist, store it first
            if default is not None and isinstance(default, (list, dict)):
                self[key] = default
                return self[key]
            return default
    
    def clear(self):
        """
        Remove all key-value pairs from the database.
        Translates to: DELETE FROM table
        """
        cursor = self.conn.cursor()
        cursor.execute(f'DELETE FROM {self.table_name}')
        self.conn.commit()
    
    def update(self, other=None, **kwargs):
        """
        Update the database with key-value pairs from dict or kwargs.
        """
        if other is not None:
            if hasattr(other, 'items'):
                for key, value in other.items():
                    self[key] = value
            else:
                for key, value in other:
                    self[key] = value
        
        for key, value in kwargs.items():
            self[key] = value
    
    def __repr__(self) -> str:
        """String representation of the database."""
        return f"<LightDB table='{self.table_name}' entries={len(self)}>"
    
    def close(self):
        """Close the database connection."""
        self.conn.close()
