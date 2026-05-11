import os
import socket
from flask import Flask, redirect, jsonify, request, render_template_string
from dotenv import load_dotenv

load_dotenv()  # loads .env if present, no-op otherwise

# --- Environment variables ---
PORT    = int(os.environ.get("PORT", 5000))
VERSION = os.environ.get("VERSION", "dev")
API_KEY = os.environ.get("API_KEY")

if not API_KEY:
    raise RuntimeError("API_KEY environment variable must be set before starting the app.")

app = Flask(__name__)

# ---------------------------------------------------------------------------
# HTML template
# ---------------------------------------------------------------------------
INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Status Dashboard</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Syne:wght@400;700;800&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --bg:        #0a0e14;
      --surface:   #111720;
      --border:    #1e2d40;
      --accent:    #00d4ff;
      --accent2:   #ff4d6a;
      --text:      #c8d8e8;
      --muted:     #4a6080;
      --mono:      'Share Tech Mono', monospace;
      --sans:      'Syne', sans-serif;
    }

    body {
      background: var(--bg);
      color: var(--text);
      font-family: var(--sans);
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 2rem;
      overflow-x: hidden;
    }

    /* grid background */
    body::before {
      content: '';
      position: fixed;
      inset: 0;
      background-image:
        linear-gradient(var(--border) 1px, transparent 1px),
        linear-gradient(90deg, var(--border) 1px, transparent 1px);
      background-size: 48px 48px;
      opacity: 0.35;
      pointer-events: none;
      z-index: 0;
    }

    .card {
      position: relative;
      z-index: 1;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 4px;
      width: 100%;
      max-width: 580px;
      padding: 3rem 3rem 2.5rem;
      box-shadow: 0 0 80px rgba(0, 212, 255, 0.05);
    }

    .badge {
      display: inline-block;
      font-family: var(--mono);
      font-size: 0.65rem;
      letter-spacing: 0.15em;
      text-transform: uppercase;
      color: var(--accent);
      border: 1px solid var(--accent);
      padding: 3px 10px;
      border-radius: 2px;
      margin-bottom: 1.4rem;
    }

    h1 {
      font-size: 2.4rem;
      font-weight: 800;
      line-height: 1.1;
      letter-spacing: -0.02em;
      color: #fff;
      margin-bottom: 1rem;
    }

    h1 span { color: var(--accent); }

    p.blurb {
      font-size: 0.95rem;
      color: var(--muted);
      line-height: 1.7;
      margin-bottom: 2rem;
    }

    button {
      font-family: var(--mono);
      font-size: 0.85rem;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      background: transparent;
      color: var(--accent);
      border: 1px solid var(--accent);
      padding: 0.7rem 1.6rem;
      cursor: pointer;
      border-radius: 2px;
      transition: background 0.15s, color 0.15s;
    }

    button:hover { background: var(--accent); color: var(--bg); }
    button:disabled { opacity: 0.4; cursor: not-allowed; }

    /* result block */
    #result {
      margin-top: 1.8rem;
      font-family: var(--mono);
      font-size: 0.82rem;
      line-height: 1.8;
      display: none;
    }

    #result .label {
      font-size: 0.65rem;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--muted);
      margin-bottom: 0.6rem;
    }

    .row { display: flex; gap: 1rem; align-items: baseline; padding: 0.25rem 0; border-bottom: 1px solid var(--border); }
    .row:last-child { border-bottom: none; }
    .key   { color: var(--muted); min-width: 90px; }
    .value { color: var(--accent); }
    .value.ok { color: #3ddc84; }
    .value.err { color: var(--accent2); }

    .spinner {
      display: inline-block;
      width: 14px; height: 14px;
      border: 2px solid var(--border);
      border-top-color: var(--accent);
      border-radius: 50%;
      animation: spin 0.6s linear infinite;
      vertical-align: middle;
      margin-right: 0.5rem;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
  </style>
</head>
<body>
  <div class="card">
    <div class="badge">system monitor</div>
    <h1>Status<br/><span>Dashboard</span></h1>
    <p class="blurb">
      Real-time health probe for the running container.
      Hit the button to query the status API and inspect hostname and version details.
    </p>

    <button id="btn" onclick="fetchStatus()">Check Status</button>

    <div id="result">
      <div class="label">API Response — /api/v1/status</div>
      <div id="rows"></div>
    </div>
  </div>

  <script>
    async function fetchStatus() {
      const btn  = document.getElementById('btn');
      const box  = document.getElementById('result');
      const rows = document.getElementById('rows');

      btn.disabled = true;
      btn.innerHTML = '<span class="spinner"></span>Checking…';
      box.style.display = 'none';

      try {
        const res  = await fetch('/api/v1/status');
        const data = await res.json();
        rows.innerHTML = Object.entries(data).map(([k, v]) => `
          <div class="row">
            <span class="key">${k}</span>
            <span class="value ${k === 'status' && v === 'ok' ? 'ok' : ''}">${v}</span>
          </div>`).join('');
        box.style.display = 'block';
      } catch (e) {
        rows.innerHTML = `<div class="row"><span class="value err">Failed to reach API</span></div>`;
        box.style.display = 'block';
      }

      btn.disabled = false;
      btn.textContent = 'Refresh';
    }
  </script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
def index():
    return render_template_string(INDEX_HTML)


@app.get("/api/status")
def api_status_redirect():
    return redirect("/api/v1/status", code=302)


@app.get("/api/v1/status")
def api_v1_status():
    return jsonify({
        "status":   "ok",
        "hostname": socket.gethostname(),
        "version":  VERSION,
    })


@app.get("/api/v1/secret")
def api_v1_secret():
    key = request.headers.get("X-API-Key", "")
    if key != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"message": "you found the secret"})


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)