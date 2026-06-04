import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler


def start_web_server():
    class RenderHandler(SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"NEXOS Bot 7/24 Aktif!")

    def run():
        port = int(os.environ.get("PORT", 8080))
        server = HTTPServer(("0.0.0.0", port), RenderHandler)
        server.serve_forever()

    threading.Thread(target=run, daemon=True).start()
