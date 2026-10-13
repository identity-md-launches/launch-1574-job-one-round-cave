#!/usr/bin/env python3
"""Encode the required 512px JPEG from the wall, using only the standard library.

Supports non-interlaced 8-bit RGB/RGBA PNG, baseline three-component JPEG.
This is an artifact-production helper, not part of contract-call rehearsal.
"""
import math
import argparse
from pathlib import Path
import struct
import zlib

ZIGZAG = [0,1,8,16,9,2,3,10,17,24,32,25,18,11,4,5,12,19,26,33,40,48,41,34,
          27,20,13,6,7,14,21,28,35,42,49,56,57,50,43,36,29,22,15,23,30,37,44,
          51,58,59,52,45,38,31,39,46,53,60,61,54,47,55,62,63]
Q = [16,11,10,16,24,40,51,61,12,12,14,19,26,58,60,55,
     14,13,16,24,40,57,69,56,14,17,22,29,51,87,80,62,
     18,22,37,56,68,109,103,77,24,35,55,64,81,104,113,92,
     49,64,78,87,103,121,120,101,72,92,95,98,112,100,103,99]
DC_BITS = [0,1,5,1,1,1,1,1,1,0,0,0,0,0,0,0]
DC_VALS = list(range(12))
AC_BITS = [0,2,1,3,3,2,4,3,5,5,4,4,0,0,1,125]
AC_VALS = bytes.fromhex('''
01 02 03 00 04 11 05 12 21 31 41 06 13 51 61 07 22 71
14 32 81 91 a1 08 23 42 b1 c1 15 52 d1 f0 24 33 62 72
82 09 0a 16 17 18 19 1a 25 26 27 28 29 2a 34 35 36 37
38 39 3a 43 44 45 46 47 48 49 4a 53 54 55 56 57 58 59
5a 63 64 65 66 67 68 69 6a 73 74 75 76 77 78 79 7a 83
84 85 86 87 88 89 8a 92 93 94 95 96 97 98 99 9a a2 a3
a4 a5 a6 a7 a8 a9 aa b2 b3 b4 b5 b6 b7 b8 b9 ba c2 c3
c4 c5 c6 c7 c8 c9 ca d2 d3 d4 d5 d6 d7 d8 d9 da e1 e2
e3 e4 e5 e6 e7 e8 e9 ea f1 f2 f3 f4 f5 f6 f7 f8 f9 fa
''')


def png_rgb(path):
    content = path.read_bytes()
    assert content[:8] == b'\x89PNG\r\n\x1a\n'
    pos, compressed = 8, bytearray()
    while pos < len(content):
        length = int.from_bytes(content[pos:pos+4], 'big')
        kind = content[pos+4:pos+8]
        payload = content[pos+8:pos+8+length]
        assert zlib.crc32(kind + payload) == int.from_bytes(content[pos+8+length:pos+12+length], 'big')
        if kind == b'IHDR':
            width, height, depth, color, comp, filt, interlace = struct.unpack('>IIBBBBB', payload)
            assert depth == 8 and color in (2, 6) and comp == filt == interlace == 0
        elif kind == b'IDAT':
            compressed.extend(payload)
        elif kind == b'IEND':
            break
        pos += length + 12
    channels = 3 if color == 2 else 4
    stride = width * channels
    raw = zlib.decompress(compressed)
    assert len(raw) == (stride + 1) * height
    previous, rows = bytearray(stride), []
    for y in range(height):
        offset = y * (stride + 1)
        mode, row = raw[offset], bytearray(raw[offset+1:offset+1+stride])
        assert mode in range(5)
        for x in range(stride):
            a, b = row[x-channels] if x >= channels else 0, previous[x]
            c = previous[x-channels] if x >= channels else 0
            if mode == 1:
                predictor = a
            elif mode == 2:
                predictor = b
            elif mode == 3:
                predictor = (a + b) // 2
            elif mode == 4:
                p = a + b - c
                distances = (abs(p-a), abs(p-b), abs(p-c))
                predictor = (a, b, c)[distances.index(min(distances))]
            else:
                predictor = 0
            row[x] = (row[x] + predictor) & 255
        if channels == 4:
            assert all(row[x] == 255 for x in range(3, stride, 4)), 'transparent source not supported'
            rows.append(bytes(v for x, v in enumerate(row) if x % 4 != 3))
        else:
            rows.append(bytes(row))
        previous = row
    return width, height, rows


