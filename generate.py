#!/usr/bin/env python3
"""Fetch FCM hosts from fcm-hosts-next, merge with manually maintained direct IPs,
and generate a sing-box rule-set of all direct-connected IPs.

Result set = manually maintained IPs (direct_ip_manual.json) + FCM preferred IPs.

Produces:
  - direct_ip.json    : rule-set source (JSON), dual-stack ip_cidr
  - direct_ip.srs     : compiled binary (via `sing-box rule-set compile`)
  - direct_ip.version : metadata (source url, generated time, ip counts)
"""

import ipaddress
import json
import os
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone

SOURCE_URL = os.environ.get(
    "FCM_SOURCE_URL",
    "https://raw.githubusercontent.com/cagedbird043/fcm-hosts-next/main/fcm_dual.hosts",
)
SINGBOX_BIN = os.environ.get("SINGBOX_BIN", "sing-box")
MANUAL_JSON = "direct_ip_manual.json"
OUT_JSON = "direct_ip.json"
OUT_SRS = "direct_ip.srs"
OUT_VERSION = "direct_ip.version"


def fetch(url: str) -> str:
    print(f"[fetch] {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "direct-ip-srs/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8")


def parse_ips(text: str):
    """Parse individual IP addresses from the FCM hosts file."""
    ips = set()
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if not parts:
            continue
        candidate = parts[0]
        try:
            ip = ipaddress.ip_address(candidate)
        except ValueError:
            continue
        ips.add(str(ip))
    return sorted(ips)


def load_manual_ips(path: str):
    """Load manually maintained CIDR entries from a JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    cidrs = set()
    for entry in data.get("ip_cidr", []):
        try:
            net = ipaddress.ip_network(entry, strict=False)
        except ValueError:
            print(f"[warn] invalid CIDR in {path}: {entry}", file=sys.stderr)
            continue
        cidrs.add(str(net))
    return sorted(cidrs)


def build_rule_set(cidrs):
    return {
        "version": 1,
        "rules": [
            {
                "ip_cidr": cidrs,
            }
        ],
    }


def compile_srs(json_path: str) -> bool:
    print(f"[compile] {SINGBOX_BIN} rule-set compile {json_path} -o {OUT_SRS}")
    result = subprocess.run(
        [SINGBOX_BIN, "rule-set", "compile", json_path, "-o", OUT_SRS],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"[warn] sing-box compile failed: {result.stderr}", file=sys.stderr)
        return False
    return True


def json_dumps(rule_set: dict) -> str:
    return json.dumps(rule_set, ensure_ascii=False, indent=2) + "\n"


def main() -> int:
    manual = load_manual_ips(MANUAL_JSON)

    text = fetch(SOURCE_URL)
    fcm = parse_ips(text)

    cidrs = sorted(set(manual) | set(fcm))
    if not cidrs:
        print("[error] no IPs parsed; aborting", file=sys.stderr)
        return 1

    rule_set = build_rule_set(cidrs)
    content = json_dumps(rule_set)

    # Skip if unchanged: compare with the JSON currently committed.
    if os.path.exists(OUT_JSON):
        try:
            with open(OUT_JSON, "r", encoding="utf-8") as f:
                if f.read() == content:
                    print("[skip] rule-set unchanged, no update needed")
                    return 2
        except OSError:
            pass

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[json] wrote {len(cidrs)} entries (manual {len(manual)}, FCM {len(fcm)}) -> {OUT_JSON}")

    compiled = compile_srs(OUT_JSON)
    if not compiled and not os.path.exists(OUT_SRS):
        print("[warn] .srs not produced; repo will still have .json", file=sys.stderr)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(OUT_VERSION, "w", encoding="utf-8") as f:
        f.write(f"source={SOURCE_URL}\n")
        f.write(f"generated_at={now}\n")
        f.write(f"manual={len(manual)}\n")
        f.write(f"fcm={len(fcm)}\n")
        f.write(f"total={len(cidrs)}\n")
        f.write(f"compiled={'yes' if compiled else 'no'}\n")
    print(f"[version] wrote {OUT_VERSION}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
