"""
Example: How to Train HighPal with PDF URLs
Demonstrates various ways to train your model from public PDFs
"""

import asyncio
import json
from pdf_url_trainer import train_from_urls_sync, PDFURLTrainer
from production_haystack_mongo import HaystackStyleMongoIntegration

# Example PDF URLs (replace with real URLs)
EXAMPLE_RESEARCH_PAPERS = [
    # AI/ML Research Papers (from arXiv)
    "https://arxiv.org/pdf/1706.03762.pdf",  # Attention Is All You Need (Transformers)
    "https://arxiv.org/pdf/2005.14165.pdf",  # GPT-3 Paper
    "https://arxiv.org/pdf/1810.04805.pdf",  # BERT Paper
]

EXAMPLE_BUSINESS_DOCUMENTS = [
    # Example business/whitepaper URLs (replace with real ones)
    "https://example.com/ai-strategy-2025.pdf",
    "https://example.com/digital-transformation-guide.pdf",
    "https://example.com/industry-report-2025.pdf",
]

def example_1_simple_training():
    """Example 1: Simple synchronous training"""
    print("🚀 Example 1: Simple Training")
    
    # Simple training with metadata
    urls = [
        "https://arxiv.org/pdf/1706.03762.pdf",  # Attention paper
    ]
    
    metadata = {
        "domain": "AI Research",
        "training_batch": "example_1",
        "priority": "high"
    }
    
    try:
        result = train_from_urls_sync(urls, metadata)
        print(f"✅ Training completed!")
        print(f"   Successful: {result['successful']}/{result['total_urls']}")
        print(f"   Total chunks: {result['total_chunks']}")
        print(f"   Errors: {len(result['errors'])}")
    except Exception as e:
        print(f"❌ Training failed: {e}")

async def example_2_batch_training():
    """Example 2: Batch training with multiple domains"""
    print("\\n🚀 Example 2: Batch Training")
    
    # Define different batches for different domains
    ai_papers = ["https://arxiv.org/pdf/1706.03762.pdf"]
    business_docs = ["https://example.com/business-doc.pdf"]  # Replace with real URL
    
    async with PDFURLTrainer() as trainer:
        # Train AI research papers
        ai_result = await trainer.train_from_pdf_urls(
            urls=ai_papers,
            metadata={"domain": "AI Research", "batch": "ai_papers"}
        )
        
        # Train business documents  
        # business_result = await trainer.train_from_pdf_urls(
        #     urls=business_docs,
        #     metadata={"domain": "Business", "batch": "business_docs"}
        # )
        
        print(f"✅ AI Papers: {ai_result['successful']}/{ai_result['total_urls']} successful")
        # print(f"✅ Business Docs: {business_result['successful']}/{business_result['total_urls']} successful")

def example_3_training_status():
    """Example 3: Check training status"""
    print("\\n🚀 Example 3: Training Status")
    
    try:
        # Initialize connection
        haystack_mongo = HaystackStyleMongoIntegration()
        
        # Get document counts
        total_docs = haystack_mongo.collection.count_documents({})
        pdf_url_docs = haystack_mongo.collection.count_documents({
            'metadata.source_type': 'pdf_url'
        })
        
        print(f"📊 Training Statistics:")
        print(f"   Total Documents: {total_docs}")
        print(f"   PDF URL Documents: {pdf_url_docs}")
        print(f"   Other Documents: {total_docs - pdf_url_docs}")
        
        # Show some example documents
        print("\\n📄 Recent PDF URL Documents:")
        recent_docs = haystack_mongo.collection.find(
            {'metadata.source_type': 'pdf_url'}
        ).limit(3)
        
        for doc in recent_docs:
            metadata = doc.get('metadata', {})
            print(f"   • {metadata.get('filename', 'Unknown')}")
            print(f"     URL: {metadata.get('source_url', 'Unknown')[:50]}...")
            print(f"     Chunks: {metadata.get('total_chunks', 'Unknown')}")
        
    except Exception as e:
        print(f"❌ Status check failed: {e}")

async def example_4_test_search():
    """Example 4: Test search with trained data"""
    print("\\n🚀 Example 4: Testing Search")
    
    try:
        haystack_mongo = HaystackStyleMongoIntegration()
        
        # Test queries
        test_queries = [
            "attention mechanism",
            "transformer architecture", 
            "neural networks",
            "artificial intelligence"
        ]
        
        for query in test_queries:
            print(f"\\n🔍 Searching: '{query}'")
            results = haystack_mongo.semantic_search(query, top_k=3)
            
            print(f"   Found {len(results)} results:")
            for i, result in enumerate(results[:2]):
                content_preview = result.get('content', '')[:100]
                source_url = result.get('metadata', {}).get('source_url', 'Unknown')
                score = result.get('score', 0)
                print(f"   {i+1}. Score: {score:.3f}")
                print(f"      Content: {content_preview}...")
                print(f"      Source: {source_url[:50]}...")
        
    except Exception as e:
        print(f"❌ Search test failed: {e}")

def example_5_api_usage():
    """Example 5: How to use the training API endpoints"""
    print("\\n🚀 Example 5: API Usage Examples")
    
    api_examples = {
        "train_urls": {
            "method": "POST",
            "endpoint": "http://localhost:8003/train/pdf-urls",
            "payload": {
                "urls": [
                    "https://arxiv.org/pdf/1706.03762.pdf"
                ],
                "metadata": {
                    "domain": "AI Research",
                    "batch": "transformers"
                }
            }
        },
        "background_training": {
            "method": "POST", 
            "endpoint": "http://localhost:8003/train/pdf-urls/background",
            "description": "Same payload as above, returns task ID immediately"
        },
        "check_status": {
            "method": "GET",
            "endpoint": "http://localhost:8003/train/status",
            "description": "Get overall training statistics"
        },
        "search_trained": {
            "method": "GET",
            "endpoint": "http://localhost:8003/search?q=attention mechanism",
            "description": "Search using trained data"
        }
    }
    
    print("📖 API Usage Examples:")
    for name, example in api_examples.items():
        print(f"\\n   {name.upper()}:")
        print(f"   {example['method']} {example['endpoint']}")
        if 'payload' in example:
            print(f"   Payload: {json.dumps(example['payload'], indent=4)}")
        if 'description' in example:
            print(f"   Description: {example['description']}")

async def main():
    """Run all examples"""
    print("🎓 HighPal PDF URL Training Examples")
    print("=" * 50)
    
    # Example 1: Simple training
    example_1_simple_training()
    
    # Wait between examples
    await asyncio.sleep(2)
    
    # Example 2: Batch training
    await example_2_batch_training()
    
    # Wait between examples  
    await asyncio.sleep(1)
    
    # Example 3: Training status
    example_3_training_status()
    
    # Example 4: Test search
    await example_4_test_search()
    
    # Example 5: API usage
    example_5_api_usage()
    
    print("\\n🎉 All examples completed!")
    print("💡 Next steps:")
    print("   1. Start training server: python training_server.py")
    print("   2. Visit http://localhost:8003/docs for API documentation")
    print("   3. Use POST /train/pdf-urls to train with your PDF URLs")
    print("   4. Test searches with GET /search?q=your_query")

if __name__ == "__main__":
    # Run examples
    asyncio.run(main())
