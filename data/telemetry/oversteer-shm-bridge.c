/* oversteer-shm-bridge: forward a game's Windows shared-memory telemetry
 * to Oversteer's rev lights over UDP.
 *
 * Games built on the Assetto Corsa family (Assetto Corsa, Assetto Corsa
 * Competizione, Assetto Corsa Rally) publish telemetry only through named
 * shared memory (Local\acpmf_physics, Local\acpmf_static). Under Proton
 * that lives inside the game's Wine prefix, so this small Windows program
 * runs there alongside the game (see oversteer-run) and sends what the rev
 * lights need to Oversteer on the host as a 24-byte "OVST" datagram.
 *
 * All three games share the same prefix of the physics and static structs
 * (packetId, gas, brake, fuel, gear, rpms / ... sectorCount, maxTorque,
 * maxPower, maxRpm), which is all that is read here.
 *
 * Built for the Windows (GUI) subsystem so no console window appears when it
 * runs next to the game; all output goes to the --log file.
 * Build (any mingw): x86_64-w64-mingw32-gcc -O2 -s -mwindows -o oversteer-shm-bridge.exe oversteer-shm-bridge.c -lws2_32
 *   or: zig cc -target x86_64-windows-gnu -O2 -s -Wl,--subsystem,windows -o oversteer-shm-bridge.exe oversteer-shm-bridge.c -lws2_32
 *
 * Usage: oversteer-shm-bridge.exe [--host 127.0.0.1] [--port 5300] [--rate 60] [--verbose] [--exit-when-gone] [--log FILE]
 *   --log FILE: also append messages to FILE (Proton doesn't pass a console
 *   program's stderr through, so this is how oversteer-run keeps a log).
 *   --exit-when-gone: once telemetry has been seen, exit when it is gone
 *   for a few seconds (the game has quit) instead of waiting for the next one.
 *
 * This file is part of Oversteer (GPL-3.0-or-later).
 */
#include <winsock2.h>
#include <windows.h>
#include <tlhelp32.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdarg.h>


/* Offsets into the shared structs (4-byte packing, identical in AC/ACC/ACR) */
#define PHYS_PACKET_ID   0     /* int */
#define PHYS_GEAR        16    /* int, 0 = reverse, 1 = neutral, 2 = first ... */
#define PHYS_RPMS        20    /* int */
#define PHYS_SPEED_KMH   28    /* float */
#define PHYS_VIEW_SIZE   64
#define STATIC_MAX_RPM   412   /* int; after smVersion/acVersion (2x15 wchar), 2 ints,
                                  5x33 wchar strings, sectorCount, maxTorque, maxPower */
#define STATIC_VIEW_SIZE 416

#define OVST_VERSION 1
#define OVST_SOURCE_ACPMF 1

#pragma pack(push, 1)
struct ovst_packet {
    char magic[4];       /* "OVST" */
    uint8_t version;
    uint8_t source;
    uint16_t flags;      /* bit 0: shift light */
    float rpm;
    float max_rpm;       /* 0 when unknown */
    int32_t gear;        /* -1 reverse, 0 neutral, 1.. */
    float speed_kmh;
};
#pragma pack(pop)

static int verbose = 0;
static int exit_when_gone = 0;
static FILE *logfile = NULL;

static void logmsg(const char *fmt, ...)
{
    va_list ap;
    va_start(ap, fmt);
    fprintf(stderr, "oversteer-shm-bridge: ");
    vfprintf(stderr, fmt, ap);
    fprintf(stderr, "\n");
    va_end(ap);
    if (logfile) {
        va_start(ap, fmt);
        fprintf(logfile, "[%lu] ", (unsigned long)GetTickCount() / 1000);
        vfprintf(logfile, fmt, ap);
        fprintf(logfile, "\n");
        fflush(logfile);
        va_end(ap);
    }
}

