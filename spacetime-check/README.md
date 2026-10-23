# XetsiwVPN — Spacetime diagnostics

Independent diagnostics; does not modify existing VPN profiles.

## What it checks
- TCP reachability of listed candidate endpoints
- HTTPS availability of a *specified* Spacetime domain from a GitHub-hosted runner
- Runner public egress IP and response statuses

**Important:** a reachable TCP socket does not mean the endpoint is a working VPN, that its *VPN exit IP* differs from older profiles, or that Spacetime accepts it. GitHub Actions uses a separate network from an actual VPN connection.

## Running
Open **Actions → Spacetime connectivity check → Run workflow**, enter the actual Spacetime hostname (without https://) and run. Find the downloadable diagnostic report in the run's Artifacts section.

Candidates are listed in `candidates.csv`. Do not put access keys, authentication URLs, or VPN subscription tokens in that file.
