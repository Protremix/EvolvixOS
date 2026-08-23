#!/usr/bin/env python3
"""EvolvixOS Landing Page Server — serves web files on port 5021."""
import os
import socket
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

WEB_DIR = "/opt/evolvixos/web"
PORT = 5021

class LandingHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

# Custom server with SO_REUSEADDR
class LandingServer(ThreadingHTTPServer):
    allow_reuse_address = True
    
    def server_bind(self):
        import socketserver
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        socketserver.TCPServer.server_bind(self)

if __name__ == "__main__":
    os.chdir(WEB_DIR)
    try:
        server = LandingServer(("0.0.0.0", PORT), LandingHandler)
        print(f"Landing server running on port {PORT}", flush=True)
        server.serve_forever()
    except Exception as e:
        print(f"Error: {e}", flush=True)
        # Try alternate port
        PORT = 5023
        server = LandingServer(("0.0.0.0", PORT), LandingHandler)
        print(f"Landing server running on alternate port {PORT}", flush=True)
        server.serve_forever()
