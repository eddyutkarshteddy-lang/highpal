#!/usr/bin/env python3
"""
Simple HTTP server for HighPal admin interface
"""
import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
import hashlib
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory storage for uploaded documents
uploaded_documents = {}

class SimpleHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        logger.info(f"{self.address_string()} - {format % args}")

    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        logger.info("Handling OPTIONS request")
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
        logger.info(f"GET request: {self.path} -> path: {path}")
        
        if path == '/health':
            self.send_json_response({'status': 'healthy', 'message': 'Simple server is running'})
        elif path == '/admin':
            self.serve_admin_page()
        else:
            logger.warning(f"Unknown path: {path}")
            self.send_error(404, 'Not found')

    def do_POST(self):
        """Handle POST requests"""
        logger.info(f"POST request: {self.path}")
        
        try:
            if self.path == '/admin/upload_training_pdf/':
                self.handle_upload()
            else:
                self.send_error(404, 'Not found')
        except Exception as e:
            logger.error(f"Error in POST: {e}")
            logger.error(traceback.format_exc())
            self.send_json_response({'error': str(e)}, status=500)

    def handle_upload(self):
        """Handle file upload - very simple version"""
        logger.info("Processing upload request")
        
        try:
            # Read content
            content_length = int(self.headers.get('Content-Length', 0))
            logger.info(f"Content length: {content_length}")
            
            if content_length == 0:
                self.send_json_response({'error': 'No content'}, status=400)
                return
            
            # Read the data
            post_data = self.rfile.read(content_length)
            logger.info(f"Read {len(post_data)} bytes")
            
            # Generate file ID
            file_id = hashlib.md5(post_data).hexdigest()
            
            # Store the upload
            uploaded_documents[file_id] = {
                'filename': 'uploaded_training.pdf',
                'size': len(post_data),
                'content': f'Training content ({len(post_data)} bytes)',
                'category': 'academic',
                'type': 'training_pdf'
            }
            
            logger.info(f"Stored upload with ID: {file_id}")
            
            # Send success response
            self.send_json_response({
                'message': 'Upload successful!',
                'file_id': file_id,
                'filename': 'uploaded_training.pdf',
                'size': len(post_data)
            })
            
        except Exception as e:
            logger.error(f"Upload error: {e}")
            self.send_json_response({'error': f'Upload failed: {str(e)}'}, status=500)

    def send_json_response(self, data, status=200):
        """Send JSON response with CORS headers"""
        logger.info(f"Sending response: {status}")
        
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, DELETE')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        response_json = json.dumps(data, indent=2)
        self.wfile.write(response_json.encode('utf-8'))
        logger.info(f"Response sent: {response_json}")

    def serve_admin_page(self):
        """Serve admin HTML page"""
        try:
            with open('admin.html', 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(html_content.encode('utf-8'))
            logger.info("Served admin page")
        except FileNotFoundError:
            self.send_error(404, 'Admin page not found')
        except Exception as e:
            logger.error(f"Error serving admin page: {e}")
            self.send_error(500, str(e))

def start_server(port=8000):
    """Start the simple server"""
    try:
        server = HTTPServer(('localhost', port), SimpleHandler)
        print(f"🚀 Simple HighPal Server starting on http://localhost:{port}")
        print(f"📊 Health check: http://localhost:{port}/health")
        print(f"🎛️ Admin interface: http://localhost:{port}/admin")
        print("=" * 60)
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
    except Exception as e:
        print(f"❌ Server error: {e}")
        raise

if __name__ == '__main__':
    start_server()
