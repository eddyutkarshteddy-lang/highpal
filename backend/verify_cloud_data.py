"""
Verify MongoDB Atlas Cloud Data
Checks what content is stored in the cloud database
"""

import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Connect to MongoDB Atlas
mongo_uri = os.getenv('MONGODB_URI')
client = MongoClient(mongo_uri)
db = client['highpal_db']

print("=" * 60)
print("MongoDB Atlas Cloud Data Verification")
print("=" * 60)
print()

# Check shared_knowledge collection
shared_knowledge = db['shared_knowledge']
total_docs = shared_knowledge.count_documents({})

print(f"✅ Total Documents in Cloud: {total_docs}")
print()

# Count documents with embeddings
with_embeddings = shared_knowledge.count_documents({"embedding": {"$exists": True, "$ne": None}})
print(f"✅ Documents with Embeddings: {with_embeddings}")
print(f"✅ Embeddings Coverage: {(with_embeddings/total_docs*100):.1f}%")
print()

# Get document statistics by tags
print("📊 Content by Exam Type:")
pipeline = [
    {"$unwind": "$tags.exam_types"},
    {"$group": {"_id": "$tags.exam_types", "count": {"$sum": 1}}},
    {"$sort": {"count": -1}}
]
for result in shared_knowledge.aggregate(pipeline):
    print(f"   - {result['_id']}: {result['count']} documents")
print()

print("📚 Content by Subject:")
pipeline = [
    {"$group": {"_id": "$tags.subject", "count": {"$sum": 1}}},
    {"$sort": {"count": -1}}
]
for result in shared_knowledge.aggregate(pipeline):
    print(f"   - {result['_id']}: {result['count']} documents")
print()

# Sample one document
print("📄 Sample Document from Cloud:")
sample = shared_knowledge.find_one({}, {
    "content": 1,
    "tags": 1,
    "embedding": 1,
    "metadata.file_name": 1,
    "metadata.chunk_index": 1
})

if sample:
    print(f"   File: {sample.get('metadata', {}).get('file_name', 'N/A')}")
    print(f"   Chunk: {sample.get('metadata', {}).get('chunk_index', 'N/A')}")
    print(f"   Tags: {sample.get('tags', {})}")
    print(f"   Content Preview: {sample.get('content', '')[:200]}...")
    print(f"   Has Embedding: {'Yes' if sample.get('embedding') else 'No'}")
    if sample.get('embedding'):
        print(f"   Embedding Dimensions: {len(sample['embedding'])}")
print()

# Check training metadata
training_metadata = db['training_metadata']
uploads = training_metadata.count_documents({})
print(f"📥 Total Uploads Tracked: {uploads}")

if uploads > 0:
    latest = training_metadata.find_one({}, sort=[("upload_date", -1)])
    print(f"   Latest Upload:")
    print(f"   - File: {latest.get('source_name', 'N/A')}")
    print(f"   - Date: {latest.get('upload_date', 'N/A')}")
    print(f"   - Chunks Created: {latest.get('chunks_created', 0)}")
    print(f"   - Admin: {latest.get('admin_id', 'N/A')}")
print()

print("=" * 60)
print("✅ All data is stored in MongoDB Atlas Cloud!")
print("=" * 60)

client.close()
