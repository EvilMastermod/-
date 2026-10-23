#!/usr/bin/env python3
"""Refresh Russia-only pool through real Xray HTTP exit checks without touching other country profiles."""
from __future__ import annotations
import concurrent.futures
import copy
import json
import pathlib
import time
import refresh_fast as core

ROOT = pathlib.Path(__file__).resolve().parent
CONFIG = ROOT / "Happ_US_RU_Auto.json"
REPORT = ROOT / "FAST_NODES_RESULTS.json"

def key(node):
    return core.server(node)

def refresh():
    profiles = json.loads(CONFIG.read_text(encoding="utf-8"))
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    ru = next(p for p in profiles if "🇷🇺 РОССИЯ — АВТОВЫБОР — СТАБИЛЬНЫЙ" in p["remarks"])
    original_nodes = [x for x in ru["outbounds"] if x.get("protocol") == "vless"]
    candidates = core.gather("RU", original_nodes)
    results = []
    print("Starting RU-only check:", len(candidates), flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
        for r in pool.map(lambda o: core.probe(o, "RU"), candidates):
            results.append(r)
            if r["ok"]:
                print("RU verified", r["server"], r["http_ms"], "ms", r["success_rate"], flush=True)
    selected = core.choose_verified(results, "RU")
    if not selected:
        print("No verified Russian nodes on this pass, preserving existing profile.", flush=True)
        return
    new_profiles = [
        core.build_auto(ru, "RU", "🇷🇺", "РОССИЯ", selected),
        core.build_ru_fast(ru, selected),
        core.build_auto(ru, "RU", "🇷🇺", "РОССИЯ", selected, gaming=True)
    ]
    for i in range(min(len(selected), core.MANUAL_LIMIT["RU"])):
        new_profiles.append(core.build_manual(ru, "RU", "🇷🇺", "РОССИЯ", selected, i))
    new_profiles.append(core.build_discord_voice(ru, "RU", "🇷🇺", "РОССИЯ", selected))
    if len(selected) > 1:
        new_profiles.append(core.build_discord_voice(ru, "RU", "🇷🇺", "РОССИЯ", selected, backup=True))
    # Keep other country profiles unchanged.
    profiles = [p for p in profiles
                if not ("🇷🇺 РОССИЯ — " in p["remarks"] or
                        "🎧 DISCORD — РОССИЯ — " in p["remarks"])]
    at = 2 if len(profiles) > 1 and any("⚡ ВЕСЬ МИР" in p["remarks"] for p in profiles) else (1 if profiles and any("🌍 ВЕСЬ МИР" in p["remarks"] for p in profiles) else 0)
    profiles[at:at] = new_profiles

    # Refresh only Russian candidates in worldwide auto mode; preserve global pool and other locations.
    world = next((p for p in profiles if "🌍 ВЕСЬ МИР" in p["remarks"]), None)
    if world:
        previous = {key(p) for p in original_nodes}
        existing = [p for p in world["outbounds"] if p["protocol"] == "vless"
                    and key(p) not in previous]
        known = {key(p) for p in existing}
        additions = []
        for r in selected:
            p = copy.deepcopy(r["proxy"])
            if key(p) in known:
                continue
            additions.append(p)
            known.add(key(p))
        max_size = 240
        remaining = existing[:max(0, max_size-len(additions))]
        all_nodes = remaining + additions
        for i, p in enumerate(all_nodes, 1):
            p["tag"] = f"world-{i}"
        world["outbounds"] = all_nodes + [{"tag": "direct", "protocol": "freedom", "settings": {}}]
        world["routing"]["balancers"][0]["fallbackTag"] = all_nodes[0]["tag"]
        # Keep the separate >=80-node branded ultra mode synchronized.
        ultra_index = next((i for i, p in enumerate(profiles)
                            if "⚡ ВЕСЬ МИР — УЛЬТРА-ПИНГ" in p["remarks"]), None)
        if ultra_index is not None and len(all_nodes) >= 80:
            profiles[ultra_index] = core.build_ultra_world(world)

    report.setdefault("countries", {})["RU"] = {
        "tested": len(results),
        "country_verified": sum(r["ok"] for r in results),
        "wrong_country": sum(r["exit"] not in (None, "RU") for r in results),
        "retained_old_nodes": False,
        "selected": [{"server": r["server"], "http_ms": r.get("http_ms"),
                      "jitter_ms": r.get("jitter_ms"), "success_rate": r.get("success_rate"),
                      "exit": r["exit"]} for r in selected]
    }
    report["ru_updated_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    # Other concurrent jobs may have generated older, unbranded profiles.
    for p in profiles:
        if not p["remarks"].startswith(core.BRAND + " · "):
            p["remarks"] = core.branded(p["remarks"])
    if world and not any("⚡ ВЕСЬ МИР — УЛЬТРА-ПИНГ" in p["remarks"] for p in profiles):
        if len([p for p in world["outbounds"] if p["protocol"] == "vless"]) >= 80:
            profiles.insert(0, core.build_ultra_world(world))
    profile_names = [p["remarks"] for p in profiles]
    if len(profile_names) != len(set(profile_names)):
        raise ValueError("Duplicate profile names after RU-only refresh")
    for p in profiles:
        outbound_tags = [o["tag"] for o in p["outbounds"]]
        if len(outbound_tags) != len(set(outbound_tags)):
            raise ValueError("Duplicate outbound tags in "+p["remarks"])
    CONFIG.write_text(json.dumps(profiles, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print("Russian nodes verified:", len(selected), "; total Happ profiles:", len(profiles), flush=True)

if __name__ == "__main__":
    refresh()
