#!/usr/bin/env python3
"""Update two Happ/Xray leastPing profiles from public, externally checked nodes."""
from __future__ import annotations
import json
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
TARGET = ROOT / "Happ_US_RU_Auto.json"
SOURCE = "https://raw.githubusercontent.com/Au1rxx/free-vpn-subscriptions/main/output/country/{}/singbox-0001.json"

def xray(o, tag):
    if o.get("type") != "vless" or not all(o.get(k) for k in ("server", "server_port", "uuid")):
        return None
    tls = o.get("tls") or {}
    if not tls.get("enabled"):
        return None
    transport = o.get("transport") or {}
    network = transport.get("type", "tcp")
    if network not in ("tcp", "ws", "grpc"):
        return None
    reality = tls.get("reality") or {}
    stream = {"network": network, "security": "reality" if reality.get("enabled") else "tls"}
    if stream["security"] == "reality":
        if not reality.get("public_key"):
            return None
        stream["realitySettings"] = {
            "show": False,
            "serverName": tls.get("server_name", ""),
            "fingerprint": (tls.get("utls") or {}).get("fingerprint") or "chrome",
            "publicKey": reality["public_key"],
            "shortId": reality.get("short_id", ""),
            "spiderX": "/",
        }
    else:
        stream["tlsSettings"] = {
            "serverName": tls.get("server_name") or o["server"],
            "allowInsecure": bool(tls.get("insecure")),
            "fingerprint": (tls.get("utls") or {}).get("fingerprint") or "chrome",
        }
    if network == "ws":
        stream["wsSettings"] = {"path": transport.get("path") or "/", "headers": transport.get("headers") or {}}
    elif network == "grpc":
        stream["grpcSettings"] = {"serviceName": transport.get("service_name") or "", "multiMode": False}
    user = {"id": o["uuid"], "encryption": "none"}
    if o.get("flow") and network == "tcp":
        user["flow"] = o["flow"]
    return {"tag": tag, "protocol": "vless", "settings": {"vnext": [
        {"address": o["server"], "port": o["server_port"], "users": [user]}
    ]}, "streamSettings": stream}

def choose(outbounds, country):
    max_count = 16 if country == "US" else 12
    found, seen, blocks = [], set(), {}
    for item in outbounds:
        if item.get("type") != "vless" or not (item.get("tls") or {}).get("enabled"):
            continue
        key = (item.get("server"), item.get("server_port"))
        if key in seen:
            continue
        block = ".".join(str(item.get("server", "")).split(".")[:3])
        if country == "US" and blocks.get(block, 0) >= 2:
            continue
        converted = xray(item, country.lower() + "-" + str(len(found) + 1))
        if converted is None:
            continue
        seen.add(key)
        blocks[block] = blocks.get(block, 0) + 1
        found.append(converted)
        if len(found) >= max_count:
            break
    if len(found) < 3:
        raise ValueError(f"{country}: too few valid nodes ({len(found)})")
    return found

def profile(country, proxies):
    prefix = country.lower() + "-"
    return {
        "remarks": "🇺🇸 США — АВТОВЫБОР" if country == "US" else "🇷🇺 РОССИЯ — АВТОВЫБОР",
        "log": {"loglevel": "warning"},
        "dns": {"servers": ["1.1.1.1", "8.8.8.8"]},
        "inbounds": [
            {"tag": "socks", "listen": "127.0.0.1", "port": 10808, "protocol": "socks",
             "settings": {"auth": "noauth", "udp": True},
             "sniffing": {"enabled": True, "destOverride": ["http", "tls", "quic"]}},
            {"tag": "http", "listen": "127.0.0.1", "port": 10809, "protocol": "http", "settings": {}}
        ],
        "outbounds": [*proxies, {"tag": "direct", "protocol": "freedom", "settings": {}}],
        "routing": {"domainStrategy": "AsIs",
                    "balancers": [{"tag": "auto", "selector": [prefix],
                                   "strategy": {"type": "leastPing"}, "fallbackTag": proxies[0]["tag"]}],
                    "rules": [
                        {"type": "field", "ip": ["geoip:private"], "outboundTag": "direct"},
                        {"type": "field", "inboundTag": ["socks", "http"], "balancerTag": "auto"}
                    ]},
        "observatory": {"subjectSelector": [prefix],
                        "probeUrl": "https://www.gstatic.com/generate_204",
                        "probeInterval": "30s", "enableConcurrency": True}
    }

def main():
    profiles = []
    for country in ("US", "RU"):
        url = SOURCE.format(country)
        request = urllib.request.Request(url, headers={"User-Agent": "HappFreeNodesUpdater/1.0"})
        with urllib.request.urlopen(request, timeout=45) as response:
            source = json.load(response)
        proxies = choose(source["outbounds"], country)
        profiles.append(profile(country, proxies))
        print(country, len(proxies), "unique candidate nodes")
    output = json.dumps(profiles, ensure_ascii=False, indent=2) + "\n"
    TARGET.write_text(output, encoding="utf-8")

if __name__ == "__main__":
    main()
