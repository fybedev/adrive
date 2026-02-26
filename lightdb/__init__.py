"""
LightDB by Andrew (Fybe)

A lightweight database library with two interfaces:

1. LightDB - Dictionary-like key-value store (simple, fast)
2. Table - Traditional SQL tables with schemas (powerful, queryable)

Choose the one that fits your needs!

https://www.fybe.dev/
"""

from .lightdb import LightDB
from .lightsql import Table
from .dbconnect import get_connection

connection = get_connection()

__all__ = ['LightDB', 'Table', 'get_connection']