"""
Forex Dashboard — Server + Cloudflare public tunnel in ONE window
"""
import subprocess, threading, re, time, os, sys, urllib.request, webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse, json, socket

PORT = 8765
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

YF_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
}

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80)); ip = s.getsockname()[0]; s.close(); return ip
    except: return '127.0.0.1'

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path.startswith('/api/chart/'):
            sym = urllib.parse.unquote(path[len('/api/chart/'):])
            url = f'https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1h&range=5d'
            try:
                req = urllib.request.Request(url, headers=YF_HEADERS)
                with urllib.request.urlopen(req, timeout=15) as r: data = r.read()
                self._send(200, 'application/json', data)
            except Exception as e:
                self._send(500, 'application/json', json.dumps({'error':str(e)}).encode())
            return
        rel = path.lstrip('/') or 'forex_dashboard.html'
        fp = os.path.join(SCRIPT_DIR, rel)
        try:
            with open(fp,'rb') as f: content = f.read()
            self._send(200, 'text/html' if rel.endswith('.html') else 'application/octet-stream', content)
        except FileNotFoundError:
            self._send(404, 'text/plain', b'Not found')
    def _send(self, code, ct, body):
        self.send_response(code)
        self.send_header('Content-Type', ct)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', len(body))
        self.end_headers(); self.wfile.write(body)
    def log_message(self, *a): pass

def ensure_cloudflared():
    cf = os.path.join(SCRIPT_DIR, 'cloudflared.exe')
    if not os.path.exists(cf):
        print('  מוריד cloudflared (פעם ראשונה בלבד, ~30MB)...')
        urllib.request.urlretrieve(
            'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe', cf)
        print('  הורדה הושלמה.\n')
    return cf

if __name__ == '__main__':
    os.chdir(SCRIPT_DIR)
    ip = get_local_ip()

    # Start HTTP server in background thread
    server = HTTPServer(('0.0.0.0', PORT), Handler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()

    print(f'\n  שרת פעיל על http://localhost:{PORT}')
    print(f'  מכין קישור ציבורי...\n')

    cf = ensure_cloudflared()
    proc = subprocess.Popen(
        [cf, 'tunnel', '--protocol', 'http2', '--url', f'http://127.0.0.1:{PORT}'],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, cwd=SCRIPT_DIR
    )

    found = False
    for line in proc.stdout:
        if not found:
            m = re.search(r'https://[\w\-]+\.trycloudflare\.com', line)
            if m:
                found = True
                url = m.group(0)
                print('=' * 56)
                print('  >>> קישור ציבורי — שלח לכל אחד:')
                print(f'  >>> {url}')
                print('=' * 56)
                print('  (סגור חלון זה = הלינק מת)\n')
                webbrowser.open(f'http://localhost:{PORT}/forex_dashboard.html')
