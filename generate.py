#!/usr/bin/env python3
"""Generate a square pixel-art render with Nano Banana 2 (gemini-3.1-flash-image).

    GEMINI_API_KEY=... python3 generate.py square_cat     ->  visuals/square_cat.png

The prompt is prompts/base.txt followed by prompts/<scene>.txt. The request is the
Interactions API call from Jixoo's RECIPES.md (https://github.com/glaforge/jixoo).
"""
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
URL = "https://generativelanguage.googleapis.com/v1beta/interactions"


def find_image(node):
    """(mime type, base64 data) of the first image in the response, wherever it is nested."""
    if isinstance(node, dict):
        mime = node.get("mime_type") or node.get("mimeType") or ""
        if mime.startswith("image/") and isinstance(node.get("data"), str):
            return mime, node["data"]
        node = list(node.values())
    if isinstance(node, list):
        for item in node:
            found = find_image(item)
            if found:
                return found
    return None


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: python3 generate.py <scene>   (a file in prompts/, e.g. square_cat)")
    scene = sys.argv[1]
    key = os.environ.get("GEMINI_API_KEY") or sys.exit("set GEMINI_API_KEY first")
    prompt = "\n\n".join((ROOT / "prompts" / f).read_text().strip() for f in ("base.txt", f"{scene}.txt"))

    body = {"model": "models/gemini-3.1-flash-image", "input": prompt,
            "response_format": {"type": "image", "aspect_ratio": "1:1"}}
    request = urllib.request.Request(URL, data=json.dumps(body).encode(), method="POST",
                                     headers={"Content-Type": "application/json", "x-goog-api-key": key})
    try:
        with urllib.request.urlopen(request) as response:
            reply = json.load(response)
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code}: {e.read().decode(errors='replace')[:800]}")

    out_dir = ROOT / "visuals"
    out_dir.mkdir(exist_ok=True)
    found = find_image(reply)
    if not found:
        dump = out_dir / f"{scene}.json"
        dump.write_text(json.dumps(reply, indent=2))
        sys.exit(f"no image in the response; saved it to {dump}")
    mime, data = found
    out = out_dir / f"{scene}.{'jpg' if 'jpeg' in mime else mime.split('/')[1]}"
    out.write_bytes(base64.b64decode(data))
    print(f"{out.relative_to(ROOT)} written; next: python3 pixoo64.py {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
