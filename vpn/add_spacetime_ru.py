#!/usr/bin/env python3
"""Publish a dedicated different verified Russian exit for XetsiwVPN.

The candidate must be absent from the existing subscription, pass real VLESS
tunnel HTTP country tests and return an RU egress IPv4 not shared with the
previously used RU server endpoints. Do not publish an unverified node.
"""
import copy
import ipaddress
import json
import pathlib
import random
import subprocess
import tempfile
import time
import concurrent.futures
import refresh_fast as core

BASE=pathlib.Path(__file__).resolve().parent
TARGET=BASE/"Happ_US_RU_Auto.json"
SINGLE=BASE/"XetsiwVPN_Spacetime_RU.json"
REPORT=BASE/"XetsiwVPN_Spacetime_RU_check.json"
SOURCES=[
  "https://raw.githubusercontent.com/whoahaow/rjsxrd/main/githubmirror/bypass/bypass-7.txt",
  "https://raw.githubusercontent.com/whoahaow/rjsxrd/main/githubmirror/bypass/bypass-6.txt",
  "https://raw.githubusercontent.com/rtwo2/FastNodes/main/sub/countries/RU.txt",
]
TITLE_PREFIX="XetsiwVPN · 🇷🇺 SPACETIME — ДРУГОЙ РОССИЙСКИЙ IP"
BLOCKED={"213.226.127.71", "127.0.0.1"}

def egress_ip(proxy):
    """Query a second independent service using an actual Xray SOCKS tunnel."""
    port=random.randint(21000, 61000)
    config={
      "log":{"loglevel":"error"},
      "inbounds":[{"listen":"127.0.0.1","port":port,"protocol":"socks",
                   "settings":{"auth":"noauth","udp":True}}],
      "outbounds":[dict(copy.deepcopy(proxy),tag="proxy")]
    }
    with tempfile.TemporaryDirectory() as tmp:
        filepath=pathlib.Path(tmp)/"config.json"
        filepath.write_text(json.dumps(config),encoding="utf-8")
        process=subprocess.Popen(["./xray","run","-config",str(filepath)],
                                cwd=BASE.parent,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        try:
            time.sleep(.6)
            observed=[]
            for _ in range(2):
                r=subprocess.run(
                    ["curl","-fsS","--max-time","7","--connect-timeout","4",
                     "--socks5-hostname",f"127.0.0.1:{port}","https://api.country.is/"],
                    text=True,capture_output=True,timeout=9)
                if r.returncode:
                    continue
                try:
                    info=json.loads(r.stdout)
                    address=str(info.get("ip",""))
                    ipaddress.IPv4Address(address)
                    if info.get("country","").upper()=="RU":
                        observed.append(address)
                except (ValueError,KeyError):
                    continue
            if len(observed)==2 and len(set(observed))==1:
                return observed[0]
        finally:
            process.terminate()
            try:process.wait(timeout=2)
            except subprocess.TimeoutExpired:process.kill()
    return None

def run():
    existing=json.loads(TARGET.read_text(encoding="utf-8"))
    prev={core.server(x) for p in existing for x in p.get("outbounds",[])
          if x.get("protocol")=="vless"}
    old_ru_endpoints={x for p in existing if "РОССИЯ" in p.get("remarks","")
                      for x in (core.server(o) for o in p.get("outbounds",[])
                                if o.get("protocol")=="vless")}
    prior_exit_ips={x.split(":")[0] for x in old_ru_endpoints if x.split(":")[0].count(".")==3}
    candidates=[]
    seen=set()
    for url in SOURCES:
        try:
            raw=core.qdecode(core.download(url))
            for line in raw.splitlines():
                if not line.startswith("vless://"):continue
                p=core.convert_link(line)
                if not p or not core.safe(p):continue
                endpoint=core.server(p)
                if endpoint in prev or endpoint in seen:continue
                seen.add(endpoint)
                priority=(0 if "9f6635t.msk1.h1clayd.click" in line else
                          1 if "🇷🇺" in line or "%F0%9F%87%B7" in line else 2)
                candidates.append((priority,p))
            print(url,"new unique candidates so far",len(candidates),flush=True)
        except Exception as e:
            print("Source unavailable:",url,str(e)[:150],flush=True)
    candidates.sort(key=lambda item:item[0])
    candidates=[p for _,p in candidates[:125]]
    if not candidates:
        raise RuntimeError("No new VLESS server endpoints outside existing subscription")
    print("Checking fresh candidates",len(candidates),flush=True)
    # Probe prioritized endpoints concurrently, preserving source order.
    with concurrent.futures.ThreadPoolExecutor(max_workers=18) as pool:
        checked=list(pool.map(lambda p:core.probe(p,"RU"),candidates))
    verified=[r for r in checked if r["ok"] and r["exit"]=="RU"]
    verified.sort(key=lambda r:(r.get("success_rate")!=1,
                              r.get("http_ms") or 99999))
    print("Previously unused RU candidates after real Xray checks:",len(verified),flush=True)
    picked=None; ip=None
    for result in verified[:22]:
        candidate_ip=egress_ip(result["proxy"])
        print("Candidate",result["server"],"RU egress",candidate_ip,flush=True)
        if not candidate_ip or candidate_ip in BLOCKED or candidate_ip in prior_exit_ips:
            continue
        picked=result
        ip=candidate_ip
        break
    if not picked:
        raise RuntimeError("No independently verified DIFFERENT Russian exit; leaving current VPN unchanged")
    template=next(p for p in existing if "РОССИЯ — АВТОВЫБОР" in p["remarks"])
    cfg=core.build_manual(template,"RU","🇷🇺","РОССИЯ",[picked],0)
    cfg["remarks"]=f"{TITLE_PREFIX} · {ip}"
    # Ensure Xray accepts the final profile before publication.
    with tempfile.TemporaryDirectory() as tmp:
        path=pathlib.Path(tmp)/"spacetime.json"
        path.write_text(json.dumps(cfg,ensure_ascii=False),encoding="utf-8")
        r=subprocess.run(["./xray","run","-test","-config",str(path)],
                         capture_output=True,text=True,cwd=BASE.parent,timeout=10)
        if r.returncode:
            raise RuntimeError("Xray rejected new profile: "+r.stderr[-600:])
    existing=[p for p in existing if not p["remarks"].startswith(TITLE_PREFIX)]
    existing.insert(2,cfg)
    TARGET.write_text(json.dumps(existing,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    SINGLE.write_text(json.dumps([cfg],ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    REPORT.write_text(json.dumps({"exit_country":"RU","exit_ip":ip,
                                  "endpoint":picked["server"],"checked_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
                                  "ms_from_github_runner":picked["http_ms"],"profiles":len(existing)},
                                 ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("SUCCESS new RU exit IP",ip,"source",picked["server"],"total profiles",len(existing),flush=True)

if __name__=="__main__":
    run()
