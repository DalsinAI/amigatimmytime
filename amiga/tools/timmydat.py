#!/usr/bin/env python3
"""Build Timmy Time Adventure's .dat files without its own `dat` tool.

Upstream's Makefile runs tools/dat/dat (a macOS or Windows binary):

  dat create OUT --bmp DIR/*.bmp --wav DIR/*.wav --midi DIR/*.mid
                 --pal-bmp DIR/*.pal --data DIR/*.txt --h src/data/X.h

That writes an Allegro 4 datafile with the objects in the order of the
options, each group in name order, and a header naming each object's
index (src/data/*.h, kept in git). This writes the same datafile with the
Python standard library, for gfopenallegro's load_datafile_object_indexed:

  BMP   8-bit bitmap        (*.bmp)
  SAMP  sample              (*.wav, PCM 8/16-bit)
  MIDI  MIDI file           (*.mid)
  PAL   the palette of a BMP (*.pal are 8-bit BMPs)
  DATA  the file as it is   (*.txt)

  timmydat.py OUT DIR [--h HEADER]
      --h checks the order against HEADER instead of writing one.
  timmydat.py --all RES_DIR SRC_DATA_DIR OUT_DIR
      every .dat the game loads, each checked against its header.

Copyright (c) 2026 AmiCradle Team. GPL-3 or later, as Timmy Time Adventure.
"""
import glob
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import a4img  # noqa: E402

# upstream Makefile: out name -> (res dir, header)
DATS = [
    ("game.dat", "game", "gdata.h"),
    ("player.dat", "player", "pdata.h"),
    ("collmap.dat", "collisions", "cdata.h"),
    ("objects.dat", "objects", "odata.h"),
    ("enemies.dat", "enemies", "edata.h"),
    ("jurassic.dat", "levels/jurassic", "judata.h"),
    ("west.dat", "levels/west", "wedata.h"),
    ("medieval.dat", "levels/medieval", "medata.h"),
    ("egypt.dat", "levels/egypt", "egydata.h"),
    ("tutorial.dat", "levels/tutorial", "tutdata.h"),
]
# option order of the dat command line: (glob, type, header comment)
GROUPS = [("*.bmp", "BMP ", "BMP"), ("*.wav", "SAMP", "SAMP"), ("*.mid", "MIDI", "MIDI"),
          ("*.pal", "PAL ", "PAL"), ("*.txt", "DATA", "DATA")]


def dat_id(s):
    return struct.unpack(">I", s.encode("ascii"))[0]


DAT_MAGIC = dat_id("ALL.")
F_NOPACK_MAGIC = 0x736C682E


def mw(v):
    return struct.pack(">H", v & 0xFFFF)


def ml(v):
    return struct.pack(">I", v & 0xFFFFFFFF)


def read_bytes(path):
    with open(path, "rb") as f:
        return f.read()


def obj_name(path):
    return re.sub(r"[^A-Za-z0-9]", "_", os.path.basename(path)).upper()


def bitmap_obj(path):
    im = a4img.read_image(path)
    if im.pixels is None:
        raise ValueError("%s: not an 8-bit BMP" % path)
    return mw(8) + mw(im.w) + mw(im.h) + bytes(im.pixels)


def palette_obj(path):
    im = a4img.read_image(path)
    if im.pixels is None:
        raise ValueError("%s: not an 8-bit BMP" % path)
    out = []
    for rgb in im.palette:
        out.append(bytes(((c >> 2) << 2) | ((c >> 2) >> 4) for c in rgb))
    return b"".join(out)