/* The games create the mappings in the session-local namespace; try the
 * spellings that resolve to it, and the global one, so an unusual
 * launcher setup still works. */
static const char *physics_names[] = { "Local\\acpmf_physics", "acpmf_physics", "Global\\acpmf_physics", NULL };
static const char *static_names[] = { "Local\\acpmf_static", "acpmf_static", "Global\\acpmf_static", NULL };

static const void *open_any(const char **names, HANDLE *handle, size_t size, const char **used);

/* Is a process with this image name (case-insensitive) running? */
static int process_running(const char *image)
{
    HANDLE snap = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    PROCESSENTRY32 pe;
    int found = 0;

    if (snap == INVALID_HANDLE_VALUE)
        return 1;   /* can't tell: assume yes */
    pe.dwSize = sizeof(pe);
    if (Process32First(snap, &pe)) {
        do {
            if (!_stricmp(pe.szExeFile, image)) {
                found = 1;
                break;
            }
        } while (Process32Next(snap, &pe));
    }
    CloseHandle(snap);
    return found;
}

static const void *open_view(const char *name, HANDLE *handle, size_t size)
{
    const void *view;

    *handle = OpenFileMappingA(FILE_MAP_READ, FALSE, name);
    if (*handle == NULL)
        return NULL;
    view = MapViewOfFile(*handle, FILE_MAP_READ, 0, 0, size);
    if (view == NULL) {
        CloseHandle(*handle);
        *handle = NULL;
    }
    return view;
}

static const void *open_any(const char **names, HANDLE *handle, size_t size, const char **used)
{
    const void *view = NULL;
    int i;

    for (i = 0; names[i] && view == NULL; i++) {
        view = open_view(names[i], handle, size);
        if (view && used)
            *used = names[i];
    }
    return view;
}

static void close_view(const void *view, HANDLE *handle)
{
    if (view)
        UnmapViewOfFile(view);
    if (*handle) {
        CloseHandle(*handle);
        *handle = NULL;
    }
}

static int32_t rd_i32(const void *base, size_t off)
{
    int32_t v;
    memcpy(&v, (const char *)base + off, sizeof(v));
    return v;
}

static float rd_f32(const void *base, size_t off)
{
    float v;
    memcpy(&v, (const char *)base + off, sizeof(v));
    return v;
}

