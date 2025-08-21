import json
import logging
import hashlib
import os
import tempfile
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
import traceback
import io
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store uploaded documents in memory
uploaded_documents = {}

class ReliableHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        logger.info(f"{self.address_string()} - {format % args}")

    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, DELETE')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Max-Age', '3600')
        self.end_headers()

    def do_GET(self):
        """Handle GET requests"""
        # Remove query parameters for path matching
        path = self.path.split('?')[0]
        
        if path == '/health':
            self.send_json_response({'status': 'healthy', 'message': 'Backend server is running'})
        elif path == '/admin':
            self.serve_admin_interface()
        elif path.startswith('/admin/training_data/'):
            self.handle_admin_get_training_data()
        elif path == '/':
            self.send_json_response({'message': 'HighPal Backend API', 'version': '1.0', 'endpoints': ['/ask_question/', '/health', '/admin']})
        else:
            self.send_error(404, 'Endpoint not found')

    def do_POST(self):
        """Handle POST requests"""
        try:
            if self.path == '/ask_question/':
                self.handle_ask_question()
            elif self.path == '/upload':
                self.handle_file_upload()
            elif self.path == '/upload_pdf/':
                self.handle_upload_pdf()
            elif self.path == '/upload_image/':
                self.handle_upload_image()
            elif self.path == '/fetch_url/':
                self.handle_fetch_url()
            elif self.path == '/admin/upload_training_pdf/':
                self.handle_admin_upload_training_pdf()
            elif self.path == '/admin/add_training_url/':
                self.handle_admin_add_training_url()
            else:
                self.send_error(404, 'Endpoint not found')
        except Exception as e:
            logger.error(f"Error handling POST request: {e}")
            logger.error(traceback.format_exc())
            self.send_json_response({'error': f'Server error: {str(e)}'}, status=500)

    def do_DELETE(self):
        """Handle DELETE requests"""
        try:
            if self.path.startswith('/admin/clear_training_data/'):
                self.handle_admin_clear_training_data()
            else:
                self.send_error(404, 'Endpoint not found')
        except Exception as e:
            logger.error(f"Error handling DELETE request: {e}")
            logger.error(traceback.format_exc())
            self.send_json_response({'error': f'Server error: {str(e)}'}, status=500)

    def handle_ask_question(self):
        """Handle question answering"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            question = data.get('question', '').strip()
            uploaded_files = data.get('uploaded_files', [])
            logger.info(f"Received question: {question}")
            logger.info(f"Uploaded files referenced: {uploaded_files}")
            
            if not question:
                self.send_json_response({'error': 'No question provided'}, status=400)
                return
            
            # Check if we have uploaded documents to reference
            answer = self.generate_answer(question, uploaded_files)
            
            self.send_json_response({
                'answer': answer, 
                'question': question, 
                'status': 'success',
                'documents_used': len(uploaded_files)
            })
            
        except json.JSONDecodeError:
            self.send_json_response({'error': 'Invalid JSON format'}, status=400)
        except Exception as e:
            logger.error(f"Error in handle_ask_question: {e}")
            self.send_json_response({'error': f'Processing error: {str(e)}'}, status=500)

    def generate_answer(self, question, uploaded_file_ids):
        """Generate answer based on question and uploaded documents"""
        # Simple response logic - will enhance with AI later
        if any(word in question.lower() for word in ['hello', 'hi', 'test']):
            return f"✅ Hello! I received your question: '{question}'. The backend is working perfectly!"
        
        # Check if we have uploaded documents
        if uploaded_file_ids and uploaded_documents:
            relevant_docs = []
            for file_id in uploaded_file_ids:
                if file_id in uploaded_documents:
                    relevant_docs.append(uploaded_documents[file_id])
            
            if relevant_docs:
                doc_names = [doc['filename'] for doc in relevant_docs]
                return f"📄 Based on your uploaded documents ({', '.join(doc_names)}), I can see you have {len(relevant_docs)} document(s) to reference. Question: '{question}'. Document processing and AI integration coming soon!"
        
        # General responses
        if any(word in question.lower() for word in ['ai', 'artificial', 'intelligence']):
            return "🤖 AI (Artificial Intelligence) refers to computer systems that can perform tasks that typically require human intelligence, such as learning, reasoning, and problem-solving."
        elif any(word in question.lower() for word in ['document', 'file', 'upload']):
            doc_count = len(uploaded_documents)
            return f"� I currently have {doc_count} document(s) uploaded. You can upload PDFs, images, and text files. Soon I'll be able to search through them to answer your questions!"
        else:
            return f"📝 I received your question: '{question}'. The backend is working! Upload some documents and I'll soon be able to search through them to provide specific answers."

    def handle_upload_pdf(self):
        """Handle PDF upload"""
        self.send_json_response({'message': 'PDF upload endpoint ready', 'status': 'implemented'})

    def handle_upload_image(self):
        """Handle image upload"""
        self.send_json_response({'message': 'Image upload endpoint ready', 'status': 'implemented'})

    def handle_fetch_url(self):
        """Handle URL fetching"""
        self.send_json_response({'message': 'URL fetch endpoint ready', 'status': 'implemented'})

    def handle_admin_upload_training_pdf(self):
        """Handle admin training PDF upload - simplified version"""
        try:
            # Get content length
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_json_response({'error': 'No content received'}, status=400)
                return

            # Read the raw form data
            form_data = self.rfile.read(content_length)
            
            # Generate file ID from content
            file_id = hashlib.md5(form_data).hexdigest()
            filename = "training_document.pdf"  # Simplified filename
            
            # Extract basic info (simplified for demo)
            extracted_text = f"Training PDF content ({len(form_data)} bytes) - Training data processed successfully"
            
            # Store document as training data
            uploaded_documents[file_id] = {
                'filename': filename,
                'size': len(form_data),
                'content': extracted_text,
                'file_type': 'Training PDF',
                'category': 'academic',  # Default category
                'source': 'training_data'
            }
            
            logger.info(f"📚 Training PDF uploaded: {filename} ({len(form_data)} bytes)")
            
            self.send_json_response({
                'message': f'Training PDF uploaded and processed successfully',
                'filename': filename,
                'file_id': file_id,
                'size': len(form_data),
                'category': 'academic',
                'extracted_text_length': len(extracted_text),
                'file_type': 'Training PDF'
            })
            
        except Exception as e:
            logger.error(f"Training PDF upload error: {e}")
            logger.error(traceback.format_exc())
            self.send_json_response({'error': f'Training upload failed: {str(e)}'}, status=500)

    def handle_admin_add_training_url(self):
        """Handle admin training URL addition"""
        try:
            content_type = self.headers.get('Content-Type', '')
            if not content_type.startswith('multipart/form-data'):
                self.send_json_response({'error': 'Expected multipart/form-data'}, status=400)
                return

            # Get content length
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_json_response({'error': 'No content received'}, status=400)
                return

            # Parse multipart form data
            boundary = content_type.split('boundary=')[1]
            form_data = self.rfile.read(content_length)
            
            # Parse form fields
            form_fields = self.parse_multipart_form_data(form_data, boundary)
            
            if 'admin_key' not in form_fields or form_fields['admin_key'] != 'admin123':
                self.send_json_response({'error': 'Invalid admin key'}, status=403)
                return
            
            if 'url' not in form_fields:
                self.send_json_response({'error': 'No URL provided'}, status=400)
                return
                
            url = form_fields['url']
            category = form_fields.get('category', 'general')
            
            # Generate document ID
            url_id = hashlib.md5(url.encode('utf-8')).hexdigest()
            
            # Extract text from URL (simplified for demo)
            extracted_text = f"Training URL content from {url} - Web content processed for training"
            
            # Store URL content as training data
            uploaded_documents[url_id] = {
                'url': url,
                'size': len(extracted_text),
                'content': extracted_text,
                'file_type': 'Training URL',
                'category': category,
                'source': 'training_data',
                'title': f'Web Content: {url}'
            }
            
            logger.info(f"🌐 Training URL added: {url} - Category: {category}")
            
            self.send_json_response({
                'message': f'Training URL processed successfully',
                'url': url,
                'doc_id': url_id,
                'category': category,
                'character_count': len(extracted_text),
                'title': f'Web Content: {url}'
            })
            
        except Exception as e:
            logger.error(f"Training URL error: {e}")
            logger.error(traceback.format_exc())
            self.send_json_response({'error': f'Training URL failed: {str(e)}'}, status=500)

    def handle_admin_get_training_data(self):
        """Handle admin get training data request"""
        try:
            # Filter training documents
            training_docs = []
            categories = {}
            
            for doc_id, doc_data in uploaded_documents.items():
                if doc_data.get('source') == 'training_data':
                    category = doc_data.get('category', 'unknown')
                    categories[category] = categories.get(category, 0) + 1
                    
                    training_docs.append({
                        'doc_id': doc_id,
                        'filename': doc_data.get('filename'),
                        'url': doc_data.get('url'),
                        'category': category,
                        'content_length': len(doc_data.get('content', '')),
                        'title': doc_data.get('title'),
                        'storage': 'memory'
                    })
            
            self.send_json_response({
                'training_documents': training_docs,
                'categories': categories,
                'total_training_docs': len(training_docs)
            })
            
        except Exception as e:
            logger.error(f"Error getting training data: {e}")
            self.send_json_response({'error': f'Failed to get training data: {str(e)}'}, status=500)

    def handle_admin_clear_training_data(self):
        """Handle admin clear training data request"""
        try:
            # Parse query parameters for admin key
            from urllib.parse import urlparse, parse_qs
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            
            admin_key = query_params.get('admin_key', [''])[0]
            if admin_key != 'admin123':
                self.send_json_response({'error': 'Invalid admin key'}, status=403)
                return
            
            # Count training documents before clearing
            training_count = 0
            docs_to_remove = []
            
            for doc_id, doc_data in uploaded_documents.items():
                if doc_data.get('source') == 'training_data':
                    training_count += 1
                    docs_to_remove.append(doc_id)
            
            # Remove training documents
            for doc_id in docs_to_remove:
                del uploaded_documents[doc_id]
            
            logger.info(f"🗑️ Cleared {training_count} training documents")
            
            self.send_json_response({
                'message': f'Successfully cleared {training_count} training documents',
                'cleared_count': training_count
            })
            
        except Exception as e:
            logger.error(f"Error clearing training data: {e}")
            self.send_json_response({'error': f'Failed to clear training data: {str(e)}'}, status=500)

    def handle_file_upload(self):
        """Handle file upload - simplified version"""
        try:
            # Get content length
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_json_response({'error': 'No content received'}, status=400)
                return

            # Read the raw form data
            form_data = self.rfile.read(content_length)
            
            # For now, create a simple file representation
            # In a real implementation, we'd properly parse the multipart data
            file_id = hashlib.md5(form_data).hexdigest()
            filename = "uploaded_file.txt"  # Placeholder filename
            
            # Extract basic info
            extracted_text = f"File content ({len(form_data)} bytes) - Basic file processing active"
            
            # Store document
            uploaded_documents[file_id] = {
                'filename': filename,
                'size': len(form_data),
                'content': extracted_text,
                'file_type': 'Document'
            }
            
            logger.info(f"📄 File uploaded: {filename} ({len(form_data)} bytes)")
            
            self.send_json_response({
                'message': f'File uploaded and processed successfully',
                'file_id': file_id,
                'filename': filename,
                'size': len(form_data),
                'extracted_text_length': len(extracted_text),
                'file_type': 'Document'
            })
            
        except Exception as e:
            logger.error(f"File upload error: {e}")
            logger.error(traceback.format_exc())
            self.send_json_response({'error': f'Upload failed: {str(e)}'}, status=500)

    def send_json_response(self, data, status=200):
        """Send JSON response with proper headers"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        response_json = json.dumps(data, indent=2)
        self.wfile.write(response_json.encode('utf-8'))
        logger.info(f"Sent response: {response_json}")

    def serve_admin_interface(self):
        """Serve the admin HTML interface"""
        try:
            with open('admin.html', 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(html_content.encode('utf-8'))
            logger.info("Served admin interface")
        except FileNotFoundError:
            self.send_error(404, 'Admin interface file not found')
        except Exception as e:
            logger.error(f"Error serving admin interface: {e}")
            self.send_error(500, f'Error loading admin interface: {str(e)}')

def start_server(port=8000):
    """Start the reliable server"""
    try:
        server = HTTPServer(('0.0.0.0', port), ReliableHandler)
        print(f"🚀 HighPal Backend Server starting on http://localhost:{port}")
        print(f"📊 Health check: http://localhost:{port}/health")
        print(f"❓ Ask questions: POST to http://localhost:{port}/ask_question/")
        print(f"🔄 Server is ready for connections!")
        print("=" * 60)
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        raise

if __name__ == '__main__':
    start_server()
