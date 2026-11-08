"""Check that the viewer loads a real APOD picture for today's date."""

from __future__ import annotations

import datetime as dt
import unittest
import urllib.request
from urllib.parse import urlencode

import app


def image_dimensions(data: bytes) -> tuple[int, int] | None:
    if data.startswith(b"\xff\xd8"):
        index = 2
        while index + 9 < len(data):
            if data[index] != 0xFF:
                index += 1
                continue
            marker = data[index + 1]
            if marker in (0xC0, 0xC1, 0xC2):
                height = int.from_bytes(data[index + 5 : index + 7], "big")
                width = int.from_bytes(data[index + 7 : index + 9], "big")
                return width, height
            if marker in (0xD8, 0xD9):
                index += 2
                continue
            if index + 4 > len(data):
                break
            length = int.from_bytes(data[index + 2 : index + 4], "big")
            if length < 2:
                break
            index += 2 + length
        return None
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        width = int.from_bytes(data[16:20], "big")
        height = int.from_bytes(data[20:24], "big")
        return width, height
    return None


class TodayApodTest(unittest.TestCase):
    def test_today_picture_renders(self) -> None:
        today = app.apod_today()
        server = app.serve("127.0.0.1", 0)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        port = server.server_address[1]
        query = urlencode({"date": today.isoformat()})

        page = urllib.request.urlopen(f"http://127.0.0.1:{port}/?{query}", timeout=60)
        html = page.read().decode("utf-8")
        self.assertEqual(page.status, 200)
        self.assertIn(today.isoformat(), html)
        self.assertIn(f"/image?date={today.isoformat()}", html)
        self.assertIn(f"apod-basic/?date={today.isoformat()}", html)
        self.assertNotIn("Could not load", html)

        picture = urllib.request.urlopen(f"http://127.0.0.1:{port}/image?{query}", timeout=60)
        data = picture.read()
        content_type = picture.headers.get("Content-Type", "")
        self.assertTrue(content_type.startswith("image/"), content_type)
        self.assertGreater(len(data), 20_000)
        width, height = image_dimensions(data) or (0, 0)
        self.assertGreaterEqual(width, 600, f"picture width {width} is too small to be the APOD photo")
        self.assertGreaterEqual(height, 400, f"picture height {height} is too small to be the APOD photo")

        entry = app.fetch_apod(today)
        self.assertEqual(entry["date"], today.isoformat())
        self.assertIn(entry["title"], html)
        self.assertNotIn("nasa-logo", entry["hdurl"])
        self.assertEqual(entry["date"], dt.date.fromisoformat(entry["date"]).isoformat())


if __name__ == "__main__":
    unittest.main()
