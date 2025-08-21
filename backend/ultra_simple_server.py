#!/usr/bin/env python3
"""
Ultra-simple HTTP server for testing uploads
"""
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import hashlib

class UltraSimpleHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        print("OPTIONS request received")
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()

    def do_GET(self):
        print(f"GET request: {self.path}")
        path = self.path.split('?')[0]
        
        if path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(b'{"status": "ok"}')
            print("Health check sent")
            
        elif path == '/admin':
            try:
                with open('admin.html', 'r') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(content.encode())
                print("Admin page served")
            except:
                self.send_error(404, "Admin page not found")
        else:
            self.send_error(404, "Not found")

    def do_POST(self):
        print(f"POST request: {self.path}")
        
        if '/upload_training_pdf/' in self.path:
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                print(f"Reading {content_length} bytes")
                
                data = self.rfile.read(content_length)
                print(f"Got {len(data)} bytes of data")
                
                # Send success response
                response = {
                    'message': 'Upload successful!',
                    'size': len(data),
                    'filename': 'training.pdf'
                }
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
                print("Upload response sent")
                
            except Exception as e:
                print(f"Upload error: {e}")
                self.send_error(500, str(e))
        else:
            self.send_error(404, "Endpoint not found")

if __name__ == '__main__':
    try:
        server = HTTPServer(('0.0.0.0', 8000), UltraSimpleHandler)
        print("🚀 Ultra-simple server starting on http://localhost:8000")
        print("🎛️ Admin: http://localhost:8000/admin")
        print("🔌 Server socket created and bound successfully")
        server.serve_forever()
    except Exception as e:
        print(f"❌ Server error: {e}")
        import traceback
        traceback.print_exc()
    except KeyboardInterrupt:
        print("\nServer stopped")
