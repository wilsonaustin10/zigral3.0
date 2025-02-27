#!/usr/bin/env python3
"""
Simple HTTP server to test noVNC integration with WebSocket proxy
"""

import http.server
import socketserver
import os
import sys
import webbrowser
from http import HTTPStatus

# Configuration
PORT = 8090
VNC_HOST = os.environ.get('VNC_HOST', 'localhost')
VNC_PORT = os.environ.get('VNC_PORT', '6080')

class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom request handler with CORS support"""
    
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        http.server.SimpleHTTPRequestHandler.end_headers(self)
    
    def do_OPTIONS(self):
        # Handle preflight requests
        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()
    
    def do_GET(self):
        # Redirect / to simple-test.html
        if self.path == '/':
            self.path = '/simple-test.html'
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

def main():
    print(f"Starting test server on port {PORT}")
    print(f"VNC connection configured for {VNC_HOST}:{VNC_PORT}")
    
    # Set environment variables for the HTML to use
    os.environ['VNC_HOST'] = VNC_HOST
    os.environ['VNC_PORT'] = VNC_PORT
    
    try:
        with socketserver.TCPServer(("", PORT), CORSRequestHandler) as httpd:
            print(f"Server running at http://localhost:{PORT}/")
            print("Press Ctrl+C to stop")
            
            # Open the browser automatically
            webbrowser.open(f"http://localhost:{PORT}/")
            
            # Start serving
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        sys.exit(0)

if __name__ == "__main__":
    main() 