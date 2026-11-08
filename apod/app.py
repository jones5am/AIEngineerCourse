#!/usr/bin/env python3
"""Serve today's NASA Astronomy Picture of the Day.

The legacy api.nasa.gov APOD endpoint now returns the NASA logo instead of
the photograph. This viewer calls the current APOD API on science.nasa.gov
for a specific calendar date and renders that picture.

APOD dates follow US Eastern time. With no date selected, the page uses today
in America/New_York.
"""

from __future__ import annotations

import datetime as dt
import html
import json
import os
import re
import threading
import zoneinfo
from html.parser import HTMLParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen

APOD_API = "https://science.nasa.gov/wp-json/wp/v2/apod-basic"
APOD_FIELDS = "date,title,explanation,credit,copyright,alt,media_type,permalink,url,hdurl"
APOD_ZONE = zoneinfo.ZoneInfo("America/New_York")
FIRST_APOD = dt.date(1995, 6, 16)
USER_AGENT = "apod-daily-viewer/1.0"
CACHE_SECONDS = 600

_cache_lock = threading.Lock()
_cache: dict[str, tuple[float, dict]] = {}


class ApodError(Exception):
    """The APOD API did not return a picture we can show."""


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def html_to_text(value: str) -> str:
    parser = _TextExtractor()
    parser.feed(value or "")
    parser.close()
    text = re.sub(r"\s+", " ", "".join(parser.parts)).strip()
    return re.sub(r"\.(?=[A-Z])", ". ", text)


def apod_today() -> dt.date:
    return dt.datetime.now(APOD_ZONE).date()


def parse_apod_date(value: str | None) -> dt.date:
    if value is None or value == "":
        return apod_today()
    try:
        day = dt.date.fromisoformat(value)
    except ValueError as exc:
        raise ApodError("Use a date in YYYY-MM-DD form.") from exc
    if day < FIRST_APOD or day > apod_today():
        raise ApodError(
            f"{day.isoformat()} is outside the APOD archive "
            f"({FIRST_APOD.isoformat()} through {apod_today().isoformat()})."
        )
    return day


def _get_json(url: str) -> object:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urlopen(request, timeout=30) as response:
            payload = response.read()
    except HTTPError as exc:
        raise ApodError(f"APOD API returned HTTP {exc.code} for {url}.") from exc
    except URLError as exc:
        raise ApodError(f"Could not reach the APOD API: {exc.reason}.") from exc

    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ApodError("APOD API returned a response that was not JSON.") from exc


def _entry_from_payload(payload: object, day: dt.date) -> dict | None:
    if isinstance(payload, dict):
        candidates = [payload]
    elif isinstance(payload, list):
        candidates = [item for item in payload if isinstance(item, dict)]
    else:
        return None
    key = day.isoformat()
    match = next((item for item in candidates if item.get("date") == key), None)
    return match


def fetch_apod(day: dt.date) -> dict:
    """Load the APOD entry for `day` from the APOD API."""

    key = day.isoformat()
    now = dt.datetime.now(dt.timezone.utc).timestamp()
    with _cache_lock:
        cached = _cache.get(key)
        if cached and now - cached[0] < CACHE_SECONDS:
            return cached[1]

    # Ask for this calendar date. The API currently answers with recent
    # entries, so pick the object whose date field is the day we asked for.
    # If that day is not in the list, load its YYMMDD resource directly.
    dated_url = f"{APOD_API}/?date={key}&_fields={APOD_FIELDS}"
    match = _entry_from_payload(_get_json(dated_url), day)
    api_url = dated_url
    if match is None:
        api_url = f"{APOD_API}/{day.strftime('%y%m%d')}?_fields={APOD_FIELDS}"
        match = _entry_from_payload(_get_json(api_url), day)
    if match is None or match.get("date") != key:
        raise ApodError(f"Asked the APOD API for {key} and did not get that day's picture.")
    picture = match.get("hdurl") or ""
    if not isinstance(picture, str) or not picture.startswith("https://"):
        raise ApodError(f"APOD entry for {key} did not include a picture URL.")
    entry = {
        "date": key,
        "title": str(match.get("title") or "Astronomy Picture of the Day"),
        "explanation": html_to_text(str(match.get("explanation") or "")),
        "credit": html_to_text(str(match.get("credit") or match.get("copyright") or "")),
        "alt": html_to_text(str(match.get("alt") or match.get("title") or "NASA astronomy picture")),
        "media_type": str(match.get("media_type") or "image"),
        "permalink": str(match.get("permalink") or match.get("url") or ""),
        "hdurl": picture,
        "api_url": api_url,
    }
    with _cache_lock:
        _cache[key] = (now, entry)
    return entry


def picture_url(entry: dict) -> str:
    """Return a display-sized NASA image URL for this entry."""

    raw = entry["hdurl"]
    parts = urlsplit(raw)
    host = (parts.hostname or "").lower()
    if not (host == "nasa.gov" or host.endswith(".nasa.gov")):
        raise ApodError(f"Refusing to load a picture from {host or 'an unknown host'}.")
    if "nasa-logo" in parts.path:
        raise ApodError("APOD API returned the NASA logo instead of the day's picture.")
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    if query.get("w") in (None, "", "0"):
        query["w"] = "1600"
    if query.get("h") in ("", "0"):
        query.pop("h", None)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), ""))


