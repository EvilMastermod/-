#!/usr/bin/env python3
"""Verify actual VLESS egress IP through a SOCKS5 tunnel, not just a TCP port."""
import ipaddress
import json
import pathlib
import socket
import subprocess
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROFILE = ROOT / "vpn/XetsiwVPN_Spacetime_NEW_IP.json"
ORIGINAL = ROOT / "vpn/Happ_US_RU_Auto.json"
REPORT = pathlib.Path(__file__).with_name("tunnel_report.json")
result = {"status": "failed", "method": "Xray VLESS -> local SOCKS5 -> api.country.is"}

def curl(url, socks=False):
    args = ["curl", "-fsS", "--max-time", "12", "--connect-timeout", "6"]
    if socks:
        args += ["--socks5-hostname", "127.0.0.1:10808", "--noproxy", ""]
    return subprocess.check_output(args + [url], text=True, timeout=15).strip()

try:
    configs = json.loads(PROFILE.read_text(encoding="utf-8"))
    config = configs[0]
    proxy = next(p for p in config["outbounds"] if p.get("tag") == "proxy")
    if proxy["protocol"] != "vless":
        raise ValueError("Unexpected proxy protocol")
    host = proxy["settings"]["vnext"][0]["address"]
    port = proxy["settings"]["vnext"][0]["port"]
    result["endpoint"] = str(host) + ":" + str(port)
    old = json.loads(ORIGINAL.read_text(encoding="utf-8"))
    result["old_profiles"] = len(old)
    old_endpoints = {str(p["settings"]["vnext"][0]["address"])+":"+str(p["settings"]["vnext"][0]["port"])
       for profile in old for p in profile.get("outbounds", []) if p.get("protocol") == "vless"}
    old_addresses = {str(p["settings"]["vnext"][0]["address"])
       for profile in old for p in profile.get("outbounds", []) if p.get("protocol") == "vless"}
    result["new_endpoint"] = result["endpoint"] not in old_endpoints
    if not result["new_endpoint"]:
        raise ValueError("Endpoint already in main subscription")
    result["runner_ip"] = curl("https://api.ipify.org")
    single = pathlib.Path(__file__).with_name("xray_test_config.json")
    single.write_text(json.dumps(config), encoding="utf-8")
    validated = subprocess.run(["./xray", "run", "-test", "-config", str(single)], cwd=ROOT,
        capture_output=True, text=True, timeout=12)
    if validated.returncode:
        raise RuntimeError("Xray config invalid: " + validated.stderr[-300:])
    with open("/tmp/spacetime-xray.log", "w") as log:
        proc = subprocess.Popen(["./xray", "run", "-config", str(single)], cwd=ROOT,
            stdout=log, stderr=subprocess.STDOUT)
        try:
            for _ in range(30):
                if proc.poll() is not None:
                    raise RuntimeError("Xray stopped unexpectedly")
                try:
                    with socket.create_connection(("127.0.0.1", 10808), timeout=0.2):
                        break
                except OSError:
                    time.sleep(0.2)
            else:
                raise RuntimeError("SOCKS5 listener not started")
            responses = [json.loads(curl("https://api.country.is/", True)) for _ in range(2)]
            ips = [r.get("ip") for r in responses]
            countries = [r.get("country") for r in responses]
            result["observed_exit_ips"] = ips
            result["observed_countries"] = countries
            if len(set(ips)) != 1 or countries != ["US", "US"]:
                raise RuntimeError("Exit IP unstable or wrong country")
            if not ipaddress.ip_address(ips[0]).is_global:
                raise RuntimeError("Exit IP is not public")
            if ips[0] == result["runner_ip"]:
                raise RuntimeError("Proxy bypass detected: runner public IP returned")
            result["exit_ip_not_in_old_endpoints"] = ips[0] not in old_addresses
            if not result["exit_ip_not_in_old_endpoints"]:
                raise RuntimeError("Observed exit IP also used by an existing profile")
            result["status"] = "success"
        finally:
            proc.terminate()
            try: proc.wait(timeout=4)
            except subprocess.TimeoutExpired: proc.kill()
except Exception as exc:
    result["error"] = str(exc)
finally:
    REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
if result["status"] != "success":
    raise SystemExit(1)