def resize(width, height, rows, size):
    # Area average each source pixel footprint; no new shapes or painting edits.
    output = []
    for y in range(size):
        row = []
        y0, y1 = y * height // size, (y+1) * height // size
        for x in range(size):
            x0, x1 = x * width // size, (x+1) * width // size
            n = (y1-y0) * (x1-x0)
            row.append(tuple(sum(rows[sy][3*sx+c] for sy in range(y0, y1)
                                 for sx in range(x0, x1)) / n for c in range(3)))
        output.append(row)
    return output


def huffman(counts, values):
    table, code, index = {}, 0, 0
    for bits, count in enumerate(counts, 1):
        for _ in range(count):
            table[values[index]] = (code, bits)
            index, code = index+1, code+1
        code <<= 1
    assert index == len(values)
    return table


def jpeg(pixels):
    size = len(pixels)
    assert size % 8 == 0
    output = bytearray(b'\xff\xd8')

    def segment(marker, payload):
        output.extend(bytes([255, marker]) + struct.pack('>H', len(payload)+2) + payload)

    segment(0xe0, b'JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00')
    segment(0xdb, bytes([0] + [Q[i] for i in ZIGZAG]))
    segment(0xc0, struct.pack('>BHHB', 8, size, size, 3) + bytes([1,0x11,0,2,0x11,0,3,0x11,0]))
    segment(0xc4, bytes([0] + DC_BITS + DC_VALS))
    segment(0xc4, bytes([0x10] + AC_BITS) + AC_VALS)
    segment(0xda, bytes([3,1,0,2,0,3,0,0,63,0]))
    dc, ac = huffman(DC_BITS, DC_VALS), huffman(AC_BITS, AC_VALS)
    buffer, filled = 0, 0

    def write(value, bits):
        nonlocal buffer, filled
        buffer = (buffer << bits) | value
        filled += bits
        while filled >= 8:
            filled -= 8
            byte = (buffer >> filled) & 255
            output.append(byte)
            if byte == 255:
                output.append(0)
        buffer &= (1 << filled) - 1

    def coefficient(value):
        bits = abs(value).bit_length()
        return bits, value if value >= 0 else value + (1 << bits) - 1

    basis = [[0.5 * (1/math.sqrt(2) if u == 0 else 1)
              * math.cos((2*x+1)*u*math.pi/16) for x in range(8)] for u in range(8)]
    previous = [0, 0, 0]
    for by in range(0, size, 8):
        for bx in range(0, size, 8):
            planes = [[], [], []]
            for y in range(by, by+8):
                for x in range(bx, bx+8):
                    red, green, blue = pixels[y][x]
                    planes[0].append(0.299*red + 0.587*green + 0.114*blue - 128)
                    planes[1].append(-0.168736*red - 0.331264*green + 0.5*blue)
                    planes[2].append(0.5*red - 0.418688*green - 0.081312*blue)
            for channel, plane in enumerate(planes):
                horizontal = [[sum(plane[y*8+x]*basis[u][x] for x in range(8))
                               for u in range(8)] for y in range(8)]
                quantized = [round(sum(horizontal[y][u]*basis[v][y] for y in range(8))/Q[v*8+u])
                             for v in range(8) for u in range(8)]
                values = [quantized[i] for i in ZIGZAG]
                bits, value = coefficient(values[0] - previous[channel])
                previous[channel] = values[0]
                write(*dc[bits])
                write(value, bits)
                zeros = 0
                for value in values[1:]:
                    if value == 0:
                        zeros += 1
                        continue
                    while zeros >= 16:
                        write(*ac[0xf0])
                        zeros -= 16
                    bits, encoded = coefficient(value)
                    write(*ac[(zeros << 4) | bits])
                    write(encoded, bits)
                    zeros = 0
                if zeros:
                    write(*ac[0])
    if filled:
        write((1 << (8-filled))-1, 8-filled)
    output.extend(b'\xff\xd9')
    return bytes(output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', help='workspace RGB/RGBA PNG, at least 512px square')
    parser.add_argument('target', help='new workspace 512px JPEG; overwrite refused')
    args = parser.parse_args()
    source = Path(args.source).resolve()
    target = Path(args.target).resolve()
    assert source.is_relative_to(Path.cwd().resolve()) and target.is_relative_to(Path.cwd().resolve())
    width, height, rows = png_rgb(source)
    assert width == height and width >= 512
    encoded = jpeg(resize(width, height, rows, 512))
    assert len(encoded) < 100_000
    with target.open('xb') as handle:
        handle.write(encoded)
    print(f'{target.relative_to(Path.cwd())}: JPEG, 512 x 512, {len(encoded)} bytes')
