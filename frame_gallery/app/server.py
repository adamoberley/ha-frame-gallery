"""Ingress control panel: shows the current piece + a "Show next now" button.

Bound to 0.0.0.0 for ingress (HA authenticates it). URLs are relative so they
work under the ingress token path. `trigger` is set by the button to request an
immediate change; `status` is a dict the loop updates and the panel reads.
"""
from __future__ import annotations

import json
import logging
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

log = logging.getLogger("frame-gallery.server")

PREVIEW_PATH = "/data/last.jpg"

CONTROL_HTML = b"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>REFRAMED Gallery</title>
<style>
  :root {
    color-scheme: light dark;
    --primary:#03a9f4; --bg:#f5f5f5; --card:#ffffff; --text:#212121;
    --secondary:#727272; --divider:rgba(0,0,0,.12); --screen:#202124;
    --shadow:0 2px 1px -1px rgba(0,0,0,.2),0 1px 1px 0 rgba(0,0,0,.14),0 1px 3px 0 rgba(0,0,0,.12);
    --card-border:transparent;
    --sans:Roboto,"Helvetica Neue",-apple-system,system-ui,"Segoe UI",Arial,sans-serif;
  }
  @media (prefers-color-scheme: dark) {
    :root { --bg:#111111; --card:#1c1c1c; --text:#e1e1e1; --secondary:#9b9b9b;
            --divider:rgba(225,225,225,.12); --shadow:none; --card-border:rgba(225,225,225,.12); }
  }
  * { box-sizing:border-box; }
  body { font-family:var(--sans); margin:0; padding:16px; background:var(--bg);
         color:var(--text); line-height:1.5; -webkit-font-smoothing:antialiased; }
  .card { max-width:760px; margin:0 auto; background:var(--card); border-radius:12px;
          box-shadow:var(--shadow); border:1px solid var(--card-border); padding:20px; }
  h1 { font-size:1.375rem; font-weight:500; margin:0 0 4px; }
  .sub { color:var(--secondary); font-size:.9rem; margin:0 0 18px; }
  button { font:inherit; font-weight:500; padding:10px 18px; border:0; border-radius:8px;
           background:var(--primary); color:#fff; cursor:pointer; }
  button:hover { filter:brightness(1.06); }
  button:disabled { opacity:.5; cursor:default; filter:none; }
  .status { margin:14px 0 0; font-size:.9rem; min-height:1.2em; color:var(--secondary); }
  .now { font-size:.95rem; margin:8px 0 0; }
  .now b { font-weight:500; }
  .frame { margin-top:16px; border-radius:8px; overflow:hidden; background:var(--screen);
           aspect-ratio:16/9; display:grid; place-items:center; }
  .frame img { width:100%; height:100%; object-fit:contain; display:block; }
  .frame .empty { color:#bbb; font-size:.9rem; }
</style></head><body>
<div class="card">
  <h1>REFRAMED Gallery</h1>
  <p class="sub">Curated public-domain art on your Frame TV. Changes on its own;
     use the button to jump to the next piece now.</p>
  <button id="go">Show next now</button>
  <div class="status" id="status">&nbsp;</div>
  <p class="now" id="now"></p>
  <div class="frame"><span class="empty" id="empty">Nothing shown yet</span>
       <img id="prev" alt="" hidden></div>
</div>
<script>
  var lastTs = 0;
  function fmt(t){ return t ? new Date(t*1000).toLocaleTimeString() : '-'; }
  function refresh(){
    fetch('status', {cache:'no-store'}).then(function(r){return r.json();}).then(function(s){
      document.getElementById('go').disabled = !!s.busy;
      var state = s.busy ? 'Fetching a new piece...'
                : (s.last_error ? ('Last error: ' + s.last_error) : 'Idle');
      document.getElementById('status').textContent = state
        + ' \\u2022 ' + s.tv_count + ' TV(s) \\u2022 every ' + s.interval_minutes
        + ' min \\u2022 last changed ' + fmt(s.last_ts);
      document.getElementById('now').innerHTML = s.title
        ? ('Now showing: <b>' + s.title + '</b> \\u2014 ' + (s.artist||'') +
           (s.credit ? ' <span style="opacity:.6">(' + s.credit + ')</span>' : ''))
        : '';
      if (s.last_ts && s.last_ts !== lastTs){
        lastTs = s.last_ts;
        var img = document.getElementById('prev');
        img.src = 'preview.jpg?t=' + s.last_ts; img.hidden = false;
        document.getElementById('empty').style.display = 'none';
      }
    }).catch(function(){});
  }
  document.getElementById('go').onclick = function(){
    document.getElementById('go').disabled = true;
    document.getElementById('status').textContent = 'Queued...';
    fetch('next', {method:'POST'}).catch(function(){});
    setTimeout(refresh, 600);
  };
  refresh(); setInterval(refresh, 2000);
</script></body></html>"""


def make_server(trigger: threading.Event, status: dict,
                host: str = "0.0.0.0", port: int = 8099):
    debug = status.get("_debug", False)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            if debug:
                log.debug("%s - %s", self.address_string(), fmt % args)

        def _send(self, code, ctype, body: bytes):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)

        def do_POST(self):
            if urlparse(self.path).path == "/next":
                trigger.set()
                log.info("manual 'show next' requested from control panel")
                self._send(200, "application/json", b'{"queued":true}')
            else:
                self._send(404, "text/plain", b"not found")

        def do_GET(self):
            path = urlparse(self.path).path
            if path in ("/", ""):
                self._send(200, "text/html; charset=utf-8", CONTROL_HTML)
            elif path == "/status":
                public = {k: v for k, v in status.items() if not k.startswith("_")}
                self._send(200, "application/json", json.dumps(public).encode())
            elif path == "/preview.jpg":
                try:
                    with open(PREVIEW_PATH, "rb") as fh:
                        self._send(200, "image/jpeg", fh.read())
                except OSError:
                    self._send(404, "text/plain", b"no preview yet")
            else:
                self._send(404, "text/plain", b"not found")

        do_HEAD = do_GET

    return ThreadingHTTPServer((host, port), Handler)
