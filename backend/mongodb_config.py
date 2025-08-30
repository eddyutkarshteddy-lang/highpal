"""
MongoDB Atlas Configuration for HighPal
Handles connection setup and database configuration
"""

import os
import logging
from typing import Optional
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

class MongoDBConfig:
    """MongoDB Atlas configuration and connection manager"""
    
    def __init__(self):
        self.connection_string: Optional[str] = None
        self.database_name: str = "highpal_documents"
        self.collection_name: str = "documents"
        self.client: Optional[MongoClient] = None
        self.database: Optional[Database] = None
        self.collection: Optional[Collection] = None
        
        # Load configuration
        self._load_config()
    
    def _load_config(self):
        """Load MongoDB configuration from environment variables"""
        # Try to get MongoDB connection string from environment
        self.connection_string = os.getenv('MONGODB_CONNECTION_STRING')
        self.database_name = os.getenv('MONGODB_DATABASE', 'highpal_documents')
        self.collection_name = os.getenv('MONGODB_COLLECTION', 'documents')
        
        if not self.connection_string:
            logger.warning("MongoDB connection string not found in environment variables")
            logger.info("Please set MONGODB_CONNECTION_STRING in your .env file")
    
    def connect(self) -> bool:
        """Connect to MongoDB Atlas"""
        if not self.connection_string:
            logger.error("No MongoDB connection string provided")
            return False
        
        try:
            # Create MongoDB client
            self.client = MongoClient(self.connection_string)
            
            # Test the connection
            self.client.admin.command('ping')
            
            # Get database and collection
            self.database = self.client[self.database_name]
            self.collection = self.database[self.collection_name]
            
            logger.info(f"✅ Connected to MongoDB Atlas database: {self.database_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB Atlas: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB Atlas")
    
    def get_collection(self) -> Optional[Collection]:
        """Get the documents collection"""
        if not self.collection:
            if not self.connect():
                return None
        return self.collection
    
    def test_connection(self) -> dict:
        """Test MongoDB connection and return status"""
        try:
            if self.connect():
                # Get database stats
                stats = self.database.command("dbstats")
                return {
                    "status": "connected",
                    "database": self.database_name,
                    "collection": self.collection_name,
                    "server_info": self.client.server_info(),
                    "document_count": self.collection.count_documents({}),
                    "database_size": stats.get("dataSize", 0)
                }
            else:
                return {
                    "status": "failed",
                    "error": "Could not establish connection"
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def is_configured(self) -> bool:
        """Check if MongoDB is properly configured"""
        return self.connection_string is not None

# Global MongoDB configuration instance
mongodb_config = MongoDBConfig()

def get_mongodb_config() -> MongoDBConfig:
    """Get the global MongoDB configuration instance"""
    return mongodb_config
