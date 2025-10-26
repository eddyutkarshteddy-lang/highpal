# Vector Search Setup Guide for MongoDB Atlas

This guide explains how to set up vector search in MongoDB Atlas for semantic search with OpenAI embeddings.

## Overview

The admin training system now supports **semantic search** using OpenAI's `text-embedding-3-small` model (1536 dimensions). This enables AI-powered search that understands meaning, not just keywords.

## Features Implemented

✅ **Automatic Embedding Generation**
- Embeddings generated during PDF upload (file & URL)
- Each content chunk gets a 1536-dimensional vector
- Stored in MongoDB alongside content

✅ **Semantic Search**
- Cosine similarity-based search
- Better than keyword search for natural language queries
- Supports tag filtering (exam type, subject, topic)

✅ **Embedding Regeneration**
- Batch process existing content
- Add embeddings to documents that don't have them
- Configurable batch size

✅ **Fallback to Keyword Search**
- Automatic fallback if embeddings disabled
- Graceful degradation

## MongoDB Atlas Configuration

### Step 1: Enable Atlas Search (Required for Production)

For optimal performance with large datasets, configure Atlas Search with vector search:

1. **Go to MongoDB Atlas Dashboard**
   - Navigate to your cluster
   - Click "Search" tab

2. **Create Search Index**
   - Click "Create Search Index"
   - Select "JSON Editor"
   - Use this configuration:

```json
{
  "mappings": {
    "dynamic": true,
    "fields": {
      "embedding": {
        "type": "knnVector",
        "dimensions": 1536,
        "similarity": "cosine"
      },
      "tags": {
        "type": "document",
        "fields": {
          "exam_type": {"type": "string"},
          "subject": {"type": "string"},
          "topic": {"type": "string"},
          "difficulty": {"type": "string"}
        }
      },
      "verified": {"type": "boolean"},
      "content": {"type": "string"}
    }
  }
}
```

3. **Index Configuration**
   - Database: `highpal_db`
   - Collection: `shared_knowledge`
   - Index name: `semantic_search_index`

4. **Wait for Index Build**
   - Can take several minutes for large collections
   - Status shows in Atlas dashboard

### Step 2: Environment Variables

Ensure these are set in your `.env` file:

```env
# MongoDB Atlas
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/highpal_db?retryWrites=true&w=majority

# OpenAI for embeddings
OPENAI_API_KEY=sk-proj-...your-key-here...
```

### Step 3: Test the Integration

Run the test script:

```powershell
cd backend
python test_embeddings.py
```

Expected output:
```
✅ System initialized
   Embeddings enabled: True
✅ Embedding generated successfully
   Dimensions: 1536
   Sample values: [0.0123, -0.0456, 0.0789, ...]
```

## API Endpoints

### 1. Upload with Embeddings

**POST** `/admin/train/upload`

Embeddings are automatically generated for each chunk.

```bash
curl -X POST "http://localhost:8003/admin/train/upload" \
  -F "file=@physics_book.pdf" \
  -F "tags={\"exam_type\":[\"JEE\"],\"subject\":\"Physics\"}" \
  -F "admin_id=admin1"
```

### 2. Semantic Search

**GET** `/admin/content/search?query=...&use_semantic=true`

```bash
# Semantic search (default)
curl "http://localhost:8003/admin/content/search?query=heat+transfer&exam_type=JEE&use_semantic=true"

# Keyword search (fallback)
curl "http://localhost:8003/admin/content/search?query=heat+transfer&use_semantic=false"
```

Response:
```json
{
  "results": [
    {
      "_id": "...",
      "content": "Heat transfer occurs through...",
      "similarity": 0.8542,
      "tags": {
        "exam_type": ["JEE"],
        "subject": "Physics",
        "topic": "Thermodynamics"
      },
      "has_embedding": true
    }
  ],
  "count": 5,
  "search_method": "semantic",
  "embeddings_available": true
}
```

### 3. Regenerate Embeddings

**POST** `/admin/embeddings/regenerate?batch_size=100`

For existing content without embeddings:

