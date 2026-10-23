# XetsiwVPN — Spacetime diagnostics

GitHub Actions checks network reachability and **actually starts Xray** with the existing separate Spacetime VLESS profile. The main VPN subscription is never overwritten.

## Checks
- TCP reachability of known candidates (TCP open does not imply VPN access)
- Runs Xray using `vpn/XetsiwVPN_Spacetime_NEW_IP.json`, validates the config and sends two HTTPS requests through local SOCKS5
- Confirms public tunnel exit IP, US exit country, and that the exit differs from the GitHub runner IP and existing subscription endpoints
- Saves machine-readable `spacetime-xray-tunnel-report` artifact
- Optional direct HTTPS probe of a specified Spacetime hostname (from GitHub runner, not the tunnel)

## Limitations
A successful tunnel check **does not** demonstrate that the Spacetime game/service accepts that IP. Its actual host, login and application-level block response have not been tested. A reachable TCP port alone is never sufficient.

## How to run
GitHub → Actions → Spacetime connectivity check → Run workflow, or submit a PR modifying `spacetime-check/**`.

Known candidates are listed in `candidates.csv`. Do not put credentials or private subscription tokens in that file.
