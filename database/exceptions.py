"""
Custom exceptions for database operations.
"""

class DatabaseConnectionError(Exception):
    """Custom exception for database connection issues"""
    pass


class DatabaseOperationError(Exception):
    """Custom exception for database operation issues"""
    pass