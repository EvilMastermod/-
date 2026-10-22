#!/usr/bin/env python3
"""Refresh Happ USA/Russia auto groups and individual nodes, verifying country + HTTP RTT."""
from __future__ import annotations
import base64
import concurrent.futures
import copy
import ipaddress
import json
import pathlib
import random
import re
import subprocess
import tempfile
import time
import urllib.parse
import urllib.request
from statistics import median

ROOT = pathlib.Path(__file__).resolve().parent
TARGET = ROOT / "Happ_US_RU_Auto.json"
REPORT = ROOT / "FAST_NODES_RESULTS.json"
AU_SOURCE = "https://raw.githubusercontent.com/Au1rxx/free-vpn-subscriptions/main/output/country/{}/singbox-0001.json"
NEXUS_SOURCE = "https://raw.githubusercontent.com/ninjastrikers/Nexus-nodes/main/configs/countries/{}/all.txt"
RADIKAL_SOURCE = "https://raw.githubusercontent.com/0xRadikal/Free-v2ray-Configs/main/top100.txt"
RU_EXTRA_SOURCE = "https://raw.githubusercontent.com/aviamastersgh/vpn-free-russia/main/ru_configs.txt"
MAX_TESTS = {"US": 115, "RU": 220}
MAX_POOL = {"US": 16, "RU": 12}

def download(url):
    request = urllib.request.Request(url, headers={"User-Agent": "Happ-VPN-Feed-Checker/2.0"})
    with urllib.request.urlopen(request, timeout=28) as response:
        return response.read().decode("utf-8", errors="replace")

def qdecode(text):
    text = text.strip()
    if re.search(r"(?m)^(?:vless|trojan)://", text):
        return text
    try:
        decoded = base64.b64decode(re.sub(r"\s+", "", text) + "=" * (-len(text.strip()) % 4))
        return decoded.decode("utf-8", "replace")
    except (ValueError, UnicodeDecodeError):
        return ""

def convert_singbox(o):
    if o.get("type") != "vless" or not all(o.get(k) for k in ("server", "server_port", "uuid")):
        return None
    tls = o.get("tls") or {}
    if not tls.get("enabled"):
        return None
    trans = o.get("transport") or {}
    net = trans.get("type") or "tcp"
    if net not in ("tcp", "ws", "grpc"):
        return None
    reality = tls.get("reality") or {}
    if reality.get("enabled") and net == "ws":
        return None
    stream = {"network": net, "security": "reality" if reality.get("enabled") else "tls"}
    if stream["security"] == "reality":
        if not reality.get("public_key"): return None
        stream["realitySettings"] = {
            "serverName": tls.get("server_name") or "",
            "publicKey": reality["public_key"],
            "shortId": reality.get("short_id") or "",
            "fingerprint": (tls.get("utls") or {}).get("fingerprint") or "chrome",
            "spiderX": "/"
        }
    else:
        stream["tlsSettings"] = {
            "serverName": tls.get("server_name") or o["server"],
            "allowInsecure": bool(tls.get("insecure", False)),
            "fingerprint": (tls.get("utls") or {}).get("fingerprint") or "chrome",
        }
    if net == "ws":
        stream["wsSettings"] = {"path": trans.get("path") or "/", "headers": trans.get("headers") or {}}
    if net == "grpc":
        stream["grpcSettings"] = {"serviceName": trans.get("service_name") or "", "multiMode": False}
    user = {"id": o["uuid"], "encryption": "none"}
    if o.get("flow") and net == "tcp":
        user["flow"] = o["flow"]
    return {"tag": "proxy", "protocol": "vless", "settings": {
        "vnext": [{"address": o["server"], "port": o["server_port"], "users": [user]}]},
        "streamSettings": stream}

def convert_link(raw):
    try:
        p = urllib.parse.urlsplit(raw.strip())
        if p.scheme != "vless" or not all((p.hostname, p.username, p.port)):
            return None
        q = urllib.parse.parse_qs(p.query, keep_blank_values=True)
        get = lambda k, d="": q.get(k, [d])[0]
        security, net = get("security"), get("type", "tcp")
        if security not in ("tls", "reality") or net not in ("tcp", "ws", "grpc"):
            return None
        if security == "reality" and net == "ws":
            return None
        stream = {"network": net, "security": security}
        if security == "reality":
            if not get("pbk"): return None
            stream["realitySettings"] = {
                "publicKey": get("pbk"), "shortId": get("sid"),
                "serverName": get("sni"), "fingerprint": get("fp", "chrome"),
                "spiderX": get("spx", "/")}
        else:
            stream["tlsSettings"] = {
                "serverName": get("sni", p.hostname),
                "allowInsecure": get("allowInsecure", "0") == "1",
                "fingerprint": get("fp", "chrome")}
        if net == "ws":
            stream["wsSettings"] = {
                "path": get("path", "/"), "headers": {"Host": get("host", p.hostname)}}
        if net == "grpc":
            stream["grpcSettings"] = {"serviceName": get("serviceName"), "multiMode": False}
        user = {"id": urllib.parse.unquote(p.username), "encryption": "none"}
        if get("flow") and net == "tcp":
            user["flow"] = get("flow")
        return {"tag": "proxy", "protocol": "vless", "settings": {
            "vnext": [{"address": p.hostname, "port": p.port, "users": [user]}]},
            "streamSettings": stream}
    except (ValueError, TypeError, KeyError):
        return None

