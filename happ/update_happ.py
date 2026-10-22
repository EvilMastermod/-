#!/usr/bin/env python3
"""Refresh a Happ URI subscription from third-party public proxy lists."""
import hashlib
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = "https://raw.githubusercontent.com/rtwo2/FastNodes/main/sub/countries/"
COUNTRIES = [
    ("US", "🇺🇸 USA", 16),
    ("RU", "🇷🇺 Russia", 12),
    ("DE", "🇩🇪 Germany", 6),
    ("NL", "🇳🇱 Netherlands", 6),
    ("FI", "🇫🇮 Finland", 6),
]

def nodes(code):
    request = urllib.request.Request(
        BASE + code + ".txt", headers={"User-Agent": "Happ-Free-Subscription/1.0"}
    )
    with urllib.request.urlopen(request, timeout=40) as response:
        content = response.read(2_500_000).decode("utf-8", errors="replace")
    usable = []
    for raw in content.splitlines()[:1000]:
        line = raw.strip().replace("&amp;", "&")
        if not line.startswith("vless://") or len(line) > 2500:
            continue
        if "allowInsecure=1" in line or "allowInsecure=true" in line:
            continue
        try:
            url = urllib.parse.urlsplit(line)
            params = urllib.parse.parse_qs(url.query)
            mode = params.get("security", [""])[0]
            if mode not in ("reality", "tls"):
                continue
            if mode == "reality" and len(params.get("pbk", [""])[0]) < 20:
                continue
            if not url.hostname or not url.port or len(url.hostname) > 130:
                continue
            host = url.hostname.lower()
            score = hashlib.sha256((code + host + str(url.port)).encode()).digest()
            usable.append((score, host, line.split("#", 1)[0]))
        except ValueError:
            continue
    return sorted(usable)

def main():
    lines = [
        "#profile-title: EvilMaster Free VPN",
        "#profile-update-interval: 6",
    ]
    seen = set()
    stats = {"updated_utc": datetime.now(timezone.utc).isoformat()}
    for code, name, target in COUNTRIES:
        count = 0
        for _, host, uri in nodes(code):
            if host in seen:
                continue
            seen.add(host)
            count += 1
            lines.append(uri + "#" + urllib.parse.quote(f"{name} {count:02d}"))
            if count == target:
                break
        stats[code] = count
    if stats["US"] < 3 or stats["RU"] < 3:
        raise RuntimeError("Not enough nodes; previous subscription left unchanged")
    (ROOT / "subscription.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (ROOT / "status.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(stats)

if __name__ == "__main__":
    main()