int main(int argc, char **argv)
{
    const char *host = "127.0.0.1";
    const char *watch = NULL;
    int port = 5300, rate = 60;
    WSADATA wsa;
    SOCKET sock;
    struct sockaddr_in dest;
    HANDLE hphys = NULL, hstat = NULL;
    const void *phys = NULL, *stat = NULL;
    int32_t last_packet = -1;
    DWORD last_change = 0, last_report = 0, last_watch = 0;
    unsigned long sent = 0;
    const char *name_used = "?";
    int seen = 0, announced = 0, i;

    for (i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "--host") && i + 1 < argc)
            host = argv[++i];
        else if (!strcmp(argv[i], "--port") && i + 1 < argc)
            port = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--rate") && i + 1 < argc)
            rate = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--verbose"))
            verbose = 1;
        else if (!strcmp(argv[i], "--exit-when-gone"))
            exit_when_gone = 1;
        else if (!strcmp(argv[i], "--watch") && i + 1 < argc)
            watch = argv[++i];
        else if (!strcmp(argv[i], "--log") && i + 1 < argc)
            logfile = fopen(argv[++i], "a");
        else {
            fprintf(stderr, "usage: %s [--host H] [--port N] [--rate HZ] [--exit-when-gone] [--watch GAME.exe] [--log FILE] [--verbose]\n", argv[0]);
            return 2;
        }
    }
    if (port <= 0 || port > 65535 || rate <= 0 || rate > 1000) {
        logmsg("bad port or rate");
        return 2;
    }

    if (WSAStartup(MAKEWORD(2, 2), &wsa) != 0) {
        logmsg("WSAStartup failed");
        return 1;
    }
    sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock == INVALID_SOCKET) {
        logmsg("socket failed: %d", WSAGetLastError());
        return 1;
    }
    memset(&dest, 0, sizeof(dest));
    dest.sin_family = AF_INET;
    dest.sin_port = htons((unsigned short)port);
    dest.sin_addr.s_addr = inet_addr(host);
    if (dest.sin_addr.s_addr == INADDR_NONE) {
        logmsg("bad host %s", host);
        return 2;
    }
    logmsg("sending to %s:%d at %d Hz; waiting for %s%s%s", host, port, rate, physics_names[0],
           watch ? ", watching " : "", watch ? watch : "");

    for (;;) {
        struct ovst_packet pkt;
        int32_t packet_id;
        DWORD now = GetTickCount();

        if (watch && now - last_watch > 3000) {
            last_watch = now;
            if (!process_running(watch)) {
                logmsg("%s is not running, exiting", watch);
                return 0;
            }
        }

        if (phys == NULL) {
            phys = open_any(physics_names, &hphys, PHYS_VIEW_SIZE, &name_used);
            if (phys == NULL) {
                if (seen && exit_when_gone) {
                    logmsg("telemetry gone, exiting");
                    return 0;
                }
                announced = 0;
                Sleep(1000);
                continue;
            }
            stat = open_any(static_names, &hstat, STATIC_VIEW_SIZE, NULL);
            /* Don't re-send the packet that was there before: a paused
             * game keeps the same id until it resumes. */
            last_packet = rd_i32(phys, PHYS_PACKET_ID);
            last_change = now;
            seen = 1;
            if (!announced) {
                announced = 1;
                logmsg("telemetry found as %s (static %s, maxRpm %d, packetId %d, rpms %d)", name_used,
                       stat ? "yes" : "no", stat ? rd_i32(stat, STATIC_MAX_RPM) : 0,
                       last_packet, rd_i32(phys, PHYS_RPMS));
            }
        }

        packet_id = rd_i32(phys, PHYS_PACKET_ID);
        if (packet_id != last_packet) {
            last_packet = packet_id;
            last_change = now;
            memset(&pkt, 0, sizeof(pkt));
            memcpy(pkt.magic, "OVST", 4);
            pkt.version = OVST_VERSION;
            pkt.source = OVST_SOURCE_ACPMF;
            pkt.rpm = (float)rd_i32(phys, PHYS_RPMS);
            pkt.max_rpm = stat ? (float)rd_i32(stat, STATIC_MAX_RPM) : 0.0f;
            pkt.gear = rd_i32(phys, PHYS_GEAR) - 1;
            pkt.speed_kmh = rd_f32(phys, PHYS_SPEED_KMH);
            if (sendto(sock, (const char *)&pkt, sizeof(pkt), 0, (struct sockaddr *)&dest, sizeof(dest)) == SOCKET_ERROR) {
                if (verbose)
                    logmsg("sendto failed: %d", WSAGetLastError());
            } else {
                sent++;
                if (verbose)
                    logmsg("rpm %.0f / %.0f gear %d", pkt.rpm, pkt.max_rpm, pkt.gear);
            }
        } else if (now - last_change > 2000) {
            /* Nothing written for two seconds: paused, in a menu, or quit.
             * Drop the views so we don't keep a quit game's section (and
             * its wineserver) alive; they are re-opened every second while
             * the mapping exists. */
            if (verbose)
                logmsg("telemetry stalled, releasing the mapping");
            close_view(phys, &hphys);
            close_view(stat, &hstat);
            phys = stat = NULL;
            Sleep(1000);
            continue;
        }
        if (now - last_report > 10000) {
            last_report = now;
            logmsg("packetId %d, rpm %d, %lu datagrams sent", packet_id, rd_i32(phys, PHYS_RPMS), sent);
        }
        Sleep(1000 / rate);
    }
}
