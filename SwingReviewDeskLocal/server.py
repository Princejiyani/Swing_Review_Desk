"""Local history helper for Swing Review Desk. Historical daily data via yfinance."""
from __future__ import annotations

import json
import math
from datetime import date, timedelta
import os
import re
import threading
import time
import subprocess
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

HOST = "127.0.0.1"
PORT = 8765
ROOT = os.path.dirname(os.path.abspath(__file__))
ALLOWED_SYMBOL = re.compile(r"^[A-Za-z0-9^._=+&\-]{1,40}$")

# Yahoo can throttle rapid sequential requests. Serialize calls and cache successful
# symbol histories for the lifetime of this helper process.
HISTORY_LOCK = threading.Lock()
HISTORY_CACHE: dict[tuple[str, str], tuple[float, list[dict]]] = {}
CACHE_SECONDS = 30 * 60
MIN_PROVIDER_GAP_SECONDS = 2.0
_LAST_PROVIDER_REQUEST = 0.0


class Handler(SimpleHTTPRequestHandler):
    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            return self._json(200, {"ok": True, "service": "Swing Review Desk local helper"})
        if parsed.path != "/api/history":
            return super().do_GET()

        params = parse_qs(parsed.query)
        symbol = (params.get("symbol") or [""])[0].strip()
        period = (params.get("period") or ["2y"])[0].strip()
        start_text = (params.get("start") or [""])[0].strip()
        end_text = (params.get("end") or [""])[0].strip()
        if not ALLOWED_SYMBOL.fullmatch(symbol):
            return self._json(400, {"error": "Invalid ticker symbol."})
        start_date = end_date = None
        if start_text or end_text:
            try:
                start_date = date.fromisoformat(start_text)
                end_date = date.fromisoformat(end_text)
                if start_date > end_date:
                    raise ValueError("start date is after end date")
                if (end_date - start_date).days > 36525:
                    raise ValueError("date range is too large")
            except ValueError:
                return self._json(400, {"error": "Choose valid start and end dates, with the start date on or before the end date."})
        elif period not in {"1y", "2y", "5y"}:
            period = "2y"

        range_key = f"{start_text}:{end_text}" if start_date else period
        cache_key = (symbol, range_key)
        cached = HISTORY_CACHE.get(cache_key)
        if cached and (time.time() - cached[0]) < CACHE_SECONDS:
            return self._json(200, {"symbol": symbol, "period": period, "start": start_text or None, "end": end_text or None, "source": "Yahoo Finance via yfinance (cached)", "bars": cached[1], "cached": True})

        try:
            import yfinance as yf

            # A lock prevents fast stock-by-stock review from creating many simultaneous
            # Yahoo requests. Retry once on transient provider/network exceptions.
            with HISTORY_LOCK:
                global _LAST_PROVIDER_REQUEST
                cached = HISTORY_CACHE.get(cache_key)
                if cached and (time.time() - cached[0]) < CACHE_SECONDS:
                    return self._json(200, {"symbol": symbol, "period": period, "start": start_text or None, "end": end_text or None, "source": "Yahoo Finance via yfinance (cached)", "bars": cached[1], "cached": True})

                last_error = None
                history = None
                for attempt in range(2):
                    wait_for = MIN_PROVIDER_GAP_SECONDS - (time.monotonic() - _LAST_PROVIDER_REQUEST)
                    if wait_for > 0:
                        time.sleep(wait_for)
                    _LAST_PROVIDER_REQUEST = time.monotonic()
                    try:
                        history_args = {
                            "interval": "1d",
                            "auto_adjust": False,
                            "actions": False,
                            "timeout": 30,
                        }
                        if start_date is not None and end_date is not None:
                            # Yahoo's end parameter is exclusive; add one day so the
                            # user's selected end date is included in the chart.
                            history_args["start"] = start_date.isoformat()
                            history_args["end"] = (end_date + timedelta(days=1)).isoformat()
                        else:
                            history_args["period"] = period
                        history = yf.Ticker(symbol).history(**history_args)
                        if history is not None and not history.empty:
                            last_error = None
                            break
                        last_error = RuntimeError("Yahoo Finance returned no daily rows")
                    except Exception as exc:
                        last_error = exc
                    if attempt == 0:
                        print(f"[data] Temporary history failure for {symbol}; retrying once...")
                        time.sleep(1.5)

            if history is None or history.empty:
                message = str(last_error or "no rows returned").replace("\n", " ").strip()
                return self._json(502, {"error": f"Yahoo Finance returned no daily history for {symbol} after retry: {message[:350]}. It may be rate-limiting requests or may not list this symbol."})

            bars = []
            for index, row in history.iterrows():
                try:
                    day = index.strftime("%Y-%m-%d")
                    values = [float(row[name]) for name in ("Open", "High", "Low", "Close")]
                    if not all(math.isfinite(value) and value > 0 for value in values):
                        continue
                    try:
                        volume = float(row.get("Volume", 0) or 0)
                        if not math.isfinite(volume):
                            volume = 0
                    except (TypeError, ValueError):
                        volume = 0
                    bars.append({
                        "time": day,
                        "open": values[0],
                        "high": values[1],
                        "low": values[2],
                        "close": values[3],
                        "volume": volume,
                    })
                except (KeyError, TypeError, ValueError, OverflowError):
                    continue

            if not bars:
                return self._json(502, {"error": f"No complete OHLC rows were returned for {symbol}."})
            HISTORY_CACHE[cache_key] = (time.time(), bars)
            return self._json(200, {"symbol": symbol, "period": period, "start": start_text or None, "end": end_text or None, "source": "Yahoo Finance via yfinance", "bars": bars, "cached": False})
        except Exception as exc:
            message = str(exc).replace("\n", " ").strip()
            if len(message) > 500:
                message = message[:500] + "…"
            return self._json(502, {"error": f"Could not download {symbol} from Yahoo Finance: {message or type(exc).__name__}. Check your internet connection or try again later."})

    def log_message(self, format: str, *args) -> None:
        # Keep terminal output concise; request and error status remain visible.
        print("[%s] %s" % (self.log_date_time_string(), format % args))


def main() -> None:
    os.chdir(ROOT)
    try:
        import yfinance  # noqa: F401
    except ImportError:
        print("Missing package: yfinance. Run start_swing_review.bat to install requirements.")
        input("Press Enter to close...")
        return

    server = ThreadingHTTPServer((HOST, PORT), Handler)
    url = f"http://{HOST}:{PORT}"
    print("Swing Review Desk is running at", url)
    print("Keep this window open while using the desk. Press Ctrl+C to stop.")
    def open_chrome() -> None:
        chrome = os.environ.get("SWING_REVIEW_CHROME", "")
        if chrome and os.path.isfile(chrome):
            try:
                subprocess.Popen([chrome, url])
            except OSError as exc:
                print(f"Could not launch Google Chrome automatically: {exc}")
                print("Open Chrome and visit", url)
        else:
            print("Google Chrome path was not provided. Open Chrome and visit", url)

    threading.Timer(1.0, open_chrome).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Swing Review Desk…")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
