"""Tiny local server for the camera smoke test: serves camera_feasibility/ and saves POSTed JSON to results/.
Usage: python3 -P serve.py <port>"""
import sys, os, json, http.server

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(ROOT)


class H(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if not self.path.startswith('/save/'):
            self.send_error(404); return
        name = os.path.basename(self.path[len('/save/'):]) or 'out.json'
        n = int(self.headers.get('Content-Length', 0))
        data = self.rfile.read(n)
        json.loads(data)  # must be valid JSON
        with open(os.path.join(ROOT, 'results', name), 'wb') as fh:
            fh.write(data)
        self.send_response(200); self.end_headers(); self.wfile.write(b'saved')


http.server.ThreadingHTTPServer(('127.0.0.1', int(sys.argv[1])), H).serve_forever()