```bash
curl -X POST "http://localhost:8003/admin/embeddings/regenerate?batch_size=100"
```

Response:
```json
{
  "success": true,
  "updated": 87,
  "failed": 13,
  "batch_size": 100,
  "message": "Successfully generated 87 embeddings, 13 failed"
}
```

### 4. Embeddings Status

**GET** `/admin/embeddings/status`

Check coverage:

```bash
curl "http://localhost:8003/admin/embeddings/status"
```

Response:
```json
{
  "embeddings_enabled": true,
  "total_documents": 1234,
  "with_embeddings": 1100,
  "without_embeddings": 134,
  "coverage_percentage": 89.14
}
```

## Cost Estimation

### OpenAI Embeddings Pricing
- Model: `text-embedding-3-small`
- Cost: **$0.02 per 1M tokens** (~62,500 pages)
- Average: ~1000 tokens per page

### Example Costs
| Content Volume | Tokens | Cost |
|----------------|--------|------|
| 100 PDFs (10 pages each) | ~1M tokens | $0.02 |
| 1000 PDFs (10 pages each) | ~10M tokens | $0.20 |
| 10,000 PDFs (10 pages each) | ~100M tokens | $2.00 |

**Note:** Very cost-effective compared to GPT-4 API calls!

## Performance Optimization

### 1. Batch Upload
Use bulk URL upload to process multiple documents efficiently:

```python
uploads = [
    {"url": "url1.pdf", "tags": {...}},
    {"url": "url2.pdf", "tags": {...}},
    # ... up to 100 URLs
]
```

### 2. Chunk Size Tuning
- Default: 1000 chars with 100 char overlap
- Larger chunks: Better context, fewer embeddings
- Smaller chunks: More precise matching, more embeddings

### 3. Caching Strategy
- Embeddings stored permanently in MongoDB
- No re-generation needed
- Only generate once per content chunk

### 4. Rate Limiting
OpenAI has rate limits:
- Free tier: 3 requests/min
- Paid tier: 3,500 requests/min

For large batches, add delays:
```python
import time
time.sleep(0.1)  # 100ms between requests
```

## Monitoring & Maintenance

### Regular Checks

1. **Embedding Coverage**
   ```bash
   curl "http://localhost:8003/admin/embeddings/status"
   ```

2. **Search Quality**
   - Test semantic vs keyword search
   - Compare result relevance
   - Adjust chunk size if needed

3. **Cost Tracking**
   - Monitor OpenAI usage dashboard
   - Track embeddings generated per day
   - Set budget alerts

### Troubleshooting

**Problem:** Embeddings not generating
```
Solution: Check OPENAI_API_KEY in .env
Verify: curl "http://localhost:8003/test-openai"
```

**Problem:** Semantic search returns keyword results
```
Solution: Check embeddings_enabled flag
Run: curl "http://localhost:8003/admin/embeddings/status"
```

**Problem:** Slow search performance
```
Solution: Create Atlas Search index (Step 1)
Verify: Check "Search" tab in Atlas dashboard
```

**Problem:** High embedding costs
```
Solution: Reduce chunk size or content volume
Review: Check duplicate detection is working
```

## Advanced: Custom Similarity Function

For specialized search needs, modify the similarity calculation in `admin_training.py`:

```python
# Cosine similarity (default)
"similarity": {"$reduce": {...}}

# Euclidean distance (alternative)
"distance": {"$sqrt": {"$sum": [...]}}
```

## Next Steps

1. ✅ **Embeddings integrated** - This guide
2. ⏭️ **Admin Panel UI** - React dashboard for content management
3. ⏭️ **Cloud Authentication** - Firebase/Auth0 integration
4. ⏭️ **Query Routing** - Connect "Learn with Pal" mode to semantic search
5. ⏭️ **Video Support** - YouTube + local video transcription

## Support

For issues or questions:
- Check logs: `backend/logs/`
- Test endpoint: `http://localhost:8003/docs`
- MongoDB Atlas support: https://docs.atlas.mongodb.com/
- OpenAI API docs: https://platform.openai.com/docs/
