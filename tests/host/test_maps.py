#!/usr/bin/env python3
"""Timmy Time Adventure for GFOS: tools/tmx2bin.py --big-endian writes the
same maps as the DOS (little-endian) build, field for field, in the order
src/map.c reads them.
Copyright (c) 2026 AmiCradle Team. GPL-3 or later, as Timmy Time Adventure."""
import glob
import os
import struct
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def read_map(data, bo):
    """Every field of a .bin, as src/map.c's map_load reads them."""
    pos = 0

    def get(fmt):
        nonlocal pos
        v = struct.unpack_from(bo + fmt, data, pos)
        pos += struct.calcsize(bo + fmt)
        return v

    hdr = get("10H")
    tw, th, mw, mh, _bg, _time, _count, _cols, nprop, nanim = hdr
    out = [hdr, get("%dB" % (mw * mh))]
    out += [get("BH") for _ in range(nprop)]
    for _ in range(nanim):
        tid, nf = get("BB")
        out += [(tid, nf)] + [get("BH") for _ in range(nf)]
    (nent,) = get("H")
    out += [nent] + [get("BBHHBH") for _ in range(nent)]
    assert pos == len(data), "%d bytes left" % (len(data) - pos)
    assert tw == th and mw > 0 and mh > 0
    return out


def main():
    fails = 0
    tmxs = sorted(glob.glob(os.path.join(ROOT, "res/maps/*.tmx")))
    assert len(tmxs) == 5, tmxs
    with tempfile.TemporaryDirectory() as tmp:
        for tmx in tmxs:
            name = os.path.basename(tmx)
            le, be = os.path.join(tmp, "le.bin"), os.path.join(tmp, "be.bin")
            subprocess.run([sys.executable, os.path.join(ROOT, "tools/tmx2bin.py"), tmx, le], check=True, capture_output=True)
            subprocess.run([sys.executable, os.path.join(ROOT, "tools/tmx2bin.py"), "--big-endian", tmx, be], check=True, capture_output=True)
            a, b = open(le, "rb").read(), open(be, "rb").read()
            try:
                ok = read_map(a, "<") == read_map(b, ">") and a != b
            except Exception as e:  # noqa: BLE001
                ok = False
                print("%s: %s" % (name, e))
            print("%s: %s" % (name, "ok" if ok else "FAIL"))
            fails += not ok
    print("test_maps: PASS" if not fails else "test_maps: %d FAILED" % fails)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
