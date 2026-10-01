from http.server import HTTPServer, SimpleHTTPRequestHandler

HOST = "0.0.0.0"
PORT = 8000

server = HTTPServer((HOST, PORT), SimpleHTTPRequestHandler)

print(f"Server started: http://localhost:{PORT}")

server.serve_forever()