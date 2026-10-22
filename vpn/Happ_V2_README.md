# Happ VPN 2.0 — one free subscription

Subscription URL:

`https://raw.githubusercontent.com/EvilMastermod/-/main/vpn/Happ_US_RU_Auto.json`

Happ → Add subscription → paste this link → Update.

## Which profile to use?

- **🇺🇸 США — АВТОВЫБОР — СТАБИЛЬНЫЙ**: USA exit for everyday browsing.
- **🇷🇺 РОССИЯ — АВТОВЫБОР — СТАБИЛЬНЫЙ**: Russian exit for everyday browsing.
- **🇩🇪 Germany, 🇳🇱 Netherlands, 🇫🇮 Finland**: region-specific automatic groups when live verification yields available nodes.
- **🎮 Gaming profiles**: smaller pools of low-HTTP-RTT nodes for comparison; test game ping locally.
- **СЕРВЕР N**: select a specific endpoint in Happ; useful if automatic selection is slow from your own network.

## How auto-selection works

Xray `leastPing` uses periodically measured HTTP latency and excludes nodes reported unavailable. Its `fallbackTag` is a backup target, but cannot guarantee an active connection survives a switch.

The GitHub Actions updater periodically samples multiple public providers and uses Xray+HTTP to verify *exit country*, availability, and two-sample HTTP response delay. It rejects incompatible REALITY/WebSocket configurations before publishing. The workflow validates every generated Xray config, and posts aggregate per-country counts to `vpn/FAST_NODES_RESULTS.json`.

**Important:** Github server latency is *not your ping*, and is not the ping to an individual game server. Happ tests should be used from your device.

**Free public nodes can fail, disappear, change country or be malicious.** Do not use them for banking, private credentials, or sensitive accounts. There are no owned private VPS endpoints in this project.

This project does not bypass paid providers or make expired VLESS accounts valid. It gathers public third-party nodes.
