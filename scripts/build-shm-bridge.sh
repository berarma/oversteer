#!/bin/sh
# Rebuild data/telemetry/oversteer-shm-bridge.exe from its C source with
# whichever Windows cross-compiler is available (mingw-w64 or zig).
set -e
cd "$(dirname "$0")/../data/telemetry"
if command -v x86_64-w64-mingw32-gcc >/dev/null; then
    x86_64-w64-mingw32-gcc -O2 -s -Wall -mwindows -o oversteer-shm-bridge.exe oversteer-shm-bridge.c -lws2_32
elif command -v zig >/dev/null; then
    zig cc -target x86_64-windows-gnu -O2 -s -Wall -Wl,--subsystem,windows -o oversteer-shm-bridge.exe oversteer-shm-bridge.c -lws2_32
elif python3 -c 'import ziglang' 2>/dev/null; then
    python3 -m ziglang cc -target x86_64-windows-gnu -O2 -s -Wall -Wl,--subsystem,windows -o oversteer-shm-bridge.exe oversteer-shm-bridge.c -lws2_32
else
    echo "need x86_64-w64-mingw32-gcc, zig, or 'pip install ziglang'" >&2
    exit 1
fi
ls -la oversteer-shm-bridge.exe
