"""Small deterministic PNGs for technical tests; never exercise illustrations."""

import struct
import zlib


def png_bytes(red=80):
    def chunk(kind, payload):
        return (struct.pack("!I", len(payload)) + kind + payload
                + struct.pack("!I", zlib.crc32(kind + payload) & 0xffffffff))
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack("!IIBBBBB", 2, 2, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress((b"\0" + bytes((red, 100, 120)) * 2) * 2))
            + chunk(b"IEND", b""))
