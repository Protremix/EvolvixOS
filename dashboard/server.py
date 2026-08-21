#!/usr/bin/env python3
import http.server
import socketserver
import os

os.chdir("/opt/evolvixos/dashboard")
handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(("127.0.0.1", 5020), handler) as httpd:
    print("EvolvixOS Dashboard running on port 5020")
    httpd.serve_forever()
