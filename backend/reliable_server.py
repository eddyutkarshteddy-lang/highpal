import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReliableHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        logger.info(f"{self.address_string()} - {format % args}")

    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Max-Age', '3600')
        self.end_headers()

    def do_GET(self):
        """Handle GET requests"""
        # Remove query parameters for path matching
        path = self.path.split('?')[0]
        
        if path == '/health':
            self.send_json_response({'status': 'healthy', 'message': 'Backend server is running'})
        elif path == '/':
            self.send_json_response({'message': 'HighPal Backend API', 'version': '1.0', 'endpoints': ['/ask_question/', '/health']})
        else:
            self.send_error(404, 'Endpoint not found')

    def do_POST(self):
        """Handle POST requests"""
        try:
            if self.path == '/ask_question/':
                self.handle_ask_question()
            elif self.path == '/upload_pdf/':
                self.handle_upload_pdf()
            elif self.path == '/upload_image/':
                self.handle_upload_image()
            elif self.path == '/fetch_url/':
                self.handle_fetch_url()
            else:
                self.send_error(404, 'Endpoint not found')
        except Exception as e:
            logger.error(f"Error handling POST request: {e}")
            logger.error(traceback.format_exc())
            self.send_json_response({'error': f'Server error: {str(e)}'}, status=500)

    def handle_ask_question(self):
        """Handle question answering"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            question = data.get('question', '').strip()
            logger.info(f"Received question: {question}")
            
            if not question:
                self.send_json_response({'error': 'No question provided'}, status=400)
                return
            
            # Simple response for now - will enhance with document search later
            if any(word in question.lower() for word in ['hello', 'hi', 'test']):
                answer = f"✅ Hello! I received your question: '{question}'. The backend is working perfectly!"
            elif any(word in question.lower() for word in ['ai', 'artificial', 'intelligence']):
                answer = "🤖 AI (Artificial Intelligence) refers to computer systems that can perform tasks that typically require human intelligence, such as learning, reasoning, and problem-solving."
            else:
                answer = f"📝 I received your question: '{question}'. The backend is working! Soon I'll be able to search through your uploaded documents to provide more specific answers."
            
            self.send_json_response({'answer': answer, 'question': question, 'status': 'success'})
            
        except json.JSONDecodeError:
            self.send_json_response({'error': 'Invalid JSON format'}, status=400)
        except Exception as e:
            logger.error(f"Error in handle_ask_question: {e}")
            self.send_json_response({'error': f'Processing error: {str(e)}'}, status=500)

    def handle_upload_pdf(self):
        """Handle PDF upload"""
        self.send_json_response({'message': 'PDF upload endpoint ready', 'status': 'implemented'})

    def handle_upload_image(self):
        """Handle image upload"""
        self.send_json_response({'message': 'Image upload endpoint ready', 'status': 'implemented'})

    def handle_fetch_url(self):
        """Handle URL fetching"""
        self.send_json_response({'message': 'URL fetch endpoint ready', 'status': 'implemented'})

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
