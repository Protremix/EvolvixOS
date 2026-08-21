#!/usr/bin/env python3
import http.server
import socketserver
import os

os.chdir("/opt/evolvixos/dashboard")
handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(("127.0.0.1", 5021), handler) as httpd:
    print("EvolvixOS Landing Page running on port 5021")
    httpd.serve_forever()
