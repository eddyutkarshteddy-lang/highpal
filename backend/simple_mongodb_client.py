"""
Simple MongoDB Atlas Client - Direct Cloud Storage
Saves data directly to MongoDB Atlas without Haystack
"""
import os
import json
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SimpleMongoClient:
    def __init__(self):
        self.connection_string = os.getenv('MONGODB_CONNECTION_STRING')
        self.database_name = os.getenv('MONGODB_DATABASE', 'highpal_documents')
        self.collection_name = os.getenv('MONGODB_COLLECTION', 'documents')
        
        self.client = None
        self.database = None
        self.collection = None
        
        self.connect()
    
    def connect(self):
        """Connect to MongoDB Atlas"""
        try:
            print("🔗 Connecting to MongoDB Atlas...")
            
            # Create client with connection string
            self.client = MongoClient(
                self.connection_string,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=5000,
                socketTimeoutMS=5000
            )
            
            # Test connection
            self.client.admin.command('ping')
            print("✅ Connected to MongoDB Atlas successfully!")
            
            # Get database and collection
            self.database = self.client[self.database_name]
            self.collection = self.database[self.collection_name]
            
            return True
            
        except ConnectionFailure as e:
            print(f"❌ Failed to connect to MongoDB Atlas: {e}")
            return False
        except Exception as e:
            print(f"❌ MongoDB connection error: {e}")
            return False
    
    def save_document(self, content, metadata):
        """Save document directly to MongoDB Atlas"""
        try:
            if not self.collection:
                raise Exception("Not connected to MongoDB Atlas")
            
            # Create document structure
            document = {
                "content": content,
                "metadata": metadata,
                "upload_date": datetime.now().isoformat(),
                "storage_type": "mongodb_atlas"
            }
            
            # Insert document
            result = self.collection.insert_one(document)
            doc_id = str(result.inserted_id)
            
            print(f"✅ Document saved to MongoDB Atlas: {doc_id}")
            return doc_id
            
        except Exception as e:
            print(f"❌ Failed to save document: {e}")
            raise
    
    def get_all_documents(self):
        """Get all documents from MongoDB Atlas"""
        try:
            if not self.collection:
                raise Exception("Not connected to MongoDB Atlas")
            
            documents = []
            for doc in self.collection.find():
                doc['_id'] = str(doc['_id'])  # Convert ObjectId to string
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            print(f"❌ Failed to get documents: {e}")
            return []
    
    def get_statistics(self):
        """Get database statistics"""
        try:
            if not self.collection:
                return {"error": "Not connected"}
            
            total_docs = self.collection.count_documents({})
            
            # Calculate total characters
            pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "total_chars": {"$sum": {"$strLenCP": "$content"}},
                        "total_docs": {"$sum": 1}
                    }
                }
            ]
            
            result = list(self.collection.aggregate(pipeline))
            total_chars = result[0]["total_chars"] if result else 0
            
            return {
                "total_documents": total_docs,
                "total_characters": total_chars,
                "average_length": total_chars // total_docs if total_docs > 0 else 0,
                "storage_type": "mongodb_atlas",
                "connection_status": "connected"
            }
            
        except Exception as e:
            print(f"❌ Statistics error: {e}")
            return {"error": str(e)}
    
    def delete_document(self, doc_id):
        """Delete document by ID"""
        try:
            from bson import ObjectId
            
            if not self.collection:
                raise Exception("Not connected to MongoDB Atlas")
            
            result = self.collection.delete_one({"_id": ObjectId(doc_id)})
            return result.deleted_count > 0
            
        except Exception as e:
            print(f"❌ Delete error: {e}")
            return False
    
    def test_connection(self):
        """Test MongoDB Atlas connection"""
        try:
            if not self.client:
                return False
            
            # Ping the database
            self.client.admin.command('ping')
            print("🟢 MongoDB Atlas connection is working!")
            
            # Test write operation
            test_doc = {
                "test": True,
                "timestamp": datetime.now().isoformat(),
                "message": "Connection test successful"
            }
            
            result = self.collection.insert_one(test_doc)
            print(f"✅ Test document inserted: {result.inserted_id}")
            
            # Clean up test document
            self.collection.delete_one({"_id": result.inserted_id})
            print("🧹 Test document cleaned up")
            
            return True
            
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False

# Test the connection
if __name__ == "__main__":
    print("🚀 Testing MongoDB Atlas Direct Connection...")
    print("=" * 50)
    
    mongo_client = SimpleMongoClient()
    
    if mongo_client.test_connection():
        print("\n🎉 SUCCESS! MongoDB Atlas is ready for direct storage!")
        
        # Show statistics
        stats = mongo_client.get_statistics()
        print(f"\n📊 Current Database Stats:")
        print(f"   Documents: {stats.get('total_documents', 0)}")
        print(f"   Characters: {stats.get('total_characters', 0):,}")
        print(f"   Storage: {stats.get('storage_type', 'unknown')}")
        
    else:
        print("\n❌ MongoDB Atlas connection failed!")
        print("Check your connection string and credentials.")
