"""
LightSQL - Traditional SQL table interface for SQLite
Provides row-based storage with schema definitions and query capabilities
"""

import sqlite3
from typing import Any, Dict, List, Optional, Union


class Table:
    """
    A traditional SQL table with schema definition and query methods.

    Usage:
        from lightdb import Table

        users = Table('users', schema={
            'id': 'TEXT PRIMARY KEY',
            'username': 'TEXT NOT NULL',
            'email': 'TEXT',
            'role': 'TEXT DEFAULT "user"'
        })

        users.insert({'id': 'user_001', 'username': 'andrew', 'email': 'andrew@example.com'})
        user = users.find_one(username='andrew')
        admins = users.find(role='admin')
    """

    def __init__(self, table_name: str, schema: Dict[str, str] = None, connection=None):
        """
        Initialize a SQL table.

        Args:
            table_name: Name of the table
            schema: Dict mapping column names to SQL type definitions
                   Example: {'id': 'TEXT PRIMARY KEY', 'name': 'TEXT NOT NULL'}
            connection: SQLite connection object (if None, creates from config)
        """
        if connection is None:
            from .dbconnect import get_connection
            connection = get_connection()

        self.conn = connection
        self.table_name = self._validate_table_name(table_name)
        self.schema = schema or {}

        if self.schema:
            self._create_table()

    def _validate_table_name(self, table_name: str) -> str:
        """Validate table name to prevent SQL injection."""
        if not table_name:
            raise ValueError("Table name cannot be empty")

        if not all(c.isalnum() or c == '_' for c in table_name):
            raise ValueError(
                f"Invalid table name '{table_name}'. "
                "Table names can only contain letters, numbers, and underscores."
            )

        if table_name[0].isdigit():
            raise ValueError("Table name cannot start with a number")

        return table_name

    def _validate_column_name(self, column_name: str) -> str:
        """Validate column name to prevent SQL injection."""
        if not all(c.isalnum() or c == '_' for c in column_name):
            raise ValueError(
                f"Invalid column name '{column_name}'. "
                "Column names can only contain letters, numbers, and underscores."
            )
        return column_name

    def _create_table(self):
        """Create the table with the specified schema."""
        if not self.schema:
            raise ValueError("Schema is required to create table")

        for col in self.schema.keys():
            self._validate_column_name(col)

        cursor = self.conn.cursor()
        cursor.execute(f'DROP TABLE IF EXISTS {self.table_name}')

        columns_sql = ', '.join([f"{col} {definition}"
                                for col, definition in self.schema.items()])

        cursor.execute(f'''
            CREATE TABLE {self.table_name} (
                {columns_sql}
            )
        ''')
        self.conn.commit()

    def insert(self, record: Dict[str, Any]) -> None:
        """
        Insert a record into the table.
        Translates to: INSERT INTO table (col1, col2, ...) VALUES (?, ?, ...)

        Args:
            record: Dict mapping column names to values
        """
        if not record:
            raise ValueError("Record cannot be empty")

        for col in record.keys():
            self._validate_column_name(col)

        columns = ', '.join(record.keys())
        placeholders = ', '.join(['?' for _ in record])
        values = tuple(record.values())

        cursor = self.conn.cursor()
        cursor.execute(
            f'INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})',
            values
        )
        self.conn.commit()

    def insert_many(self, records: List[Dict[str, Any]]) -> None:
        """
        Insert multiple records at once.

        Args:
            records: List of dicts, each representing a record
        """
        if not records:
            return

        columns = list(records[0].keys())
        for col in columns:
            self._validate_column_name(col)

        columns_sql = ', '.join(columns)
        placeholders = ', '.join(['?' for _ in columns])

        cursor = self.conn.cursor()
        for record in records:
            values = tuple(record.get(col) for col in columns)
            cursor.execute(
                f'INSERT INTO {self.table_name} ({columns_sql}) VALUES ({placeholders})',
                values
            )
        self.conn.commit()

    def find(self, **conditions) -> List[Dict[str, Any]]:
        """
        Find all records matching the conditions.
        Translates to: SELECT * FROM table WHERE col1 = ? AND col2 = ?

        Args:
            **conditions: Column-value pairs to match

        Returns:
            List of records as dicts
        """
        cursor = self.conn.cursor()

        if conditions:
            for col in conditions.keys():
                self._validate_column_name(col)

            where_clause = ' AND '.join([f"{col} = ?" for col in conditions.keys()])
            values = tuple(conditions.values())
            cursor.execute(
                f'SELECT * FROM {self.table_name} WHERE {where_clause}',
                values
            )
        else:
            cursor.execute(f'SELECT * FROM {self.table_name}')

        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def find_one(self, **conditions) -> Optional[Dict[str, Any]]:
        """
        Find the first record matching the conditions.

        Args:
            **conditions: Column-value pairs to match

        Returns:
            Record as dict, or None if not found
        """
        results = self.find(**conditions)
        return results[0] if results else None

    def update(self, conditions: Dict[str, Any], updates: Dict[str, Any]) -> int:
        """
        Update records matching the conditions.
        Translates to: UPDATE table SET col1 = ?, col2 = ? WHERE col3 = ?

        Args:
            conditions: Dict of column-value pairs to match (WHERE clause)
            updates: Dict of column-value pairs to update (SET clause)

        Returns:
            Number of rows updated
        """
        if not updates:
            raise ValueError("Updates cannot be empty")

        for col in updates.keys():
            self._validate_column_name(col)
        for col in conditions.keys():
            self._validate_column_name(col)

        set_clause = ', '.join([f"{col} = ?" for col in updates.keys()])
        set_values = tuple(updates.values())

        cursor = self.conn.cursor()

        if conditions:
            where_clause = ' AND '.join([f"{col} = ?" for col in conditions.keys()])
            where_values = tuple(conditions.values())
            cursor.execute(
                f'UPDATE {self.table_name} SET {set_clause} WHERE {where_clause}',
                set_values + where_values
            )
        else:
            cursor.execute(
                f'UPDATE {self.table_name} SET {set_clause}',
                set_values
            )

        self.conn.commit()
        return cursor.rowcount

    def delete(self, **conditions) -> int:
        """
        Delete records matching the conditions.
        Translates to: DELETE FROM table WHERE col1 = ? AND col2 = ?

        Args:
            **conditions: Column-value pairs to match

        Returns:
            Number of rows deleted
        """
        cursor = self.conn.cursor()

        if conditions:
            for col in conditions.keys():
                self._validate_column_name(col)

            where_clause = ' AND '.join([f"{col} = ?" for col in conditions.keys()])
            values = tuple(conditions.values())
            cursor.execute(
                f'DELETE FROM {self.table_name} WHERE {where_clause}',
                values
            )
        else:
            cursor.execute(f'DELETE FROM {self.table_name}')

        self.conn.commit()
        return cursor.rowcount

    def count(self, **conditions) -> int:
        """
        Count records matching the conditions.
        Translates to: SELECT COUNT(*) FROM table WHERE ...

        Args:
            **conditions: Column-value pairs to match

        Returns:
            Number of matching records
        """
        cursor = self.conn.cursor()

        if conditions:
            for col in conditions.keys():
                self._validate_column_name(col)

            where_clause = ' AND '.join([f"{col} = ?" for col in conditions.keys()])
            values = tuple(conditions.values())
            cursor.execute(
                f'SELECT COUNT(*) FROM {self.table_name} WHERE {where_clause}',
                values
            )
        else:
            cursor.execute(f'SELECT COUNT(*) FROM {self.table_name}')

        return cursor.fetchone()[0]

    def all(self) -> List[Dict[str, Any]]:
        """
        Get all records in the table.

        Returns:
            List of all records as dicts
        """
        return self.find()

    def clear(self) -> int:
        """
        Delete all records from the table.

        Returns:
            Number of rows deleted
        """
        return self.delete()

    def drop(self):
        """Drop (delete) the entire table."""
        cursor = self.conn.cursor()
        cursor.execute(f'DROP TABLE IF EXISTS {self.table_name}')
        self.conn.commit()

    def __len__(self) -> int:
        """Return the number of records in the table."""
        return self.count()

    def __repr__(self) -> str:
        """String representation of the table."""
        return f"<Table '{self.table_name}' records={len(self)}>"
