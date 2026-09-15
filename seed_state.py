#!/usr/bin/env python3
"""Seed runner dedup state from the channel itself.

Extracts every config URI visible on t.me/s/VpnProxyCenter and marks
their keys as posted, so the failover run never reposts what's already
in the channel (even if the main server's state backup is stale).
Writes/updates state/posted_configs.json (same schema as main).
"""
import json
import os
import re
import sys
import datetime
import requests

PREVIEW = "https://t.me/s/VpnProxyCenter"
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
URI_RE = re.compile(r"(vless|vmess|ss|socks5?|http|trojan|hysteria2|wireguard)://\S+")


def main():
    state_path = sys.argv[1] if len(sys.argv) > 1 else "state/posted_configs.json"
    state = {"posted_configs": {}, "last_config_time": None, "last_config_type": None}
    if os.path.exists(state_path):
        try:
            state = json.load(open(state_path))
        except Exception:
            pass
    r = requests.get(PREVIEW, headers=HEADERS, timeout=25)
    r.raise_for_status()
    texts = re.findall(
        r'<div[^>]*class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>',
        r.text, re.S)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    n = 0
    for t in texts:
        t = re.sub(r"<br\s*/?>", "\n", t)
        t = re.sub(r"<[^>]+>", "", t)
        for m in URI_RE.finditer(t):
            cfg = m.group(0).rstrip("#").rstrip(")")
            key = cfg[:80]
            if key not in state["posted_configs"]:
                state["posted_configs"][key] = {"type": "seed", "time": now}
                n += 1
    # Keep file bounded: drop entries older than 7 days (keep seeds)
    week_ago = (datetime.datetime.now(datetime.timezone.utc)
                - datetime.timedelta(days=7)).isoformat()
    kept = {k: v for k, v in state["posted_configs"].items()
            if v.get("time", "") >= week_ago or v.get("type") == "seed"}
    state["posted_configs"] = kept
    os.makedirs(os.path.dirname(state_path) or ".", exist_ok=True)
    json.dump(state, open(state_path, "w"), indent=2)
    print(f"[SEED] {n} new keys from channel, {len(kept)} total")


if __name__ == "__main__":
    main()
