#!/usr/bin/env python3
"""Happ VPN 2.0: checked country exits, tested latency/stability, and manual backups."""
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
RU_MORE_SOURCES = {
    "fastnodes_ru": "https://raw.githubusercontent.com/rtwo2/FastNodes/main/sub/countries/RU.txt",
    "cheburnet_ru": "https://raw.githubusercontent.com/JeBance/CheburNet/gh-pages/cheburnet.txt",
    "nosok_verified": "https://raw.githubusercontent.com/aviamastersgh/vpn-free-russia/main/verified_configs.txt",
}
COUNTRIES = {
    "US": ("🇺🇸", "США"),
    "RU": ("🇷🇺", "РОССИЯ"),
    "DE": ("🇩🇪", "ГЕРМАНИЯ"),
    "NL": ("🇳🇱", "НИДЕРЛАНДЫ"),
    "FI": ("🇫🇮", "ФИНЛЯНДИЯ"),
    "FR": ("🇫🇷", "ФРАНЦИЯ"),
    "PL": ("🇵🇱", "ПОЛЬША"),
    "GB": ("🇬🇧", "ВЕЛИКОБРИТАНИЯ"),
    "CA": ("🇨🇦", "КАНАДА"),
    "JP": ("🇯🇵", "ЯПОНИЯ"),
    "SG": ("🇸🇬", "СИНГАПУР"),
    "SE": ("🇸🇪", "ШВЕЦИЯ"),
    "AT": ("🇦🇹", "АВСТРИЯ"),
    "CZ": ("🇨🇿", "ЧЕХИЯ"),
    "CH": ("🇨🇭", "ШВЕЙЦАРИЯ"),
    "IT": ("🇮🇹", "ИТАЛИЯ"),
    "ES": ("🇪🇸", "ИСПАНИЯ"),
    "HK": ("🇭🇰", "ГОНКОНГ"),
    "KR": ("🇰🇷", "ЮЖНАЯ КОРЕЯ"),
    "AU": ("🇦🇺", "АВСТРАЛИЯ"),
    "TW": ("🇹🇼", "ТАЙВАНЬ"),
    "TR": ("🇹🇷", "ТУРЦИЯ"),
    "UA": ("🇺🇦", "УКРАИНА"),
}
# Sampling limits, not a promise that a server will be reachable from the end user's network.
MAX_TESTS = {"US": 185, "RU": 420, "DE": 135, "NL": 135, "FI": 100,
             "FR": 115, "PL": 80, "GB": 95, "CA": 95, "JP": 130, "SG": 115, "SE": 85,
             "AT": 55, "CZ": 55, "CH": 55, "IT": 55, "ES": 55, "HK": 70,
             "KR": 70, "AU": 65, "TW": 65, "TR": 60, "UA": 60}
MAX_POOL = {"US": 48, "RU": 36, "DE": 38, "NL": 38, "FI": 24,
            "FR": 30, "PL": 22, "GB": 24, "CA": 24, "JP": 36, "SG": 36, "SE": 24,
            "AT": 20, "CZ": 20, "CH": 20, "IT": 20, "ES": 20, "HK": 28,
            "KR": 28, "AU": 24, "TW": 24, "TR": 20, "UA": 20}
MANUAL_LIMIT = {"US": 30, "RU": 28, "DE": 26, "NL": 26, "FI": 20,
                "FR": 24, "PL": 18, "GB": 20, "CA": 20, "JP": 28, "SG": 28, "SE": 20,
                "AT": 16, "CZ": 16, "CH": 16, "IT": 16, "ES": 16, "HK": 24,
                "KR": 24, "AU": 20, "TW": 20, "TR": 16, "UA": 16}
PRIVATE_IPS = ["geoip:private"]
BRAND = "XetsiwVPN"

