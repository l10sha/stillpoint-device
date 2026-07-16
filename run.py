#!/usr/bin/env python3
"""Boot the virtual StillPoint.

    python3 run.py [--time HH:MM] [--port 8777]
"""
import argparse
from datetime import datetime

from firmware import device, server
from firmware.simclock import SimClock


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--time", default=None, help="initial simulated time, HH:MM")
    ap.add_argument("--port", type=int, default=8777)
    args = ap.parse_args()

    start = None
    if args.time:
        h, m = map(int, args.time.split(":"))
        start = datetime.now().replace(hour=h, minute=m, second=0, microsecond=0)

    clock = SimClock(start=start)
    dev = device.start(server.broadcast, clock)
    server.run(dev, port=args.port)


if __name__ == "__main__":
    main()
