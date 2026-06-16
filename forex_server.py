"""
Forex Dashboard Server
- Serves forex_dashboard.html
- Proxies Yahoo Finance at /api/chart/<SYMBOL>
- Reads PORT from environment (for Render.com cloud deployment)
"""
import os, json, webbrowser, threading, time, socket
import urllib.request, urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = int(os.environ.get('PORT', 8765))
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

YF_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.9',
}

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return '127.0.0.1'

class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path.startswith('/api/chart/'):
            sym = urllib.parse.unquote(path[len('/api/chart/'):])
            qs = parsed.query or 'interval=1h&range=5d'
            url = f'https://query1.finance.yahoo.com/v8/finance/chart/{sym}?{qs}'
            try:
                req = urllib.request.Request(url, headers=YF_HEADERS)
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = resp.read()
                self._send(200, 'application/json', data)
            except Exception as e:
                self._send(500, 'application/json', json.dumps({'error': str(e)}).encode())
            return

        rel = path.lstrip('/')
        if not rel:
            rel = 'forex_dashboard.html'
        filepath = os.path.join(SCRIPT_DIR, rel)
        try:
            with open(filepath, 'rb') as f:
                content = f.read()
            ct = 'text/html' if rel.endswith('.html') else 'application/octet-stream'
            self._send(200, ct, content)
        except FileNotFoundError:
            self._send(404, 'text/plain', b'Not found')

    def _send(self, code, ct, body):
        self.send_response(code)
        self.send_header('Content-Type', ct)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass

def open_browser(url):
    time.sleep(1.2)
    webbrowser.open(url)

if __name__ == '__main__':
    os.chdir(SCRIPT_DIR)
    ip = get_local_ip()
    local_url   = f'http://localhost:{PORT}/forex_dashboard.html'
    network_url = f'http://{ip}:{PORT}/forex_dashboard.html'

    print(f'\n  ================================================')
    print(f'  דשבורד מט"ח — שרת פעיל')
    print(f'  ================================================')
    print(f'  מחשב זה:  {local_url}')
    print(f'  ברשת:     {network_url}')
    print(f'  ================================================')
    print(f'  לעצור: Ctrl+C\n')

    is_cloud = 'PORT' in os.environ
    if not is_cloud:
        threading.Thread(target=open_browser, args=(local_url,), daemon=True).start()
    try:
        HTTPServer(('0.0.0.0', PORT), Handler).serve_forever()
    except KeyboardInterrupt:
        print('\nנסגר.')
