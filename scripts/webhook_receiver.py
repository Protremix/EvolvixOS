"""
EvolvixOS GitHub Webhook Receiver
Accepts GitHub webhook events and triggers the discovery engine.
"""
import os
import json
import hmac
import hashlib
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = int(os.environ.get('WEBHOOK_PORT', '5006'))
GITHUB_SECRET = os.environ.get('GITHUB_WEBHOOK_SECRET', '')

class WebhookHandler(BaseHTTPRequestHandler):
    def _send(self, code, data):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        if length > 1048576:
            self._send(413, {'error': 'Payload too large'})
            return
        body = self.rfile.read(length) if length else b''

        # Verify GitHub signature
        if GITHUB_SECRET:
            sig = self.headers.get('X-Hub-Signature-256', '')
            expected = 'sha256=' + hmac.new(GITHUB_SECRET.encode(), body, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(sig, expected):
                self._send(403, {'error': 'Invalid signature'})
                return

        event = self.headers.get('X-GitHub-Event', 'ping')
        try:
            payload = json.loads(body) if body else {}
        except:
            payload = {}

        if event == 'ping':
            self._send(200, {'status': 'pong'})
            return

        if event == 'push':
            repo = payload.get('repository', {}).get('full_name', 'unknown')
            ref = payload.get('ref', '')
            print(f'Push event: {repo} {ref}')

            # Trigger discovery engine update
            try:
                subprocess.Popen(
                    ['python3', '/opt/evolvixos/learner/discovery_engine.py'],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                self._send(200, {'status': 'ok', 'action': 'discovery_triggered'})
            except Exception as e:
                self._send(500, {'error': str(e)})
            return

        if event == 'release':
            repo = payload.get('repository', {}).get('full_name', 'unknown')
            tag = payload.get('release', {}).get('tag_name', '')
            print(f'Release event: {repo} {tag}')
            self._send(200, {'status': 'ok', 'event': 'release', 'tag': tag})
            return

        self._send(200, {'status': 'ok', 'event': event})

    def do_GET(self):
        self._send(200, {'status': 'webhook receiver active'})

    def log_message(self, format, *args):
        print(f'[webhook] {args[0]}')

if __name__ == '__main__':
    print(f'Webhook receiver starting on port {PORT}')
    server = HTTPServer(('127.0.0.1', PORT), WebhookHandler)
    server.serve_forever()