def sample_obj(path):
    data = read_bytes(path)
    if data[:4] != b"RIFF" or data[8:12] != b"WAVE":
        raise ValueError("%s: not a WAV" % path)
    pos, fmt = 12, None
    while pos + 8 <= len(data):
        cid, clen = data[pos:pos + 4], struct.unpack_from("<I", data, pos + 4)[0]
        body = data[pos + 8:pos + 8 + clen]
        if cid == b"fmt ":
            fmt = struct.unpack_from("<HHIIHH", body, 0)
        elif cid == b"data" and fmt:
            tag, ch, freq, _br, _ba, bits = fmt
            if tag != 1 or bits not in (8, 16) or ch not in (1, 2):
                raise ValueError("%s: PCM 8/16-bit only" % path)
            frames = len(body) // ((bits // 8) * ch)
            if bits == 8:
                pcm = body[:frames * ch]
            else:
                n = frames * ch
                vals = struct.unpack_from("<%dh" % n, body, 0)
                pcm = struct.pack("<%dH" % n, *[(v + 0x8000) & 0xFFFF for v in vals])
            return mw(-bits if ch == 2 else bits) + mw(freq) + ml(frames) + pcm
        pos += 8 + clen + (clen & 1)
    raise ValueError("%s: no PCM data" % path)


def midi_obj(path):
    data = read_bytes(path)
    if data[:4] != b"MThd":
        raise ValueError("%s: not MIDI" % path)
    hlen = struct.unpack_from(">I", data, 4)[0]
    _fmt, ntr, div = struct.unpack_from(">HHH", data, 8)
    pos, tracks = 8 + hlen, []
    while pos + 8 <= len(data) and len(tracks) < ntr:
        cid, clen = data[pos:pos + 4], struct.unpack_from(">I", data, pos + 4)[0]
        if cid == b"MTrk":
            tracks.append(data[pos + 8:pos + 8 + clen])
        pos += 8 + clen
    out = [mw(div)]
    for i in range(32):
        t = tracks[i] if i < len(tracks) else b""
        out += [ml(len(t)), t]
    return b"".join(out)


MAKERS = {"BMP ": bitmap_obj, "SAMP": sample_obj, "MIDI": midi_obj, "PAL ": palette_obj, "DATA": read_bytes}


def objects(res_dir):
    """[(name, type, comment, path)] in the dat tool's order."""
    objs = []
    for pat, typ, comment in GROUPS:
        for path in sorted(glob.glob(os.path.join(res_dir, pat)), key=lambda p: os.path.basename(p).lower()):
            objs.append((obj_name(path), typ, comment, path))
    return objs


def read_header(path):
    """[(name, index, comment)] from a dat tool header."""
    out = []
    with open(path, encoding="latin-1") as f:
        for line in f:
            m = re.match(r"\s*#define\s+(\w+)\s+(\d+)\s*(?://\s*(\w+))?", line)
            if m:
                out.append((m.group(1), int(m.group(2)), m.group(3) or ""))
    return out


def check_header(objs, header):
    want = read_header(header)
    got = [(n, i, c) for i, (n, _t, c, _p) in enumerate(objs)]
    if want != got:
        for a, b in zip(want + [None] * len(got), got + [None] * len(want)):
            if a != b:
                raise ValueError("%s: header has %s, data has %s" % (header, a, b))
    return len(got)


def build(res_dir):
    objs = objects(res_dir)
    out = [ml(DAT_MAGIC), ml(len(objs))]
    for name, typ, _c, path in objs:
        data = MAKERS[typ](path)
        nb = name.encode("ascii")
        out += [ml(dat_id("prop")), ml(dat_id("NAME")), ml(len(nb)), nb]
        out += [ml(dat_id(typ)), ml(len(data)), ml(len(data)), data]
    return objs, ml(F_NOPACK_MAGIC) + b"".join(out)


def write(out_path, res_dir, header=None):
    objs, body = build(res_dir)
    if header:
        check_header(objs, header)
    with open(out_path, "wb") as f:
        f.write(body)
    return len(objs), len(body)


def main(argv):
    if len(argv) >= 5 and argv[1] == "--all":
        res, hdrs, out = argv[2], argv[3], argv[4]
        os.makedirs(out, exist_ok=True)
        for name, sub, hdr in DATS:
            n, size = write(os.path.join(out, name), os.path.join(res, sub), os.path.join(hdrs, hdr))
            print("%s: %d objects, %d bytes" % (name, n, size))
        return 0
    if len(argv) >= 3:
        hdr = argv[argv.index("--h") + 1] if "--h" in argv else None
        n, size = write(argv[1], argv[2], hdr)
        print("%s: %d objects, %d bytes" % (argv[1], n, size))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
