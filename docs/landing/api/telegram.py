"""Vercel Python serverless function — Telegram bot webhook handler.

POST /api/telegram ← Telegram sends updates here.

Commands: /start, /health, /scan <addr>, /status, /help
"""
from __future__ import annotations

import json
import os
import urllib.request
from http.server import BaseHTTPRequestHandler

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

CONTRACTS = {
    "0x09bc4e0d864854c6afb6eb9a9cdf58ac190d0df9": "USDC.e",
    "0x78c1b0c915c4faa5fffa6cabf0219da63d7f4cb8": "WMNT",
    "0x201eba5cc46d216ce6dc03f6a759e8e766e956ae": "USDT",
    "0xcda86a272531e8640cd7f1a92c01839911b90bb0": "mETH",
    "0xcfa5ae7c2ce8fadc6426c1ff872ca45378fb7cf3": "Lendle",
}


def _supabase_get(path: str) -> list[dict]:
    """GET from Supabase REST API."""
    url = SUPABASE_URL.rstrip("/") + "/rest/v1/" + path
    req = urllib.request.Request(url, headers={"apikey": SUPABASE_KEY})
    with urllib.request.urlopen(req, timeout=8) as resp:
        return json.loads(resp.read().decode())


def _send_tg(chat_id: int, text: str) -> None:
    """Send a Telegram message (HTML parse mode)."""
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    body = json.dumps({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=8)


def _bar(score: int, width: int = 10) -> str:
    """Return a text progress bar."""
    filled = max(0, min(width, round(score / 100 * width)))
    return "\u2588" * filled + "\u2591" * (width - filled)


def _status_emoji(score: int) -> str:
    if score >= 80:
        return "\u2705"
    if score >= 60:
        return "\u26a0\ufe0f"
    return "\u274c"


def _handle_health(chat_id: int) -> None:
    """Latest health scores for all 5 contracts."""
    # Get last scan per contract (5 most recent distinct)
    rows = _supabase_get(
        "scan_history?order=scanned_at.desc&limit=50"
    )
    # Pick latest per contract
    seen: dict[str, dict] = {}
    for r in rows:
        c = r["contract"]
        if c not in seen:
            seen[c] = r
        if len(seen) >= 5:
            break

    if not seen:
        _send_tg(chat_id, "No scan data yet. Run the scan pipeline first.")
        return

    lines = ["\U0001f6e1 <b>Mantle Sentinel \u2014 Health Report</b>\n"]
    for addr in CONTRACTS:
        r = seen.get(addr)
        if not r:
            continue
        name = r.get("contract_name") or CONTRACTS.get(addr, addr[:10])
        score = r["health_score"]
        bar = _bar(score)
        emoji = _status_emoji(score)
        lines.append(f"<code>{name:<8}</code> {bar} <b>{score}</b> {emoji}")

    # Last scan timestamp
    if rows:
        last = rows[0].get("scanned_at", "?")
        lines.append(f"\n\U0001f4ca Last scan: <code>{last[:16]}</code>")

    _send_tg(chat_id, "\n".join(lines))


def _handle_scan(chat_id: int, text: str) -> None:
    """Latest scan for a specific address."""
    parts = text.strip().split()
    if len(parts) < 2:
        _send_tg(chat_id, "Usage: <code>/scan 0x09bc4e...</code>")
        return

    addr = parts[1].lower()
    rows = _supabase_get(
        f"scan_history?contract=eq.{addr}&order=scanned_at.desc&limit=1"
    )
    if not rows:
        _send_tg(chat_id, f"No data for <code>{addr[:12]}...</code>")
        return

    r = rows[0]
    name = r.get("contract_name") or addr[:12]
    score = r["health_score"]
    lines = [
        f"\U0001f50d <b>{name}</b>",
        f"Health: <b>{score}</b> {_status_emoji(score)}",
        f"Drift median: <code>{r.get('drift_median', 0):.4f}</code>",
        f"Drift p99: <code>{r.get('drift_p99', 0):.4f}</code>",
        f"Alerts: <code>{r.get('alert_count', 0)}</code>",
        f"TXs analyzed: <code>{r.get('tx_analyzed', 0)}</code>",
        f"Scanned: <code>{r.get('scanned_at', '?')[:16]}</code>",
    ]
    _send_tg(chat_id, "\n".join(lines))


def _handle_status(chat_id: int) -> None:
    """Monitoring uptime and stats."""
    rows = _supabase_get("scan_history?order=scanned_at.desc&limit=1")
    count_rows = _supabase_get("scan_history?select=id&limit=10000")
    last = rows[0]["scanned_at"][:16] if rows else "never"
    total = len(count_rows)
    _send_tg(chat_id, (
        "\U0001f4e1 <b>Sentinel Status</b>\n"
        f"Last scan: <code>{last}</code>\n"
        f"Total records: <b>{total}</b>\n"
        f"Contracts monitored: <b>5</b>\n"
        f"Scan interval: <b>every 4 hours</b>"
    ))


def _handle_start(chat_id: int) -> None:
    _send_tg(chat_id, (
        "\U0001f6e1 <b>Mantle Sentinel Bot</b>\n\n"
        "Behavioral anomaly detection for Mantle smart contracts.\n\n"
        "/health \u2014 Health scores for all monitored contracts\n"
        "/scan &lt;address&gt; \u2014 Latest scan for a contract\n"
        "/status \u2014 Monitoring uptime and stats\n"
        "/help \u2014 This message\n\n"
        "\U0001f310 <a href=\"https://mntsentinel.xyz\">mntsentinel.xyz</a>"
    ))


class handler(BaseHTTPRequestHandler):
    """Vercel Python runtime handler."""

    def do_POST(self):  # noqa: N802
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}

        msg = body.get("message", {})
        chat_id = msg.get("chat", {}).get("id")
        text = (msg.get("text") or "").strip()

        if chat_id and text:
            cmd = text.split()[0].lower().split("@")[0]  # strip @botname
            try:
                if cmd in ("/start", "/help"):
                    _handle_start(chat_id)
                elif cmd == "/health":
                    _handle_health(chat_id)
                elif cmd == "/scan":
                    _handle_scan(chat_id, text)
                elif cmd == "/status":
                    _handle_status(chat_id)
                else:
                    _send_tg(chat_id, "Unknown command. Try /help")
            except Exception as e:
                _send_tg(chat_id, f"\u26a0\ufe0f Error: {e}")

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"ok":true}')

    def do_GET(self):  # noqa: N802
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status":"ok","bot":"MantleSentinelBot"}')
