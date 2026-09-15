#!/usr/bin/env python3
"""Failover guard: exit 0 only if @VpnProxyCenter has been silent >3h.

Reads the public preview (same IDs as real messages). Any parse failure
-> exit 2 (skip: never risk duplicate posts on uncertainty).
"""
import re
import sys
import datetime
import requests

PREVIEW = "https://t.me/s/VpnProxyCenter"
SILENCE_AFTER = 3 * 3600
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}


def newest_post_time():
    r = requests.get(PREVIEW, headers=HEADERS, timeout=25)
    r.raise_for_status()
    times = re.findall(r'datetime="([^"]+)"', r.text)
    best = None
    for t in times:
        try:
            dt = datetime.datetime.fromisoformat(t)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=datetime.timezone.utc)
            if best is None or dt > best:
                best = dt
        except ValueError:
            continue
    return best


def main():
    try:
        best = newest_post_time()
    except Exception as e:
        print(f"[GUARD] scrape failed ({e}) -> SKIP")
        return 2
    if best is None:
        print("[GUARD] no timestamps found -> SKIP")
        return 2
    age = (datetime.datetime.now(datetime.timezone.utc) - best).total_seconds()
    print(f"[GUARD] newest post {best.isoformat()} ({int(age // 60)} min ago)")
    if age < SILENCE_AFTER:
        print("[GUARD] channel alive -> SKIP")
        return 2
    print("[GUARD] channel silent 3h+ -> PROCEED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
