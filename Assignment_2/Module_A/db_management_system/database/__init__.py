"""
database package
================
Lightweight DBMS powered by a B+ Tree index.

Exports
-------
BPlusTree, BPlusTreeNode   – core index structure
Table                       – single-table abstraction
DatabaseManager             – multi-database manager
BruteForceDB                – linear-scan baseline for benchmarking
PerformanceAnalyzer         – automated benchmarking suite
"""

from bplustree   import BPlusTree, BPlusTreeNode
from table       import Table
from db_manager  import DatabaseManager
from bruteforce  import BruteForceDB
from performance import PerformanceAnalyzer

__all__ = [
    "BPlusTree",
    "BPlusTreeNode",
    "Table",
    "DatabaseManager",
    "BruteForceDB",
    "PerformanceAnalyzer",
]