def branded(title):
    return f"{BRAND} · {title}"



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
    rng = random.Random(int(time.time() // 86400) + sum(map(ord, country)))
    inputs = {"old": [], "au": [], "nexus": [], "radikal": [], "ru_extra": [],
              **({k: [] for k in RU_MORE_SOURCES} if country == "RU" else {})}
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
        for name, source_url in RU_MORE_SOURCES.items():
            try:
                data = qdecode(download(source_url))
                inputs[name] = [x for x in (convert_link(line) for line in data.splitlines()) if x]
                print(f"RU source {name}: {len(inputs[name])} compatible configs", flush=True)
            except Exception as e:
                print(f"RU source {name} failed: {str(e)[:160]}", flush=True)
    for key in ("au", "nexus", "radikal", "ru_extra", *(RU_MORE_SOURCES if country == "RU" else ())):
        rng.shuffle(inputs[key])
    dedup, seen, blocks = [], set(), {}
    # Existing working endpoints are sampled too; broaden to several operators / subnets.
    order = (["old", "fastnodes_ru", "nexus", "cheburnet_ru",
              "nosok_verified", "ru_extra", "fastnodes_ru", "nexus", "radikal"]
             if country == "RU" else
             ["old", "au", "nexus", "au", "nexus", "radikal"])
    while len(dedup) < MAX_TESTS[country] and any(inputs.values()):
        advanced = False
        for source in order:
            while inputs[source]:
                p = inputs[source].pop()
                if not safe(p): continue
                s, b = server(p), subnet(p)
                # Same endpoint with a different public credential can work after
                # the previous credential expires; test two variants per address.
                uid = p["settings"]["vnext"][0]["users"][0]["id"]
                credential = (s, uid, p["streamSettings"]["network"])
                block_limit = 7 if country == "RU" else 3
                if credential in seen or blocks.get(b, 0) >= block_limit:
                    continue
                seen.add(credential); blocks[b] = blocks.get(b, 0) + 1
                dedup.append(p)
                advanced = True
                break
            if len(dedup) >= MAX_TESTS[country]: break
        if not advanced: break
    print(country, "candidates", len(dedup),
          "sources", {k: len(v) for k, v in inputs.items()}, flush=True)
    return dedup

def probe(proxy, country):
    """Two HTTP probes through Xray to estimate response latency and short-term failures."""
    port = random.randint(21000, 62000)
    conf = {"log": {"loglevel": "error"}, "inbounds": [
        {"listen": "127.0.0.1", "port": port, "protocol": "socks",
         "settings": {"auth": "noauth"}}],
        "outbounds": [dict(proxy, tag="proxy")]}
    observations = []
    with tempfile.TemporaryDirectory() as temp:
        c = pathlib.Path(temp) / "xray.json"
        c.write_text(json.dumps(conf), encoding="utf-8")
        proc = subprocess.Popen(["./xray", "run", "-config", str(c)],
                                cwd=ROOT.parent, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            time.sleep(0.4)
            for endpoint in ("https://www.cloudflare.com/cdn-cgi/trace", "https://api.country.is/"):
                try:
                    t0 = time.monotonic()
                    r = subprocess.run([
                        "curl", "-fsS", "--max-time", "4", "--connect-timeout", "3",
                        "--socks5-hostname", f"127.0.0.1:{port}", endpoint],
                        text=True, capture_output=True, timeout=6)
                    ms = round((time.monotonic() - t0) * 1000)
                    if r.returncode != 0:
                        observations.append((None, ms))
                        continue
                    loc = re.search(r"(?m)^loc=([A-Z]{2})\s*$", r.stdout)
                    if loc:
                        found = loc.group(1)
                    else:
                        try:
                            found = str(json.loads(r.stdout).get("country", "")).upper()
                        except ValueError:
                            found = ""
                    observations.append((found if len(found) == 2 else None, ms))
                except (subprocess.TimeoutExpired, OSError):
                    observations.append((None, 6000))
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()
    good = [ms for loc, ms in observations if loc == country]
    wrong = [loc for loc, ms in observations if loc not in (None, country)]
    # Reject inconsistent egress countries to prevent country switching unexpectedly.
    valid = bool(good) and not wrong
    latency = round(median(good)) if good else None
    success_rate = len(good) / 2
    jitter_ms = abs(good[1] - good[0]) if len(good) == 2 else None
    return {"server": server(proxy), "exit": country if valid else (wrong[0] if wrong else None),
            "http_ms": latency, "success_rate": success_rate,
            "jitter_ms": jitter_ms, "ok": valid, "proxy": proxy}

def choose_verified(results, country):
    """Prefer stable responses, then short latency, while avoiding shared server subnets."""
    selected, net_seen, seen_servers = [], {}, set()
    candidates = sorted((r for r in results if r["ok"]),
                        key=lambda r: (r["success_rate"] < 1.0,
                                       (r["http_ms"] or 10000) + (r["jitter_ms"] or 700) * 0.25))
    for r in candidates:
        k = subnet(r["proxy"])
        endpoint = server(r["proxy"])
        if endpoint in seen_servers or net_seen.get(k, 0) >= (3 if country == "RU" else 2):
            continue
        net_seen[k] = net_seen.get(k, 0) + 1
        seen_servers.add(endpoint)
        selected.append(r)
        if len(selected) == MAX_POOL[country]:
            break
    return selected

def build_auto(template, country, emoji, name, verified, gaming=False):
    cfg = copy.deepcopy(template)
    suffix = "ИГРЫ — МИНИМАЛЬНЫЙ ПИНГ" if gaming else "АВТОВЫБОР — СТАБИЛЬНЫЙ"
    cfg["remarks"] = branded(f"{emoji} {name} — {suffix}")
    ranked = sorted(verified, key=lambda r: r["http_ms"] or 10000) if gaming else verified
    ranked = ranked[:5] if gaming else ranked
    outbounds = []
    prefix = country.lower() + ("-game-" if gaming else "-")
    for i, item in enumerate(ranked, 1):
        proxy = copy.deepcopy(item["proxy"])
        proxy["tag"] = f"{prefix}{i}"
        outbounds.append(proxy)
    if not outbounds:
        raise ValueError(f"{country}: empty profile")
    cfg["outbounds"] = outbounds + [{"tag": "direct", "protocol": "freedom", "settings": {}}]
    cfg["routing"] = {
        "domainStrategy": "AsIs",
        "balancers": [{"tag": "auto", "selector": [prefix],
                       "fallbackTag": outbounds[0]["tag"], "strategy": {"type": "leastPing"}}],
        "rules": [
            {"type": "field", "ip": PRIVATE_IPS, "outboundTag": "direct"},
            {"type": "field", "inboundTag": ["socks", "http"], "balancerTag": "auto"}]
    }
    cfg["observatory"] = {
        "subjectSelector": [prefix],
        "probeUrl": "https://www.gstatic.com/generate_204",
        "probeInterval": "20s" if gaming else "35s",
        "enableConcurrency": True
    }
    return cfg

def build_world(template, selected):
    """Global least HTTP latency, measured locally by Xray, over every distinct verified country node."""
    all_proxies = []
    seen = set()
    for country, nodes in selected.items():
        for r in nodes:
            p = r["proxy"]
            k = server(p)
            if k in seen:
                continue
            seen.add(k)
            all_proxies.append(r)
    if not all_proxies:
        raise RuntimeError("No working nodes to build world-wide selection")
    cfg = copy.deepcopy(template)
    cfg["remarks"] = branded("🌍 ВЕСЬ МИР — АВТОВЫБОР — МИНИМАЛЬНЫЙ ПИНГ")
    # Fallback and initial ordering prefer fastest known probe.
    all_proxies.sort(key=lambda x: (x.get("http_ms") is None,
                                    x.get("http_ms") or 99999))
    # Include a little of each country first, then rank by measured response delay.
    # Cap at 240: Xray checks all outbounds; huge lists create traffic and CPU load.
    representative = []
    picked = set()
    for code, group in selected.items():
        for r in sorted(group, key=lambda x: x.get("http_ms") or 99999)[:2]:
            key = server(r["proxy"])
            if key not in picked:
                picked.add(key)
                representative.append(r)
    remainder = [r for r in all_proxies if server(r["proxy"]) not in picked]
    all_proxies = representative + remainder[:max(0, 240 - len(representative))]
    outbounds = []
    for i, record in enumerate(all_proxies, 1):
        p = copy.deepcopy(record["proxy"])
        p["tag"] = f"world-{i}"
        outbounds.append(p)
    cfg["outbounds"] = outbounds + [
        {"tag": "direct", "protocol": "freedom", "settings": {}}
    ]
    cfg["routing"] = {
        "domainStrategy": "AsIs",
        "balancers": [{
            "tag": "auto",
            "selector": ["world-"],
            "fallbackTag": "world-1",
            "strategy": {"type": "leastPing"}
        }],
        "rules": [
            {"type": "field", "ip": PRIVATE_IPS, "outboundTag": "direct"},
            {"type": "field", "inboundTag": ["socks", "http"], "balancerTag": "auto"}
        ]
    }
    # Probing all at once frequently is excessive; 150 seconds limits CPU/bandwidth load.
    cfg["observatory"] = {
        "subjectSelector": ["world-"],
        "probeUrl": "https://www.gstatic.com/generate_204",
        "probeInterval": "150s",
        "enableConcurrency": True
    }
    return cfg


def build_ultra_world(world_cfg, verified_by_country=None):
    """Fast global selector: 112 distinct working endpoints from verified countries.

    Source measurements only seed initial order. Xray measures connection latency
    again on the Happ user's own device; not a guarantee of gaming latency.
    """
    cfg = copy.deepcopy(world_cfg)
    candidates = [p for p in world_cfg["outbounds"] if p.get("protocol") == "vless"]
    allowed = {server(p) for p in candidates}
    if verified_by_country:
        ranked_records = [r for group in verified_by_country.values() for r in group
                          if server(r["proxy"]) in allowed]
        ranked_records.sort(key=lambda r: (
            r.get("success_rate", 0) < 1,
            (r.get("http_ms") or 99999) + .2 * (r.get("jitter_ms") or 500)))
        ranked, seen = [], set()
        for record in ranked_records:
            p = record["proxy"]
            k = server(p)
            if k in seen: continue
            seen.add(k)
            ranked.append(p)
    else:
        ranked = candidates
    if len(ranked) < 80:
        raise ValueError("Need >=80 actually verified candidates for ultra mode")
    ranked = ranked[:112]
    proxies = []
    for index, p in enumerate(ranked, 1):
        node = copy.deepcopy(p)
        node["tag"] = f"ultra-{index}"
        proxies.append(node)
    cfg["remarks"] = branded("⚡ ВЕСЬ МИР — УЛЬТРА-ПИНГ — АВТОВЫБОР")
    cfg["outbounds"] = proxies + [{"tag": "direct", "protocol": "freedom", "settings": {}}]
    cfg["routing"]["balancers"] = [{
        "tag": "auto", "selector": ["ultra-"],
        "fallbackTag": "ultra-1", "strategy": {"type": "leastPing"}
    }]
    cfg["observatory"] = {
        "subjectSelector": ["ultra-"],
        "probeUrl": "https://www.gstatic.com/generate_204",
        "probeInterval": "60s",
        "enableConcurrency": True
    }
    return cfg


def build_manual(template, country, emoji, name, verified, i):
    cfg = copy.deepcopy(template)
    cfg["remarks"] = branded(f"{emoji} {name} — СЕРВЕР {i + 1}")
    p = copy.deepcopy(verified[i]["proxy"])
    p["tag"] = "proxy"
    cfg["outbounds"] = [p, {"tag": "direct", "protocol": "freedom", "settings": {}}]
    cfg["routing"] = {
        "domainStrategy": "AsIs",
        "rules": [
            {"type": "field", "ip": PRIVATE_IPS, "outboundTag": "direct"},
            {"type": "field", "inboundTag": ["socks", "http"], "outboundTag": "proxy"}]
    }
    cfg.pop("observatory", None)
    return cfg


def build_ru_fast(template, verified):
    """Small checked Russian-only leastPing pool, avoiding saturated slow fallbacks."""
    stable = [x for x in verified if x.get("success_rate", 0) == 1 and
              x.get("http_ms") is not None]
    stable.sort(key=lambda x: ((x["http_ms"] or 99999) +
                               (x.get("jitter_ms") or 0) * .2))
    chosen = stable[:min(6, len(stable))]
    if not chosen:
        chosen = [x for x in verified if x.get("proxy")][:3]
    if not chosen:
        raise ValueError("No RU candidates for fast mode")
    cfg = copy.deepcopy(template)
    cfg["remarks"] = branded("🇷🇺 РОССИЯ — БЫСТРЫЙ АВТОВЫБОР")
    out = []
    for i, item in enumerate(chosen, 1):
        p = copy.deepcopy(item["proxy"])
        p["tag"] = f"ru-fast-{i}"
        out.append(p)
    cfg["outbounds"] = out + [{"tag": "direct", "protocol": "freedom", "settings": {}}]
    cfg["routing"] = {
        "domainStrategy": "AsIs",
        "balancers": [{
            "tag": "auto", "selector": ["ru-fast-"],
            "fallbackTag": out[0]["tag"], "strategy": {"type": "leastPing"}
        }],
        "rules": [
            {"type": "field", "ip": PRIVATE_IPS, "outboundTag": "direct"},
            {"type": "field", "inboundTag": ["socks", "http"], "balancerTag": "auto"}
        ]
    }
    cfg["observatory"] = {
        "subjectSelector": ["ru-fast-"],
        "probeUrl": "https://www.gstatic.com/generate_204",
        "probeInterval": "45s",
        "enableConcurrency": True
    }
    return cfg


def build_discord_voice(template, country, emoji, name, verified, backup=False):
    """Pin Discord voice to one checked endpoint to avoid mid-call auto-switching.
    
    Happ must still use UDP-capable TUN; a JSON profile cannot force OS-wide interception.
    """
    eligible = [r for r in verified if r.get("success_rate") == 1.0 and
                r.get("proxy") and safe(r["proxy"])]
    if not eligible:
        eligible = [r for r in verified if r.get("proxy") and safe(r["proxy"])]
    if not eligible:
        raise ValueError("No stable node for Discord " + country)
    eligible.sort(key=lambda r: (r.get("http_ms") is None,
                                 (r.get("http_ms") or 99999) +
                                 0.2 * (r.get("jitter_ms") or 1000)))
    index = 1 if backup and len(eligible) > 1 else 0
    picked = eligible[index]
    cfg = copy.deepcopy(template)
    cfg["remarks"] = branded(f"🎧 DISCORD — {name} — " + ("РЕЗЕРВ" if backup else "ГОЛОС RTC"))
    proxy = copy.deepcopy(picked["proxy"])
    proxy["tag"] = "proxy"
    cfg["outbounds"] = [proxy, {"tag": "direct", "protocol": "freedom", "settings": {}}]
    cfg["routing"] = {
        "domainStrategy": "AsIs",
        "rules": [
            {"type": "field", "ip": PRIVATE_IPS, "outboundTag": "direct"},
            {"type": "field", "network": "udp", "outboundTag": "proxy"},
            {"type": "field", "inboundTag": ["socks", "http"], "outboundTag": "proxy"}
        ]
    }
    cfg.pop("observatory", None)
    # The local UDP relay remains enabled when used with Happ TUN.
    for inbound in cfg.get("inbounds", []):
        if inbound.get("protocol") == "socks":
            inbound.setdefault("settings", {})["udp"] = True
    return cfg


def preflight_profiles(existing):
    """Detect missing generator variables before lengthy remote checks."""
    template = next((p for p in existing if "АВТОВЫБОР" in p.get("remarks", "")), None)
    if template is None:
        raise RuntimeError("Missing subscription template")
    candidate = next((x for x in template["outbounds"] if safe(x)), None)
    if candidate is None:
        raise RuntimeError("No valid prior proxy for preflight")
    sample = {"proxy": candidate, "server": server(candidate), "http_ms": 100,
              "success_rate": 1.0, "jitter_ms": 0, "exit": "US"}
    build_auto(template, "US", "🇺🇸", "США", [sample])
    build_auto(template, "US", "🇺🇸", "США", [sample], gaming=True)
    build_manual(template, "US", "🇺🇸", "США", [sample], 0)
    build_world(template, {"US": [sample]})
    # Ultra needs >=80 distinct verified servers; checked at actual build time.
    build_discord_voice(template, "US", "🇺🇸", "США", [sample])
    build_ru_fast(template, [sample])


def main():
    current = json.loads(TARGET.read_text(encoding="utf-8"))
    preflight_profiles(current)
    # Prior auto profiles act as a fallback if a provider is temporarily unavailable.
    old_bases = {}
    for country, (_, label) in COUNTRIES.items():
        old_bases[country] = next((p for p in current
                                   if f"{COUNTRIES[country][0]} {label} — АВТОВЫБОР — СТАБИЛЬНЫЙ" in p.get("remarks", "")), None)
    template = old_bases["US"] or old_bases["RU"]
    if template is None:
        raise RuntimeError("No usable template found in existing Happ subscription")
    report = {
        "version": "2.0",
        "verified_from": "GitHub Actions runner, not user's device/network",
        "checked_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "limitations": "HTTP response time is not ICMP ping and cannot predict game ping",
        "countries": {}
    }
    selected = {}
    for country, (emoji, label) in COUNTRIES.items():
        old = old_bases[country]
        old_outbounds = (old or {}).get("outbounds", [])
        candidates = gather(country, old_outbounds)
        checks = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
            for result in executor.map(lambda p: probe(p, country), candidates):
                checks.append(result)
                if result["ok"]:
                    print(country, result["server"], result["http_ms"],
                          "ms", "success", result["success_rate"], flush=True)
        verified = choose_verified(checks, country)
        retained_old = False
        if not verified and old is not None:
            # Preserve known old country-specific nodes in temporary source outages.
            verified = [
                {"proxy": p, "server": server(p), "exit": "previously checked",
                 "http_ms": None, "success_rate": 0, "jitter_ms": None}
                for p in old_outbounds if safe(p)
            ][:MAX_POOL[country]]
            retained_old = bool(verified)
        if verified:
            selected[country] = verified
        report["countries"][country] = {
            "tested": len(checks),
            "country_verified": sum(1 for x in checks if x["ok"]),
            "wrong_country": sum(x["exit"] not in (None, country) for x in checks),
            "retained_old_nodes": retained_old,
            "selected": [
                {"server": x["server"], "http_ms": x["http_ms"],
                 "jitter_ms": x["jitter_ms"], "success_rate": x["success_rate"],
                 "exit": x["exit"]}
                for x in verified]
        }
    profiles = [build_world(template, selected)] if selected else []
    if profiles and sum(1 for x in profiles[0]["outbounds"] if x["protocol"] == "vless") >= 80:
        profiles.insert(0, build_ultra_world(profiles[0], selected))
    for country, (emoji, name) in COUNTRIES.items():
        verified = selected.get(country)
        if not verified:
            print(country, "no verified exit; no new profile added", flush=True)
            continue
        template_country = old_bases[country] or template
        profiles.append(build_auto(template_country, country, emoji, name, verified))
    if selected.get("RU"):
        profiles.insert(1, build_ru_fast(old_bases["RU"] or template, selected["RU"]))
    # Keep gaming modes distinct; gaming selector prioritizes the lowest measured HTTP RTT.
    for country in ("US", "RU"):
        if selected.get(country):
            emoji, name = COUNTRIES[country]
            profiles.append(build_auto(old_bases[country] or template,
                                       country, emoji, name, selected[country], gaming=True))
    europe = []
    for code in ("DE", "NL", "FI", "FR", "PL", "GB", "SE", "AT", "CZ", "CH", "IT", "ES", "TR", "UA"):
        europe.extend(selected.get(code, []))
    if europe:
        europe = sorted(europe, key=lambda x: x["http_ms"] or 99999)[:8]
        profiles.append(build_auto(template, "EU", "🎮", "ЕВРОПА",
                                   europe, gaming=True))
    # Discord UDP voice: fixed server so observatory does not switch during active calls.
    for country in ("NL", "DE", "RU", "US"):
        if selected.get(country):
            emoji, name = COUNTRIES[country]
            template_country = old_bases[country] or template
            profiles.append(build_discord_voice(template_country, country, emoji, name,
                                                selected[country]))
            if len(selected[country]) > 1:
                profiles.append(build_discord_voice(template_country, country, emoji, name,
                                                    selected[country], backup=True))
    # Standalone profiles let Happ users measure from their own network.
    for country, (emoji, name) in COUNTRIES.items():
        verified = selected.get(country)
        if not verified:
            continue
        for i in range(min(len(verified), MANUAL_LIMIT[country])):
            profiles.append(build_manual(old_bases[country] or template, country,
                                         emoji, name, verified, i))
    # Validate selected tags / Xray balancer references to prevent startup failures.
    unique_names = set()
    for item in profiles:
        name = item["remarks"]
        if name in unique_names:
            raise ValueError("Duplicate profile: " + name)
        unique_names.add(name)
        out = item["outbounds"]
        tags = [x["tag"] for x in out]
        if len(tags) != len(set(tags)):
            raise ValueError("Duplicate outbound tags")
        for o in out:
            if o["protocol"] == "vless" and not safe(o):
                raise ValueError("Unsupported transport: " + name)
        for bal in item["routing"].get("balancers", []):
            if bal["fallbackTag"] not in tags:
                raise ValueError("Invalid failover tag")
            if not any(t.startswith(bal["selector"][0]) for t in tags):
                raise ValueError("Invalid observatory selector")
    if not profiles:
        raise RuntimeError("No verified profiles or fallback pools")
    TARGET.write_text(json.dumps(profiles, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")
    print("HAPP V2 profiles:", len(profiles), "countries:",
          list(selected.keys()), flush=True)

if __name__ == "__main__":
    main()