def fetch_picture(entry: dict) -> tuple[bytes, str]:
    url = picture_url(entry)
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "image/*"})
    try:
        with urlopen(request, timeout=30) as response:
            content_type = response.headers.get("Content-Type", "application/octet-stream")
            data = response.read()
    except HTTPError as exc:
        raise ApodError(f"Picture URL returned HTTP {exc.code}.") from exc
    except URLError as exc:
        raise ApodError(f"Could not download the picture: {exc.reason}.") from exc
    media_type = content_type.split(";", 1)[0].strip().lower()
    if not media_type.startswith("image/") or len(data) < 1000:
        raise ApodError("The APOD picture URL did not return an image.")
    return data, media_type


def render_page(entry: dict) -> str:
    day = dt.date.fromisoformat(entry["date"])
    date_label = f"{day.strftime('%B')} {day.day}, {day.year}"
    credit = (
        f'<p class="credit">Credit: {html.escape(entry["credit"])}</p>'
        if entry["credit"]
        else ""
    )
    video_note = (
        "<p class=\"note\">Today's APOD is a video. This is the picture NASA published with it.</p>"
        if entry["media_type"] == "video"
        else ""
    )
    permalink = entry["permalink"]
    source = (
        f'<p class="source"><a href="{html.escape(permalink, quote=True)}">Open this picture on NASA</a></p>'
        if permalink.startswith("https://")
        else ""
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(entry["title"])} — NASA APOD {html.escape(entry["date"])}</title>
  <style>
    :root {{ color-scheme: dark; }}
    body {{
      margin: 0;
      font-family: Georgia, "Iowan Old Style", serif;
      background: #070b14;
      color: #f4f1ea;
    }}
    main {{
      max-width: 980px;
      margin: 0 auto;
      padding: 32px 20px 64px;
    }}
    p.kicker {{
      letter-spacing: 0.14em;
      text-transform: uppercase;
      font-family: "Segoe UI", sans-serif;
      font-size: 12px;
      color: #9fb0c9;
      margin: 0 0 8px;
    }}
    h1 {{
      font-size: clamp(32px, 5vw, 52px);
      line-height: 1.1;
      margin: 0 0 8px;
    }}
    p.when {{
      font-family: "Segoe UI", sans-serif;
      color: #c9d4e3;
      margin: 0 0 24px;
    }}
    figure {{ margin: 0 0 20px; }}
    img {{
      width: 100%;
      height: auto;
      display: block;
      background: #10182a;
      border-radius: 8px;
    }}
    figcaption, .credit, .note, .explanation, .source {{
      font-family: "Segoe UI", sans-serif;
      line-height: 1.55;
    }}
    .explanation {{ font-size: 18px; }}
    .credit, .note, .source, figcaption {{ color: #c9d4e3; }}
    a {{ color: #9ec1ff; }}
    .api {{
      margin-top: 28px;
      font-family: ui-monospace, monospace;
      font-size: 12px;
      color: #8ea0b8;
      word-break: break-all;
    }}
  </style>
</head>
<body>
  <main>
    <p class="kicker">NASA Astronomy Picture of the Day</p>
    <h1>{html.escape(entry["title"])}</h1>
    <p class="when">{html.escape(date_label)} <span>({html.escape(entry["date"])})</span></p>
    {video_note}
    <figure>
      <img src="/image?date={html.escape(entry["date"], quote=True)}" alt="{html.escape(entry["alt"])}" width="1600">
      <figcaption>Picture for {html.escape(entry["date"])}, loaded from the APOD API.</figcaption>
    </figure>
    {credit}
    <p class="explanation">{html.escape(entry["explanation"])}</p>
    {source}
    <p class="api">Queried {html.escape(entry["api_url"])}</p>
  </main>
</body>
</html>
"""


def render_error(message: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>APOD unavailable</title>
</head>
<body>
  <main>
    <h1>Could not load today's NASA picture</h1>
    <p>{html.escape(message)}</p>
  </main>
</body>
</html>
"""


class ApodHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        parts = urlsplit(self.path)
        if parts.path not in ("/", "/image"):
            self._send(404, "text/plain; charset=utf-8", b"Not found")
            return
        query = parse_qs(parts.query)
        raw_date = query.get("date", [None])[0]
        try:
            day = parse_apod_date(raw_date)
            entry = fetch_apod(day)
            if parts.path == "/image":
                data, media_type = fetch_picture(entry)
                self._send(200, media_type, data)
                return
            body = render_page(entry).encode("utf-8")
            self._send(200, "text/html; charset=utf-8", body)
        except ApodError as exc:
            body = render_error(str(exc)).encode("utf-8")
            self._send(502, "text/html; charset=utf-8", body)

    def _send(self, status: int, content_type: str, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args) -> None:
        print(f"[apod] {self.address_string()} {fmt % args}")


def serve(host: str = "127.0.0.1", port: int = 8765) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((host, port), ApodHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def main() -> None:
    host = os.environ.get("APOD_HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8765"))
    server = ThreadingHTTPServer((host, port), ApodHandler)
    today = apod_today()
    print(f"APOD viewer http://{host}:{port}/?date={today.isoformat()}")
    print(f"Querying {APOD_API}/?date={today.isoformat()}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping.")
        server.server_close()


if __name__ == "__main__":
    main()
