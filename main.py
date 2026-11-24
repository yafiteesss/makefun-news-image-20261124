"""Entrypoint: render the 24 November 2026 world-news image.

Writes entry.png into MAKEFUN_OUTPUT_DIR (falling back to /output,
then to ./out). Standard library only, no network, deterministic.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import build_image


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    if not os.path.isdir(out_dir):
        out_dir = os.path.join(HERE, "out")
    os.makedirs(out_dir, exist_ok=True)
    target = os.path.join(out_dir, "entry.png")
    data = build_image.encode_png(build_image.render())
    with open(target, "wb") as f:
        f.write(data)
    print("wrote", target, len(data), "bytes")


if __name__ == "__main__":
    main()
