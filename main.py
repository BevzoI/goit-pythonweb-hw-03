import http.server
import socketserver
import json
import os
from urllib.parse import parse_qs
from datetime import datetime

PORT = 3000
STORAGE_DIR = "storage"
DATA_FILE = os.path.join(STORAGE_DIR, "data.json")

if not os.path.exists(STORAGE_DIR):
    os.makedirs(STORAGE_DIR)

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.path = "index.html"
        elif self.path == "/message":
            self.path = "message.html"
        elif self.path == "/read":
            self.show_messages()
            return
        elif self.path in ["/style.css", "/logo.png", "/message.html"]:
            self.serve_static(self.path.lstrip("/"))
            return
        elif self.path == "/error":
            self.path = "error.html"
        else:
            self.path = "error.html"
            self.send_response(404)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            with open("error.html", "rb") as f:
                self.wfile.write(f.read())
            return

        return http.server.SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        if self.path == "/message":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            form_data = parse_qs(post_data)
            username = form_data.get("username", [""])[0]
            message_text = form_data.get("message", [""])[0]

            if username and message_text:
                timestamp = datetime.now().isoformat()

                with open(DATA_FILE, "r") as f:
                    data = json.load(f)

                data[timestamp] = {"username": username, "message": message_text}

                with open(DATA_FILE, "w") as f:
                    json.dump(data, f, indent=4)

                self.send_response(303)
                self.send_header("Location", "/read")
                self.end_headers()
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Invalid form data")

    def serve_static(self, filename):
        try:
            with open(filename, "rb") as f:
                self.send_response(200)
                if filename.endswith(".css"):
                    self.send_header("Content-type", "text/css")
                elif filename.endswith(".png"):
                    self.send_header("Content-type", "image/png")
                else:
                    self.send_header("Content-type", "application/octet-stream")
                self.end_headers()
                self.wfile.write(f.read())
        except FileNotFoundError:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Static file not found")

    def show_messages(self):
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)

            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()

            html = "<html><head><title>Messages</title><link rel='stylesheet' href='/style.css'></head><body>"
            html += "<h1>All Messages</h1><a href='/'>Go back</a><ul>"

            for timestamp, entry in sorted(data.items()):
                html += f"<li><strong>{entry['username']}</strong> ({timestamp}): {entry['message']}</li>"

            html += "</ul></body></html>"
            self.wfile.write(html.encode("utf-8"))
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Internal Server Error: {str(e)}".encode("utf-8"))

with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
    print(f"Server started at http://localhost:{PORT}")
    httpd.serve_forever()
