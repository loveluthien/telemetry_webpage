"""
main.py — Entry point for the CARTA telemetry dashboard.

Run directly:   python main.py
Run via gunicorn:  gunicorn main:server
"""

from app import app, server  # noqa: F401 — server must be importable for gunicorn
from layout import serve_layout
import callbacks  # noqa: F401 — registers all callbacks as a side-effect

app.layout = serve_layout

if __name__ == "__main__":
    import configparser
    _cfg = configparser.ConfigParser()
    _cfg.read("config")
    debug_mode = _cfg.get("SERVER", "debug") == "True"
    host_ip = _cfg.get("SERVER", "host") or "localhost"
    port = _cfg.getint("SERVER", "port", fallback=8050)
    app.run(debug=debug_mode, host=host_ip, port=port)
