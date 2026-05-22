#!/usr/bin/env python3
"""
Simple HTTP server to serve the dashboard locally.
Run this script and visit http://localhost:8000 in your browser.

Usage:
    python serve_dashboard.py
"""

import http.server
import socketserver
import webbrowser
import os
import sys

PORT = 8000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

def run_server():
    handler = MyHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"""
        ╔════════════════════════════════════════════════════════╗
        ║       LeetCode YouTube Bot Dashboard Server            ║
        ╚════════════════════════════════════════════════════════╝
        
        🌐 Dashboard URL:  http://localhost:{PORT}/dashboard.html
        
        📁 Serving from:   {DIRECTORY}
        
        ⚠️  Press CTRL+C to stop the server
        """)
        
        # Open dashboard in default browser
        try:
            webbrowser.open(f'http://localhost:{PORT}/dashboard.html')
        except:
            print(f"⚠️  Open your browser and go to: http://localhost:{PORT}/dashboard.html")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n✅ Server stopped. Goodbye!")
            sys.exit(0)

if __name__ == "__main__":
    run_server()