def server(proxy):
    if proxy.get("protocol") != "vless":
        return ""
    try:
        conn = proxy["settings"]["vnext"][0]
        return str(conn["address"]) + ":" + str(conn["port"])
    except (KeyError, IndexError):
        return ""

def safe(proxy):
    stream = proxy.get("streamSettings") or {}
    return bool(server(proxy)) and stream.get("security") in ("reality", "tls") and (
        stream.get("network") in ("tcp", "grpc") or
        (stream.get("network") == "ws" and stream.get("security") == "tls")
    )

def subnet(proxy):
    addr = server(proxy).rsplit(":", 1)[0]
    try:
        ip = ipaddress.ip_address(addr)
        if ip.version == 4:
            return ".".join(addr.split(".")[:3])
    except ValueError:
        pass
    return addr.lower()

def gather(country, old):
    rng = random.Random(int(time.time() // 86400))
    inputs = {"old": [], "au": [], "nexus": [], "radikal": [], "ru_extra": []}
    inputs["old"] = [o for o in old if safe(o)]
    try:
        raw = json.loads(download(AU_SOURCE.format(country)))
        inputs["au"] = [x for x in (convert_singbox(n) for n in raw.get("outbounds", [])) if x]
    except Exception as e:
        print(f"{country} Au1rxx: {str(e)[:160]}", flush=True)
    try:
        decoded = qdecode(download(NEXUS_SOURCE.format(country.lower())))
        inputs["nexus"] = [x for x in (convert_link(line) for line in decoded.splitlines()) if x]
    except Exception as e:
        print(f"{country} Nexus: {str(e)[:160]}", flush=True)
    # Unlabeled public source: exit country must pass active country check.
    try:
        decoded = qdecode(download(RADIKAL_SOURCE))
        inputs["radikal"] = [x for x in (convert_link(line) for line in decoded.splitlines()) if x]
    except Exception as e:
        print(f"{country} Radikal: {str(e)[:160]}", flush=True)
    if country == "RU":
        try:
            data = download(RU_EXTRA_SOURCE)
            inputs["ru_extra"] = [x for x in (convert_link(line) for line in data.splitlines()) if x]
        except Exception as e:
            print(f"{country} extra source: {str(e)[:160]}", flush=True)
    for key in ("au", "nexus", "radikal", "ru_extra"):
        rng.shuffle(inputs[key])
    dedup, seen, blocks = [], set(), {}
    # Existing working endpoints are sampled too; broaden to several operators / subnets.
    order = ["old", "au", "ru_extra", "nexus", "au", "ru_extra", "nexus", "radikal"]
    while len(dedup) < MAX_TESTS[country] and any(inputs.values()):
        advanced = False
        for source in order:
            while inputs[source]:
                p = inputs[source].pop()
                if not safe(p): continue
                s, b = server(p), subnet(p)
                if s in seen or blocks.get(b, 0) >= 3:
                    continue
                seen.add(s); blocks[b] = blocks.get(b, 0) + 1
                dedup.append(p)
                advanced = True
                break
            if len(dedup) >= MAX_TESTS[country]: break
        if not advanced: break
    print(country, "candidates", len(dedup),
          "sources", {k: len(v) for k, v in inputs.items()}, flush=True)
    return dedup

def probe(proxy, country):
    port = random.randint(21000, 62000)
    conf = {"log": {"loglevel": "error"}, "inbounds": [
        {"listen": "127.0.0.1", "port": port, "protocol": "socks",
         "settings": {"auth": "noauth"}}],
        "outbounds": [dict(proxy, tag="proxy")]}
    with tempfile.TemporaryDirectory() as temp:
        c = pathlib.Path(temp) / "xray.json"
        c.write_text(json.dumps(conf), encoding="utf-8")
        proc = subprocess.Popen(["./xray", "run", "-config", str(c)],
                                cwd=ROOT.parent, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            time.sleep(0.35)
            for url in ("https://www.cloudflare.com/cdn-cgi/trace", "https://api.country.is/"):
                try:
                    t0 = time.monotonic()
                    r = subprocess.run([
                        "curl", "-fsS", "--max-time", "5", "--connect-timeout", "3",
                        "--socks5-hostname", f"127.0.0.1:{port}", url],
                        text=True, capture_output=True, timeout=7)
                    elapsed = round((time.monotonic() - t0) * 1000)
                    if r.returncode != 0: continue
                    loc = re.search(r"(?m)^loc=([A-Z]{2})\s*$", r.stdout)
                    if loc:
                        found = loc.group(1)
                    else:
                        try: found = json.loads(r.stdout).get("country", "").upper()
                        except ValueError: found = ""
                    if len(found) == 2:
                        return {"server": server(proxy), "exit": found,
                                "http_ms": elapsed, "ok": found == country, "proxy": proxy}
                except (subprocess.TimeoutExpired, OSError):
                    pass
            return {"server": server(proxy), "exit": None, "http_ms": None,
                    "ok": False, "proxy": proxy}
        finally:
            proc.terminate()
            try: proc.wait(timeout=2)
            except subprocess.TimeoutExpired: proc.kill()

def choose_verified(results, country):
    selected, exit_seen, net_seen = [], set(), {}
    candidates = sorted((r for r in results if r["ok"]), key=lambda x: x["http_ms"])
    for r in candidates:
        k = subnet(r["proxy"])
        if net_seen.get(k, 0) >= 2:
            continue
        net_seen[k] = net_seen.get(k, 0) + 1
        selected.append(r)
        if len(selected) == MAX_POOL[country]: break
    return selected

def main():
    existing = json.loads(TARGET.read_text(encoding="utf-8"))
    out, report = {}, {"verified_from": "GitHub-hosted runner (not the user's network)",
                       "checked_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                       "countries": {}}
    for country, label in (("US", "США"), ("RU", "РОССИЯ")):
        old = next(x for x in existing if label in x["remarks"] and "АВТОВЫБОР" in x["remarks"])
        candidates = gather(country, old["outbounds"])
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
            for r in pool.map(lambda o: probe(o, country), candidates):
                results.append(r)
                if r["ok"]: print(country, r["server"], r["http_ms"], "ms", flush=True)
        verified = choose_verified(results, country)
        # Never silently replace a functioning subscription with an empty one.
        if not verified:
            print(country, "no verified nodes; preserving old group", flush=True)
            old_nodes = [x for x in old["outbounds"] if safe(x)]
            verified = [{"proxy": p, "server": server(p), "exit": "not_rechecked",
                         "http_ms": None} for p in old_nodes]
        out[country] = (old, verified)
        report["countries"][country] = {
            "tested": len(results),
            "country_verified": sum(1 for x in results if x["ok"]),
            "other_country": sum(x["exit"] not in (None, country) for x in results),
            "selected": [{"server": x["server"], "http_ms": x["http_ms"],
                          "exit": x["exit"]} for x in verified]}
    rebuilt = []
    for country in ("US", "RU"):
        original, ranked = out[country]
        base = copy.deepcopy(original)
        base["outbounds"] = []
        for i, item in enumerate(ranked):
            proxy = copy.deepcopy(item["proxy"])
            proxy["tag"] = f'{country.lower()}-{i+1}'
            base["outbounds"].append(proxy)
        base["outbounds"].append({"tag": "direct", "protocol": "freedom", "settings": {}})
        if not ranked:
            raise RuntimeError("Empty country: " + country)
        base["routing"]["balancers"][0]["fallbackTag"] = f'{country.lower()}-1'
        base["routing"]["balancers"][0]["selector"] = [f'{country.lower()}-']
        base["observatory"]["subjectSelector"] = [f'{country.lower()}-']
        rebuilt.append(base)
    # User may manually select individual endpoints without relying on auto balancer.
    for country, emoji, name in (("US", "🇺🇸", "США"), ("RU", "🇷🇺", "Россия")):
        original, verified = out[country]
        for i, item in enumerate(verified[:8], 1):
            one = copy.deepcopy(original)
            one["remarks"] = f"{emoji} {name} — сервер {i}"
            p = copy.deepcopy(item["proxy"])
            p["tag"] = "proxy"
            one["outbounds"] = [p, {"tag": "direct", "protocol": "freedom", "settings": {}}]
            one["routing"] = {"domainStrategy": "AsIs",
                              "rules": [
                                  {"type": "field", "ip": ["geoip:private"], "outboundTag": "direct"},
                                  {"type": "field", "inboundTag": ["socks", "http"], "outboundTag": "proxy"}]}
            one.pop("observatory", None)
            rebuilt.append(one)
    # Avoid invalid Xray combinations recurring during automated updates.
    for profile in rebuilt:
        assert all(safe(x) for x in profile["outbounds"] if x["protocol"] == "vless")
    TARGET.write_text(json.dumps(rebuilt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Wrote", len(rebuilt), "Happ profiles; updated with active country exit checks", flush=True)

if __name__ == "__main__":
    main()
