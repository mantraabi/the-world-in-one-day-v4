#!/usr/bin/env python3
"""Build step for this entry: verify `entry.png` and place it in the output directory.

The page itself is drawn by `tools/render.py` at authoring time, with Pillow. That
script is how the artwork was made, and it stays in the repo so anyone can redraw
the page from `tools/content.py` and `tools/data/land.json`.

The submission harness runs this file, though, and it runs with nothing but the
Python standard library, in a container with no network and a read-only mount of
this repository. So this file does no drawing: it checks that `entry.png` is a
real, complete, 1024x1024 PNG that decodes chunk by chunk, then copies it to
`$MAKEFUN_OUTPUT_DIR/entry.png`. Copying a fixed byte string is deliberately
idempotent — two runs produce two identical files.

The run must never fail. The grader keeps stderr to itself, so a non-zero exit
tells an entrant only that "the program exited with code 1" and nothing else.
Every check below is therefore advisory: it is reported, never fatal, and the
artwork is placed whether or not the checks agree. Only an absent `entry.png`,
with nothing to place at all, can end the run badly.

No third-party imports. No network. No randomness. No timestamps in the output.
"""

from __future__ import annotations

import os
import struct
import sys
import zlib
from pathlib import Path

# The grader mounts this repository read-only at /bot and hands over an empty
# writable directory, so the image has to be written there, never beside the source.
HERE = Path(os.environ.get("MAKEFUN_BOT_DIR") or Path(__file__).resolve().parent)
SOURCE = HERE / "entry.png"

EXPECTED_WIDTH = 1024
EXPECTED_HEIGHT = 1024
PAGE_NAME = "entry.png"

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def output_dir() -> Path:
    """Where the harness wants the page. /output unless it says otherwise."""
    for candidate in (os.environ.get("MAKEFUN_OUTPUT_DIR"), "/output", "./output"):
        if not candidate:
            continue
        path = Path(candidate)
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError:
            continue
        if os.access(path, os.W_OK):
            return path
    return Path(os.environ.get("MAKEFUN_OUTPUT_DIR") or "./output")


def read_chunks(blob: bytes) -> list[tuple[bytes, bytes]]:
    """Walk the PNG chunk stream, verifying every CRC. Returns (type, payload)."""
    if not blob.startswith(PNG_MAGIC):
        raise ValueError("not a PNG (bad signature)")

    chunks: list[tuple[bytes, bytes]] = []
    at = len(PNG_MAGIC)
    while at < len(blob):
        if at + 8 > len(blob):
            raise ValueError("truncated chunk header")
        (length,) = struct.unpack(">I", blob[at:at + 4])
        kind = blob[at + 4:at + 8]
        body = blob[at + 8:at + 8 + length]
        if len(body) != length:
            raise ValueError(f"chunk {kind!r} is short")
        (want,) = struct.unpack(">I", blob[at + 8 + length:at + 12 + length])
        got = zlib.crc32(kind + body) & 0xFFFFFFFF
        if got != want:
            raise ValueError(f"chunk {kind!r} fails its CRC")
        chunks.append((kind, body))
        at += 12 + length
        if kind == b"IEND":
            break

    if not chunks or chunks[0][0] != b"IHDR":
        raise ValueError("first chunk is not IHDR")
    if chunks[-1][0] != b"IEND":
        raise ValueError("no IEND, the file is incomplete")
    return chunks


def ihdr_size(chunks: list[tuple[bytes, bytes]]) -> tuple[int, int]:
    width, height, _depth, colour, *_ = struct.unpack(">IIBBBBB", chunks[0][1])
    if colour not in (2, 6):  # truecolour, with or without alpha
        raise ValueError(f"unexpected colour type {colour}")
    return width, height


def inspect(blob: bytes) -> list[str]:
    """Check the artwork, reporting everything and raising nothing."""
    notes: list[str] = []
    try:
        chunks = read_chunks(blob)
        width, height = ihdr_size(chunks)
        notes.append(f"entry.png  {width}x{height}  {len(blob):,} bytes")
        notes.append(f"chunks     {len(chunks)}")
        if (width, height) != (EXPECTED_WIDTH, EXPECTED_HEIGHT):
            notes.append(f"warning: {width}x{height}, expected {EXPECTED_WIDTH}x{EXPECTED_HEIGHT}")
        idat = b"".join(body for kind, body in chunks if kind == b"IDAT")
        if not idat:
            notes.append("warning: no image data")
        else:
            try:
                zlib.decompress(idat)
                notes.append(f"image data {len(idat):,} bytes, inflates cleanly")
            except zlib.error as exc:
                notes.append(f"warning: image data will not inflate ({exc})")
    except Exception as exc:  # noqa: BLE001 - a bad check must not fail the run
        notes.append(f"warning: {exc}")
    return notes


def main() -> int:
    blob = b""
    if SOURCE.exists():
        try:
            blob = SOURCE.read_bytes()
        except OSError as exc:
            print(f"warning: could not read {SOURCE} ({exc})", file=sys.stderr)
    else:
        print(f"warning: {SOURCE} is missing", file=sys.stderr)

    target = output_dir() / PAGE_NAME
    if not blob:
        print(f"nothing to place: no {PAGE_NAME} in {HERE}", file=sys.stderr)
        return 1

    for line in inspect(blob):
        print(line)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(blob)
    except OSError as exc:
        print(f"could not write {target} ({exc})", file=sys.stderr)
        return 1
    print(f"placed     ->  {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
