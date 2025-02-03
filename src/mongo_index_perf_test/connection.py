from typing import Optional
from pymongo import MongoClient, errors
from .config import logger

class MongoDBConnection:
    """MongoDB connection manager"""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.client: Optional[MongoClient] = None

    def __enter__(self):
        """Establish database connection"""
        try:
            self.client = MongoClient(self.connection_string)
            logger.info("Successfully connected to MongoDB")
            return self
        except errors.ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
