#!/usr/bin/env python3
"""Create an independent XetsiwVPN subscription with a NEW public exit IP.

Only works when a fresh node passes Xray country & outbound IP verification.
The existing main subscription is NEVER overwritten.
"""
from __future__ import annotations
import concurrent.futures
import copy
import ipaddress
import json
import pathlib
import random
import subprocess
import tempfile
import time
import refresh_fast as core

HERE = pathlib.Path(__file__).resolve().parent
MAIN = HERE / "Happ_US_RU_Auto.json"
OUTPUT = HERE / "XetsiwVPN_Spacetime_NEW_IP.json"
REPORT = HERE / "XetsiwVPN_Spacetime_NEW_IP_report.json"
CHOSEN_COUNTRIES = [
    ("US", "🇺🇸", "США"),
    ("UA", "🇺🇦", "УКРАИНА"),
    ("RU", "🇷🇺", "РОССИЯ"),
]

def ipv4_or_none(text):
    try:
        ip = ipaddress.ip_address(text)
        return str(ip) if isinstance(ip, ipaddress.IPv4Address) and ip.is_global else None
    except ValueError:
        return None

def endpoint(p):
    return core.server(p)

def confirm_exit_ip(p, expected_country):
    """Two matching real external IP checks THROUGH the tunnel, not local IP."""
    sock_port = random.randint(22000, 60500)
    conf = {
        "log": {"loglevel": "error"},
        "inbounds": [{"protocol":"socks", "listen":"127.0.0.1", "port":sock_port,
                      "settings":{"auth":"noauth", "udp":True}}],
        "outbounds": [dict(copy.deepcopy(p), tag="proxy")],
    }
    with tempfile.TemporaryDirectory() as folder:
        config_path = pathlib.Path(folder) / "xray.json"
        config_path.write_text(json.dumps(conf), encoding="utf-8")
        proc = subprocess.Popen(["./xray", "run", "-config", str(config_path)],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                cwd=HERE.parent)
        try:
            time.sleep(.5)
            ips = []
            for _ in range(2):
                response = subprocess.run(
                    ["curl","-fsS","--max-time","6","--connect-timeout","3",
                     "--socks5-hostname",f"127.0.0.1:{sock_port}",
                     "https://api.country.is/"],
                    capture_output=True, text=True, timeout=8)
                if response.returncode:
                    return None
                try:
                    payload = json.loads(response.stdout)
                except ValueError:
                    return None
                ip = ipv4_or_none(str(payload.get("ip", "")))
                if payload.get("country", "").upper() != expected_country or not ip:
                    return None
                ips.append(ip)
            return ips[0] if len(ips) == 2 and ips[0] == ips[1] else None
        finally:
            proc.terminate()
            try: proc.wait(timeout=2)
            except subprocess.TimeoutExpired: proc.kill()

def main():
    current = json.loads(MAIN.read_text(encoding="utf-8"))
    current_endpoints = set()
    known_ips = set()
    for profile in current:
        for outbound in profile.get("outbounds", []):
            if outbound.get("protocol") != "vless":
                continue
            current_endpoints.add(endpoint(outbound))
            addr = outbound["settings"]["vnext"][0]["address"]
            if ipv4_or_none(addr):
                known_ips.add(addr)
    # Protect against accidentally reusing a previously mentioned Russian IP.
    known_ips.add("213.226.127.71")

    for country, emoji, label in CHOSEN_COUNTRIES:
        print(f"Country {country}: gathering fresh servers", flush=True)
        candidates = core.gather(country, [])
        unique = []
        dedup = set()
        for candidate in candidates:
            key = endpoint(candidate)
            if key in current_endpoints or key in dedup:
                continue
            dedup.add(key)
            unique.append(candidate)
        if not unique:
            print(country, "no new endpoints outside existing XetsiwVPN", flush=True)
            continue

        # More US candidates are checked first because it has many reliable free exits.
        cap = 165 if country == "US" else 120
        unique = unique[:cap]
        print(country, "different endpoints queued:", len(unique), flush=True)
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=24) as executor:
            for r in executor.map(lambda p: core.probe(p, country), unique):
                if r["ok"] and r["exit"] == country:
                    results.append(r)
        results.sort(key=lambda r: (
            r.get("success_rate", 0) < 1,
            (r.get("http_ms") or 99999) + .2 * (r.get("jitter_ms") or 1000)))
        print(country, "Xray-verified NEW endpoints:", len(results), flush=True)

        for record in results[:20]:
            exit_ip = confirm_exit_ip(record["proxy"], country)
            print(country, record["server"], "exit_ip:", exit_ip, flush=True)
            if not exit_ip or exit_ip in known_ips:
                continue
            # Avoid apparent duplicates if another checked node shares the same public exit.
            template = next((p for p in current if f"{emoji} {label} — АВТОВЫБОР — СТАБИЛЬНЫЙ"
                             in p.get("remarks", "")), None)
            if template is None:
                print(country, "no template in subscription", flush=True)
                continue
            cfg = core.build_manual(template, country, emoji, label, [record], 0)
            cfg["remarks"] = core.branded(f"{emoji} SPACETIME — ДРУГОЙ IP — {exit_ip}")
            with tempfile.TemporaryDirectory() as d:
                path = pathlib.Path(d) / "test.json"
                path.write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")
                tested = subprocess.run(["./xray","run","-test","-config",str(path)],
                                        capture_output=True, text=True,
                                        cwd=HERE.parent, timeout=10)
                if tested.returncode:
                    raise RuntimeError("Final Xray profile failed: "+tested.stderr[-500:])
            OUTPUT.write_text(json.dumps([cfg], ensure_ascii=False, indent=2)+"\n",
                              encoding="utf-8")
            REPORT.write_text(json.dumps({
                "country": country, "exit_ip": exit_ip,
                "server_endpoint": record["server"], "checked_utc":
                time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
                "http_ms_from_github_runner": record["http_ms"],
                "not_in_existing_subscription_endpoints": True,
                "existing_profiles_kept_unchanged": True,
                "note": "A fresh endpoint/exit IP is not proof that the game has not blocked it."
            }, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
            print("SUCCESS NEW DISTINCT IP", country, exit_ip,
                  "server:", record["server"], flush=True)
            return
    raise RuntimeError("No confirmed different US, UA, or RU exit; existing VPN unchanged")

if __name__ == "__main__":
    main()
