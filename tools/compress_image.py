#!/usr/bin/env python3
"""Shrink photos/screenshots for the web (JPEG, max width 1280px).

Same layout as compress_video.py:
  assets/post/<post>/raw/   originals (git-ignored, not published)
  assets/post/<post>/       compressed .jpg (same name)

Usage
  python tools/compress_image.py                  # every assets/post/*/raw/
  python tools/compress_image.py jupiter          # one post
  python tools/compress_image.py --width 1600 --quality 3

Uses the same ffmpeg as compress_video.py.
"""

import argparse
import subprocess
import sys
from pathlib import Path

from compress_video import POST_DIR, ROOT, find_ffmpeg, output_dir

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}


def collect_inputs(paths):
    if not paths:
        paths = sorted(str(d) for d in POST_DIR.glob("*/raw") if d.is_dir())
    files = []
    for arg in paths:
        p = Path(arg)
        if not p.exists() and (POST_DIR / arg / "raw").is_dir():
            p = POST_DIR / arg / "raw"
        if p.is_dir():
            files += sorted(f for f in p.iterdir() if f.suffix.lower() in IMAGE_EXTS)
        elif p.exists():
            files.append(p)
        else:
            sys.exit(f"not found: {arg}")
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("inputs", nargs="*", help="post names, folders or files (default: every assets/post/*/raw/)")
    parser.add_argument("-o", "--out", help="output folder (default: the post folder, i.e. the parent of raw/)")
    parser.add_argument("--width", type=int, default=1280, help="max output width in px (default 1280)")
    parser.add_argument("--quality", type=int, default=4, help="JPEG quality 2(best)-31 (default 4)")
    parser.add_argument("-f", "--force", action="store_true", help="re-encode even if output is up to date")
    args = parser.parse_args()

    ffmpeg = find_ffmpeg()
    for src in collect_inputs(args.inputs):
        out = output_dir(src, args.out)
        out.mkdir(parents=True, exist_ok=True)
        dst = out / (src.stem + ".jpg")
        if dst.resolve() == src.resolve():
            sys.exit(f"output would overwrite input: {src} (put originals in a raw/ subfolder)")
        if not args.force and dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
            print(f"skip  {src.name} (up to date)")
            continue
        subprocess.run([
            ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(src),
            "-vf", f"scale='min({args.width},iw)':-2", "-q:v", str(args.quality), str(dst),
        ], check=True)
        before, after = src.stat().st_size, dst.stat().st_size
        print(f"done  {src.name} -> {dst.relative_to(ROOT) if dst.is_relative_to(ROOT) else dst}"
              f"  {before / 1e6:.1f}MB -> {after / 1e6:.2f}MB ({after / before:.0%})")


if __name__ == "__main__":
    main()
