#!/usr/bin/env python3
"""Fetch FCM hosts from fcm-hosts-next and generate sing-box rule-set.

Produces:
  - fcm_dual.srs.json   : rule-set source (JSON), dual-stack ip_cidr
  - fcm_dual.srs        : compiled binary (via `sing-box rule-set compile`)
  - fcm_dual.version    : metadata (source url, generated time, ip count)
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
OUT_JSON = "fcm_dual.srs.json"
OUT_SRS = "fcm_dual.srs"
OUT_VERSION = "fcm_dual.version"


def fetch(url: str) -> str:
    print(f"[fetch] {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "fcm-srs-generator/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8")


def parse_ips(text: str):
    v4, v6 = set(), set()
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
        if ip.version == 4:
            v4.add(str(ip))
        elif ip.version == 6:
            v6.add(str(ip))
    return sorted(v4), sorted(v6)


def build_rule_set(v4, v6):
    return {
        "version": 1,
        "rules": [
            {
                "ip_cidr": v4 + v6,
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


def main() -> int:
    text = fetch(SOURCE_URL)
    v4, v6 = parse_ips(text)
    if not v4 and not v6:
        print("[error] no IPs parsed; aborting", file=sys.stderr)
        return 1

    rule_set = build_rule_set(v4, v6)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(rule_set, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"[json] wrote {len(v4)} IPv4 + {len(v6)} IPv6 -> {OUT_JSON}")

    compiled = compile_srs(OUT_JSON)
    if not compiled and not os.path.exists(OUT_SRS):
        print("[warn] .srs not produced; repo will still have .json", file=sys.stderr)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(OUT_VERSION, "w", encoding="utf-8") as f:
        f.write(f"source={SOURCE_URL}\n")
        f.write(f"generated_at={now}\n")
        f.write(f"ipv4={len(v4)}\n")
        f.write(f"ipv6={len(v6)}\n")
        f.write(f"compiled={'yes' if compiled else 'no'}\n")
    print(f"[version] wrote {OUT_VERSION}")

    return 0


if __name__ == "__main__":
    sys.exit(main())