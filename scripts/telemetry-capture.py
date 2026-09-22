#!/usr/bin/env python3
"""Show what arrives on the telemetry port and how Oversteer decodes it.

    scripts/telemetry-capture.py [port]

Quit Oversteer (or switch its rev lights off) first: only one listener can
own the port. Prints one line per distinct (source, size) and a decoded
sample every second.
"""
import os
import socket
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from oversteer.telemetry import decode  # noqa: E402

port = int(sys.argv[1]) if len(sys.argv) > 1 else 5300
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('0.0.0.0', port))
sock.settimeout(1.0)
print("listening on UDP %d (Ctrl-C to stop)" % port)
seen = set()
last_print = 0.0
count = 0
try:
    while True:
        try:
            data, addr = sock.recvfrom(4096)
        except socket.timeout:
            continue
        count += 1
        key = (addr[0], len(data))
        if key not in seen:
            seen.add(key)
            print("new source: %s, %d-byte packets, first bytes %s" % (addr[0], len(data), data[:8].hex()))
        now = time.time()
        if now - last_print >= 1.0:
            last_print = now
            print("  #%d %d bytes -> %s" % (count, len(data), decode(data)))
except KeyboardInterrupt:
    pass
