# 📡 HighPal API Documentation

**Version:** 2.0.0  
**Base URL:** `http://localhost:8003`  
**Server:** FastAPI with automatic OpenAPI docs at `/docs`

---

## 🌐 API Overview

HighPal provides a RESTful API for document management, AI-powered search, and question answering. All endpoints support CORS and return JSON responses.

### Authentication
Currently, no authentication is required for local development. Production deployment will include JWT token authentication.

### Content-Type
- **Uploads:** `multipart/form-data`  
- **JSON:** `application/json`
- **Responses:** `application/json`

---

## 📋 Core Endpoints

### 🏥 Health & Status

#### `GET /health`
Check server health and database connectivity.

**Response:**
```json
{
  "status": "healthy",
  "mongodb": "connected",
  "training_ready": true,
  "timestamp": "2025-09-03T17:38:47.821432"
}
```

#### `GET /`
Get API overview and available endpoints.

**Response:**
```json
{
  "message": "HighPal AI Assistant - Training Edition",
  "version": "2.0.0",
  "status": "running",
  "features": [
    "Document upload and processing",
    "AI-powered semantic search", 
    "PDF URL training",
    "Background task processing"
  ],
  "endpoints": {
    "docs": "/docs",
    "health": "/health",
    "upload": "/upload",
    "search": "/search",
    "ask_question": "/ask_question"
  }
}
```

---

## 📄 Document Management

### `POST /upload`
Upload a document (PDF, image, or text file).

**Request:**
- **Method:** POST
- **Content-Type:** multipart/form-data
- **Parameters:**
  - `file` (required): The document file
  - `title` (optional): Custom title for the document

**Example:**
```bash
curl -X POST http://localhost:8003/upload \
  -F "file=@document.pdf" \
  -F "title=My Research Paper"
```

**Response:**
```json
{
  "success": true,
  "document_id": "a1b2c3d4e5f6...",
  "filename": "document.pdf",
  "size": 245760,
  "message": "Document uploaded successfully"
}
```

### `GET /documents`
List all uploaded documents with optional filtering.

**Parameters:**
- `limit` (optional): Number of documents to return (default: 20)
- `source_type` (optional): Filter by source type

**Response:**
```json
{
  "documents": [
    {
      "id": "document_id_123",
      "content_preview": "This document discusses...",
      "metadata": {
        "filename": "research.pdf",
        "file_size": 245760,
        "upload_date": "2025-09-03T10:30:00Z",
        "source_type": "manual_upload"
      }
    }
  ],
  "count": 1,
  "filter": {}
}
```

---

## 🔍 Search & Query

### `GET /search`
Search through uploaded documents using semantic similarity.

**Parameters:**
- `q` (required): Search query
- `limit` (optional): Number of results (default: 10)

**Example:**
```bash
curl "http://localhost:8003/search?q=machine%20learning&limit=5"
```

**Response:**
```json
{
  "query": "machine learning",
  "results": [
    {
      "content": "Machine learning is a method of data analysis...",
      "score": 0.89,
      "filename": "ml_paper.pdf",
      "metadata": {...}
    }
  ],
  "count": 5
}
```

### `POST /ask_question`
Ask a question about uploaded documents using AI.

**Request Body:**
```json
{
  "question": "What is machine learning?",
  "uploaded_files": ["doc_id_1", "doc_id_2"]
}
```

**Response:**
```json
{
  "question": "What is machine learning?",
  "answer": "Based on the available documents, machine learning is...",
  "search_results": [
    {
      "content": "Document excerpt...",
      "score": 0.89,
      "metadata": {
        "filename": "ml_basics.pdf",
        "source": "upload",
        "method": "semantic_search"
      }
    }
  ],
  "sources_found": 3,
  "confidence": "high"
}
```

### `GET /ask_question`
Alternative GET method for simple questions.

**Parameters:**
- `q` or `question`: The question to ask

**Example:**
```bash
curl "http://localhost:8003/ask_question?q=What%20is%20AI?"
```

---

## 🎓 Training Features

### `POST /train/pdf-urls`
Train the AI using PDFs from public URLs.

**Request Body:**
```json
{
  "urls": [
    "https://arxiv.org/pdf/2023.12345.pdf",
    "https://example.com/whitepaper.pdf"
  ],
  "metadata": {
    "domain": "research",
    "priority": "high"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "processed_urls": 2,
  "failed_urls": 0,
  "documents_added": 2,
  "processing_time": "45.2s"
}
```

### `POST /train/pdf-urls/background`
Start background training process (non-blocking).

**Request:** Same as `/train/pdf-urls`

**Response:**
```json
{
  "status": "started",
  "task_id": "train_task_123",
  "message": "Training started in background",
  "estimated_time": "60s"
}
```

### `GET /train/status`
Get training system status and statistics.

**Response:**
```json
{
  "total_documents": 150,
  "total_embeddings": 150,
  "last_training": "2025-09-03T15:30:00Z",
  "system_status": "ready",
  "active_tasks": 0
}
```

### `GET /training-guide`
Get detailed training usage examples and workflow.

---

## 🛠️ Error Handling

### HTTP Status Codes
- **200:** Success
- **400:** Bad Request (missing parameters, invalid JSON)
- **404:** Not Found (endpoint doesn't exist)
- **500:** Internal Server Error (database issues, processing errors)

### Error Response Format
```json
{
  "error": "Description of the error",
  "status": "error",
  "timestamp": "2025-09-03T17:45:00Z"
}
```

### Common Errors
- **MongoDB Connection:** `"Database connection not available"`
- **File Upload:** `"File type not supported"`
- **Search:** `"No documents found matching query"`
- **Training:** `"Failed to download PDF from URL"`

---

## 🧪 Testing the API

### Quick Health Check
```bash
curl http://localhost:8003/health
```

### Upload a Test Document
```bash
curl -X POST http://localhost:8003/upload \
  -F "file=@test.pdf"
```

### Search Test
```bash
curl "http://localhost:8003/search?q=test"
```

### Q&A Test
```bash
curl -X POST http://localhost:8003/ask_question \
  -H "Content-Type: application/json" \
  -d '{"question": "What is this document about?"}'
```

---

## 🔧 Development Notes

### Local Development
- Server runs on port **8003** (not 8000)
- MongoDB Atlas connection required
- CORS enabled for all origins in development

### Frontend Integration
- React app connects to `http://localhost:8003`
- All endpoints support preflight CORS requests
- File uploads use FormData with proper content types

### Performance
- Semantic search uses 384-dimensional embeddings
- Average response time: <2s for search, <5s for Q&A
- Supports concurrent requests with FastAPI async

### Logging
- All requests logged with timestamps
- Error details logged to console
- MongoDB operations tracked

---

## 📚 Additional Resources

- **Interactive Docs:** http://localhost:8003/docs (Swagger UI)
- **OpenAPI Schema:** http://localhost:8003/openapi.json
- **Health Dashboard:** http://localhost:8003/health
- **Training Guide:** http://localhost:8003/training-guide

---

**Last Updated:** September 3, 2025  
**API Version:** 2.0.0  
**Maintained by:** HighPal Development Team
