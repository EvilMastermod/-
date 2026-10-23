import csv
import json
import os
import socket
import ssl
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
RESULTS = {"checked_at": datetime.now(timezone.utc).isoformat(), "candidates": []}
def fetch(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "XetsiwVPN-connectivity-diagnostic/1.0"})
        with urllib.request.urlopen(req, timeout=8) as response:
            return {"status": response.status, "final_url": response.url, "text": response.read(512).decode("utf-8", "replace")}
    except Exception as exc:
        return {"error": str(exc)}

RESULTS["github_runner_public_ip"] = fetch("https://api.ipify.org")
host = os.getenv("SPACETIME_HOST", "").strip().lower()
if host:
    if "/" in host or ":" in host or "@" in host or " " in host:
        RESULTS["target"] = {"error": "Provide only a hostname, no URL or port"}
    else:
        response = fetch("https://" + host + "/")
        response.pop("text", None)
        RESULTS["target"] = response
else:
    RESULTS["target"] = {"skipped": "No Spacetime host given. No application-specific check performed."}

with (BASE / "candidates.csv").open(newline="") as f:
    for row in csv.DictReader(f):
        item = dict(row)
        protocol = item["protocol"].lower()
        if protocol == "tcp":
            try:
                with socket.create_connection((item["host"], int(item["port"])), timeout=5):
                    item["tcp_reachable"] = True
            except OSError as e:
                item["tcp_reachable"] = False
                item["detail"] = str(e)
        else:
            item["note"] = "UDP status cannot be determined by a simple handshake-free port test."
        RESULTS["candidates"].append(item)

path = BASE / "report.json"
path.write_text(json.dumps(RESULTS, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(RESULTS, ensure_ascii=False, indent=2))
