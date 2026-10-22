#!/usr/bin/env python3
"""Live-check public RU-exit VLESS nodes with Xray, update Happ RU group only when verified."""
import base64
import concurrent.futures
import json
import pathlib
import random
import re
import socket
import subprocess
import tempfile
import time
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
SUB = ROOT / "Happ_US_RU_Auto.json"
REPORT = ROOT / "RU_PROBE_RESULTS.json"
NEXUS = "https://raw.githubusercontent.com/ninjastrikers/Nexus-nodes/main/configs/countries/ru/all.txt"

def parse_link(link):
    try:
        p = urllib.parse.urlsplit(link.strip())
        if p.scheme != "vless" or not p.hostname or not p.username or not p.port:
            return None
        q = urllib.parse.parse_qs(p.query)
        get = lambda k, d="": q.get(k, [d])[0]
        security = get("security", "none")
        net = get("type", "tcp")
        if security not in ("tls", "reality") or net not in ("tcp", "ws", "grpc"):
            return None
        stream = {"network": net, "security": security}
        # REALITY + WS cannot start in Xray.
        if security == "reality" and net not in ("tcp", "grpc"):
            return None
        if security == "reality":
            if not get("pbk"):
                return None
            stream["realitySettings"] = {
                "serverName": get("sni"), "publicKey": get("pbk"),
                "shortId": get("sid"), "fingerprint": get("fp", "chrome"), "spiderX": get("spx", "/")}
        else:
            stream["tlsSettings"] = {"serverName": get("sni", p.hostname),
                                     "allowInsecure": get("allowInsecure", "0") == "1",
                                     "fingerprint": get("fp", "chrome")}
        if net == "ws":
            stream["wsSettings"] = {"path": get("path", "/"),
                                    "headers": {"Host": get("host")}}
        if net == "grpc":
            stream["grpcSettings"] = {"serviceName": get("serviceName")}
        user = {"id": urllib.parse.unquote(p.username), "encryption": "none"}
        if get("flow") and net == "tcp":
            user["flow"] = get("flow")
        return {"tag": "candidate", "protocol": "vless", "settings": {"vnext": [{
            "address": p.hostname, "port": p.port, "users": [user]}]},
            "streamSettings": stream}
    except (ValueError, KeyError, TypeError):
        return None

def fetch_nodes():
    request = urllib.request.Request(NEXUS, headers={"User-Agent": "HappRUChecker/1.0"})
    with urllib.request.urlopen(request, timeout=30) as resp:
        data = resp.read().decode("utf-8", "replace").strip()
    if not "vless://" in data[:1024]:
        try:
            data = base64.b64decode(data + "=" * (-len(data) % 4)).decode("utf-8", "replace")
        except Exception:
            return []
    output = []
    for line in data.splitlines():
        node = parse_link(line)
        if node is not None:
            output.append(node)
    return output

def key(proxy):
    n = proxy["settings"]["vnext"][0]
    return f'{n["address"]}:{n["port"]}'

def test(proxy):
    port = 20000 + random.randint(0, 42000)
    config = {
        "log": {"loglevel": "error"},
        "inbounds": [{"listen": "127.0.0.1", "port": port, "protocol": "socks",
                      "settings": {"auth": "noauth", "udp": False}}],
        "outbounds": [proxy]
    }
    with tempfile.TemporaryDirectory() as temp:
        path = pathlib.Path(temp) / "config.json"
        path.write_text(json.dumps(config), encoding="utf-8")
        proc = subprocess.Popen(["./xray", "run", "-config", str(path)],
                                cwd=ROOT.parent, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            time.sleep(0.4)
            for endpoint in ("https://api.country.is/", "https://ipinfo.io/json"):
                result = subprocess.run([
                    "curl", "-sS", "--insecure", "--max-time", "7",
                    "--socks5-hostname", f"127.0.0.1:{port}",
                    endpoint], text=True, capture_output=True, timeout=9)
                if result.returncode != 0:
                    continue
                try:
                    result_json = json.loads(result.stdout)
                except ValueError:
                    continue
                country = result_json.get("country")
                if isinstance(country, str) and len(country) == 2:
                    return {"server": key(proxy), "country": country.upper(), "ok": True, "proxy": proxy}
            return {"server": key(proxy), "country": None, "ok": False, "proxy": proxy}
        finally:
            proc.terminate()
            try: proc.wait(timeout=2)
            except subprocess.TimeoutExpired: proc.kill()

def main():
    profiles = json.loads(SUB.read_text(encoding="utf-8"))
    ru = next(p for p in profiles if "РОССИЯ" in p["remarks"])
    current = [x for x in ru["outbounds"] if x.get("protocol") == "vless"]
    try:
        extras = fetch_nodes()
    except Exception as exc:
        print("Extra source unavailable:", str(exc)[:150])
        extras = []
    found, seen = [], set()
    for item in current + extras:
        k = key(item)
        if k in seen:
            continue
        seen.add(k)
        found.append(item)
    found = found[:65]
    print("Distinct candidates:", len(found), flush=True)
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
        for item in pool.map(test, found):
            results.append(item)
            print(item["server"], item["country"] or "unavailable", flush=True)
    passed = [r["proxy"] for r in results if r["country"] == "RU"]
    report = {
        "checked_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "tested": len(found),
        "working_ru_exit": len(passed),
        "working_other_exit": sum(x["ok"] and x["country"] != "RU" for x in results),
        "candidate_servers": [{"server": x["server"], "country": x["country"]} for x in results],
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not passed:
        print("No RU exit validated: leaving subscription unchanged.", flush=True)
        return
    # Preserve 🇺🇸 profile. RU balancer always references exact ru- prefixes.
    safe = []
    for i, p in enumerate(passed[:12], 1):
        p["tag"] = f"ru-{i}"
        safe.append(p)
    ru["outbounds"] = safe + [x for x in ru["outbounds"] if x.get("tag") == "direct"]
    ru["routing"]["balancers"][0]["fallbackTag"] = safe[0]["tag"]
    SUB.write_text(json.dumps(profiles, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Updated RU auto-select with", len(safe), "verified RU-exit proxies.")

if __name__ == "__main__":
    main()
