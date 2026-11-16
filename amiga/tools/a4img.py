"""PCX and BMP readers for Timmy Time Adventure's data build (Python stdlib only).

From Liquid War 5's GFOS port (amiga/tools/lw5img.py).

Each reader gives (w, h, pixels, palette): pixels is a bytes of w*h palette
indexes, palette a list of 256 (r, g, b) in 0..255. A truecolor BMP gives
pixels None and rgb, a list of w*h (r, g, b).

Copyright (c) 2026 AmiCradle Team. GPL-3 or later, as Timmy Time Adventure.
"""
import struct


class Image:
    def __init__(self, w, h, pixels=None, palette=None, rgb=None):
        self.w, self.h = w, h
        self.pixels, self.palette, self.rgb = pixels, palette, rgb

    def rgb_at(self, i):
        if self.rgb is not None:
            return self.rgb[i]
        return self.palette[self.pixels[i]]


def read_pcx(data):
    (manuf, _ver, enc, bpp, x0, y0, x1, y1) = struct.unpack_from("<BBBBHHHH", data, 0)
    planes = data[65]
    bpl = struct.unpack_from("<H", data, 66)[0]
    if manuf != 10 or bpp != 8 or planes != 1:
        raise ValueError("only 8-bit one-plane PCX")
    w, h = x1 - x0 + 1, y1 - y0 + 1
    out = bytearray()
    pos = 128
    for _y in range(h):
        line = bytearray()
        while len(line) < bpl:
            c = data[pos]
            pos += 1
            if enc == 1 and (c & 0xC0) == 0xC0:
                n = c & 0x3F
                line += bytes([data[pos]]) * n
                pos += 1
            else:
                line.append(c)
        out += line[:w]
    pal = [(0, 0, 0)] * 256
    if len(data) >= 769 and data[-769] == 12:
        p = data[-768:]
        pal = [(p[i * 3], p[i * 3 + 1], p[i * 3 + 2]) for i in range(256)]
    return Image(w, h, bytes(out), pal)


def read_bmp(data):
    if data[:2] != b"BM":
        raise ValueError("not a BMP")
    off = struct.unpack_from("<I", data, 10)[0]
    hsz = struct.unpack_from("<I", data, 14)[0]
    w, h, _pl, bpp, comp = struct.unpack_from("<iiHHI", data, 18)
    ncol = struct.unpack_from("<I", data, 46)[0] if hsz >= 40 else 0
    flip = h > 0
    h = abs(h)
    pal = [(0, 0, 0)] * 256
    if bpp <= 8:
        n = ncol or (1 << bpp)
        p = 14 + hsz
        for i in range(n):
            b, g, r = data[p + i * 4], data[p + i * 4 + 1], data[p + i * 4 + 2]
            pal[i] = (r, g, b)
    rows = []
    if comp == 1 and bpp == 8:              # RLE8
        pos, row, rows_raw = off, bytearray(w), []
        x = 0
        while len(rows_raw) < h and pos < len(data):
            n, c = data[pos], data[pos + 1]
            pos += 2
            if n:
                for _ in range(n):
                    if x < w:
                        row[x] = c
                    x += 1
            elif c == 0:
                rows_raw.append(bytes(row)); row = bytearray(w); x = 0
            elif c == 1:
                break
            elif c == 2:
                dx, dy = data[pos], data[pos + 1]; pos += 2; x += dx
                for _ in range(dy):
                    rows_raw.append(bytes(row)); row = bytearray(w)
            else:
                for i in range(c):
                    if x < w:
                        row[x] = data[pos + i]
                    x += 1
                pos += c + (c & 1)
        if x or len(rows_raw) < h:
            rows_raw.append(bytes(row))
        while len(rows_raw) < h:
            rows_raw.append(bytes(w))
        rows = rows_raw[:h]
    elif comp == 0:
        stride = ((w * bpp + 31) // 32) * 4
        for y in range(h):
            r = data[off + y * stride: off + (y + 1) * stride]
            if bpp == 8:
                rows.append(bytes(r[:w]))
            elif bpp == 4:
                rows.append(bytes((r[x >> 1] >> (0 if x & 1 else 4)) & 15 for x in range(w)))
            elif bpp == 1:
                rows.append(bytes((r[x >> 3] >> (7 - (x & 7))) & 1 for x in range(w)))
            elif bpp in (24, 32):
                s = bpp // 8
                rows.append([(r[x * s + 2], r[x * s + 1], r[x * s]) for x in range(w)])
            else:
                raise ValueError("BMP depth %d" % bpp)
    else:
        raise ValueError("BMP compression %d" % comp)
    if flip:
        rows.reverse()
    if bpp in (24, 32):
        rgb = [p for r in rows for p in r]
        return Image(w, h, None, None, rgb)
    return Image(w, h, b"".join(rows), pal)


def read_image(path):
    with open(path, "rb") as f:
        data = f.read()
    if path.lower().endswith(".pcx"):
        return read_pcx(data)
    return read_bmp(data)
