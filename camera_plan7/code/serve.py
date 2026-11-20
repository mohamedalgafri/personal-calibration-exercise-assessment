"""Local server for PLAN7 extraction: serves camera_plan7/ WITH HTTP Range support (needed for video seeking),
and saves POSTed JSON to results/. Added 16 Nov after Stage A attempt 1 stalled (readyState 1, seeking forever)
because the plain SimpleHTTPRequestHandler ignores Range requests.
Usage: python3 -P serve.py <port>"""
import sys, os, json, re, http.server

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(ROOT)


class H(http.server.SimpleHTTPRequestHandler):
    def send_head(self):
        rng = self.headers.get('Range')
        path = self.translate_path(self.path)
        if not rng or not os.path.isfile(path):
            return super().send_head()
        m = re.match(r'bytes=(\d*)-(\d*)', rng)
        size = os.path.getsize(path)
        a = int(m.group(1)) if m.group(1) else max(0, size - int(m.group(2)))
        b = int(m.group(2)) if (m.group(1) and m.group(2)) else size - 1
        b = min(b, size - 1)
        if a > b:
            self.send_error(416); return None
        f = open(path, 'rb'); f.seek(a)
        self.send_response(206)
        self.send_header('Content-Type', self.guess_type(path))
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Content-Range', f'bytes {a}-{b}/{size}')
        self.send_header('Content-Length', str(b - a + 1))
        self.end_headers()
        self._remaining = b - a + 1
        return f

    def copyfile(self, source, outputfile):
        rem = getattr(self, '_remaining', None)
        if rem is None:
            return super().copyfile(source, outputfile)
        while rem > 0:
            chunk = source.read(min(1 << 20, rem))
            if not chunk:
                break
            outputfile.write(chunk); rem -= len(chunk)
        self._remaining = None

    def end_headers(self):
        if not getattr(self, '_ranges_hdr', False):
            self.send_header('Accept-Ranges', 'bytes')
        super().end_headers()

    def do_POST(self):
        if self.path.startswith('/claim/'):   # parallel extraction: atomic claim so two windows never process the same video
            name = os.path.basename(self.path[len('/claim/'):])
            os.makedirs(os.path.join(ROOT, 'results', 'claims'), exist_ok=True)
            done = os.path.exists(os.path.join(ROOT, 'results', name + '.json'))
            try:
                if done:
                    raise FileExistsError
                os.close(os.open(os.path.join(ROOT, 'results', 'claims', name), os.O_CREAT | os.O_EXCL | os.O_WRONLY))
                self.send_response(200); self.end_headers(); self.wfile.write(b'ok')
            except FileExistsError:
                self.send_response(409); self.end_headers(); self.wfile.write(b'taken')
            return
        if not self.path.startswith('/save/'):
            self.send_error(404); return
        name = os.path.basename(self.path[len('/save/'):]) or 'out.json'
        data = self.rfile.read(int(self.headers.get('Content-Length', 0)))
        json.loads(data)
        dst = os.path.join(ROOT, 'results', name)
        if os.path.exists(dst):   # Addendum A.9: never overwrite
            import time; base, ext = os.path.splitext(dst); dst = f'{base}_{time.strftime("%Y%m%d-%H%M%S")}{ext}'
        with open(dst, 'wb') as fh:
            fh.write(data)
        self.send_response(200); self.end_headers(); self.wfile.write(b'saved')

    def log_message(self, *a):
        pass


http.server.ThreadingHTTPServer(('127.0.0.1', int(sys.argv[1])), H).serve_forever()
