#!/usr/bin/env python3
"""Discover multiple DISTINCT, Xray-tested Spacetime alternatives without touching the old feed."""
from __future__ import annotations
import concurrent.futures
import copy
import ipaddress
import json
import pathlib
import subprocess
import tempfile
import time
from collections import Counter

import refresh_fast as core
from find_alternative_spacetime import confirm_exit_ip

HERE = pathlib.Path(__file__).resolve().parent
MAIN = HERE / "Happ_US_RU_Auto.json"
OUTPUT = HERE / "XetsiwVPN_Spacetime_Multi.json"
REPORT = HERE / "XetsiwVPN_Spacetime_Multi_report.json"
OLD_SPECIAL = HERE / "XetsiwVPN_Spacetime_NEW_IP.json"
COUNTRIES = [("US", "🇺🇸", "США", 10, 175),
             ("UA", "🇺🇦", "УКРАИНА", 5, 60),
             ("RU", "🇷🇺", "РОССИЯ", 5, 180)]
TOTAL_CAP = 20

def ip_or_none(value):
    try:
        return str(ipaddress.ip_address(value))
    except (ValueError, TypeError):
        return None

def endpoint(p):
    return core.server(p)

def all_vless(profiles):
    for profile in profiles:
        for p in profile.get("outbounds", []):
            if p.get("protocol") == "vless" and endpoint(p):
                yield p

def syntax_ok(profile):
    with tempfile.TemporaryDirectory() as d:
        path = pathlib.Path(d) / "test.json"
        path.write_text(json.dumps(profile, ensure_ascii=False), encoding="utf-8")
        result = subprocess.run(["./xray", "run", "-test", "-config", str(path)],
                                cwd=HERE.parent, capture_output=True, text=True, timeout=12)
        return result.returncode == 0

def main():
    main_profiles = json.loads(MAIN.read_text(encoding="utf-8"))
    previous_profiles = json.loads(OLD_SPECIAL.read_text(encoding="utf-8")) if OLD_SPECIAL.exists() else []
    previous = list(all_vless(main_profiles + previous_profiles))
    old_endpoints = {endpoint(p) for p in previous}
    old_addresses = {ip_or_none(p["settings"]["vnext"][0]["address"]) for p in previous}
    seen_exits = set(old_addresses)
    seen_exits.discard(None)
    # A previously reported blocked IP should never be re-added.
    seen_exits.update(["216.167.126.97", "213.226.127.71"])
    old_count = len(main_profiles)
    used = set(old_endpoints)
    selected = []
    stats = {}
    checked = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    templates = {}
    for country, emoji, name, _, _ in COUNTRIES:
        templates[country] = next((p for p in main_profiles
           if f"{emoji} {name} — АВТОВЫБОР — СТАБИЛЬНЫЙ" in p.get("remarks", "")), None)

    for country, emoji, name, quota, cap in COUNTRIES:
        print(country, "discovering candidates", flush=True)
        discovered = core.gather(country, [])
        unique = []
        used_local = set()
        for p in discovered:
            ep = endpoint(p)
            if not ep or ep in old_endpoints or ep in used_local:
                continue
            used_local.add(ep)
            unique.append(p)
            if len(unique) >= cap:
                break
        stats[country] = {"new_endpoints_available": len(unique),
                          "tunnel_country_verified": 0, "new_distinct_exits": 0}
        if not unique:
            print(country, "no fresh endpoints", flush=True)
            continue
        with concurrent.futures.ThreadPoolExecutor(max_workers=24) as pool:
            verified = [r for r in pool.map(lambda p: core.probe(p, country), unique)
                        if r["ok"] and r["exit"] == country]
        stats[country]["tunnel_country_verified"] = len(verified)
        verified.sort(key=lambda r: (r["success_rate"] < 1, r.get("http_ms") or 99999))
        template = templates[country] or templates.get("US")
        if not template:
            print(country, "no valid template", flush=True)
            continue
        # Check actual exit IP twice through the SOCKS5 tunnel, never just the TCP port.
        for rec in verified[:min(50, len(verified))]:
            if stats[country]["new_distinct_exits"] >= quota or len(selected) >= TOTAL_CAP:
                break
            ep = rec["server"]
            if ep in used:
                continue
            exit_ip = confirm_exit_ip(rec["proxy"], country)
            print(country, ep, "EXIT", exit_ip, flush=True)
            if not exit_ip or exit_ip in seen_exits:
                continue
            cfg = core.build_manual(template, country, emoji, name, [rec], 0)
            cfg["remarks"] = core.branded(f"{emoji} SPACETIME — АЛЬТЕРНАТИВА {len(selected)+1:02d} — {exit_ip}")
            if not syntax_ok(cfg):
                print(country, "Xray syntax failed", ep, flush=True)
                continue
            used.add(ep)
            seen_exits.add(exit_ip)
            selected.append({"profile": cfg, "country": country, "exit_ip": exit_ip,
                             "endpoint": ep, "http_ms": rec.get("http_ms"),
                             "success_rate": rec.get("success_rate")})
            stats[country]["new_distinct_exits"] += 1

    report = {"checked_utc": checked, "verified_from": "GitHub Actions Xray SOCKS5",
              "original_profile_count": old_count, "original_subscription_unchanged": True,
              "previous_single_ip_excluded": "216.167.126.97",
              "searched_countries": ["US", "UA", "RU"],
              "candidates_by_country": stats,
              "verified_distinct_alternatives": len(selected),
              "servers": [{k: v for k, v in s.items() if k != "profile"} for s in selected],
              "note": "Verified tunnels do not prove Spacetime accepts an IP. No Spacetime app login was tested."}
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not selected:
        print("NO VERIFIED NEW IPs; old subscription and existing Spacetime profile unchanged", flush=True)
        raise SystemExit(2)
    OUTPUT.write_text(json.dumps([s["profile"] for s in selected], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("VERIFIED_MULTI", len(selected), json.dumps(report["servers"], ensure_ascii=False), flush=True)

if __name__ == "__main__":
    main()
