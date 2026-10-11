#!/usr/bin/env python3
"""Compress videos for the web (H.264 MP4, plays in every browser).

Media lives in one folder per blog post:
  assets/post/<post>/raw/   originals (git-ignored, not published)
  assets/post/<post>/       compressed .mp4 (same name) + .jpg still frame
                            (used as <video poster> and blog-list thumbnail)
<post> is the post file name without the date, e.g. _posts/2025-10-10-ur5_allegro.md -> ur5_allegro

Usage
  python tools/compress_video.py                       # every assets/post/*/raw/
  python tools/compress_video.py ur5_allegro           # one post
  python tools/compress_video.py assets/post/ur5_allegro/raw/clip.mov   # specific files
  python tools/compress_video.py --height 1080 --crf 23 --keep-audio
  python tools/compress_video.py -f --ignore-rotation assets/post/ur5_allegro/raw/clip.mp4   # clip came out sideways

Uses the system ffmpeg if installed, otherwise the one bundled with imageio-ffmpeg
(pip install imageio-ffmpeg).
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POST_DIR = ROOT / "assets/post"
VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".mkv", ".webm", ".avi"}


def find_ffmpeg():
    if shutil.which("ffmpeg"):
        return "ffmpeg"
    try:
        import imageio_ffmpeg
    except ImportError:
        sys.exit("ffmpeg not found. Install it (brew install ffmpeg) or: pip install imageio-ffmpeg")
    return imageio_ffmpeg.get_ffmpeg_exe()


def collect_inputs(paths):
    """Files to encode. Each arg may be a post name, a folder or a file."""
    if not paths:
        paths = sorted(str(d) for d in POST_DIR.glob("*/raw") if d.is_dir())
    files = []
    for arg in paths:
        p = Path(arg)
        if not p.exists() and (POST_DIR / arg / "raw").is_dir():
            p = POST_DIR / arg / "raw"
        if p.is_dir():
            files += sorted(f for f in p.iterdir() if f.suffix.lower() in VIDEO_EXTS)
        elif p.exists():
            files.append(p)
        else:
            sys.exit(f"not found: {arg}")
    return files


def output_dir(src, override):
    """assets/post/<post>/raw/clip.mov -> assets/post/<post>/"""
    if override:
        return Path(override)
    return src.parent.parent if src.parent.name == "raw" else src.parent


def compress(ffmpeg, src, dst, args):
    # Scale down to --height (never up), keep aspect, even dimensions for H.264.
    vf = f"scale=-2:'min({args.height},ih)',setsar=1,fps='min({args.fps},source_fps)'"
    cmd = [
        ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
        *(["-display_rotation", "0"] if args.ignore_rotation else []),  # override the (wrong) rotation flag
        "-i", str(src),
        "-vf", vf,
        "-c:v", "libx264", "-preset", "slow", "-crf", str(args.crf),
        "-g", str(args.fps), "-keyint_min", str(args.fps),  # keyframe every ~1s: smooth seeking/looping
        "-pix_fmt", "yuv420p",          # widest browser support
        "-movflags", "+faststart",      # start playing before fully downloaded
    ]
    cmd += ["-c:a", "aac", "-b:a", "96k"] if args.keep_audio else ["-an"]
    cmd.append(str(dst))
    subprocess.run(cmd, check=True)


def make_poster(ffmpeg, video, poster, at=1.0, width=640):
    """Still frame (JPEG) used as the <video poster> and as the blog-list thumbnail."""
    cmd = [
        ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
        "-ss", str(at), "-i", str(video),
        "-frames:v", "1", "-vf", f"scale='min({width},iw)':-2", "-q:v", "4",
        str(poster),
    ]
    subprocess.run(cmd, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("inputs", nargs="*", help="post names, folders or files (default: every assets/post/*/raw/)")
    parser.add_argument("-o", "--out", help="output folder (default: the post folder, i.e. the parent of raw/)")
    parser.add_argument("--height", type=int, default=720, help="max output height in px (default 720)")
    parser.add_argument("--crf", type=int, default=28, help="quality, lower = better/bigger (default 28)")
    parser.add_argument("--fps", type=int, default=30, help="max frame rate (default 30)")
    parser.add_argument("--keep-audio", action="store_true", help="keep the audio track (dropped by default)")
    parser.add_argument("--ignore-rotation", action="store_true",
                        help="ignore the rotation flag in the file (use when a clip comes out sideways)")
    parser.add_argument("-f", "--force", action="store_true", help="re-encode even if output is up to date")
    args = parser.parse_args()

    ffmpeg = find_ffmpeg()
    files = collect_inputs(args.inputs)
    if not files:
        print(f"no videos found (put originals in {POST_DIR.relative_to(ROOT)}/<post>/raw/)")

    for src in files:
        out_dir = output_dir(src, args.out)
        out_dir.mkdir(parents=True, exist_ok=True)
        dst = out_dir / (src.stem + ".mp4")
        if dst.resolve() == src.resolve():
            sys.exit(f"output would overwrite input: {src} (put originals in a raw/ subfolder)")
        poster = dst.with_suffix(".jpg")
        if not args.force and dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
            if not poster.exists():
                make_poster(ffmpeg, dst, poster)
            print(f"skip  {src.name} (up to date)")
            continue
        compress(ffmpeg, src, dst, args)
        make_poster(ffmpeg, dst, poster)
        before, after = src.stat().st_size, dst.stat().st_size
        print(f"done  {src.name} -> {dst.relative_to(ROOT) if dst.is_relative_to(ROOT) else dst}"
              f"  {before / 1e6:.1f}MB -> {after / 1e6:.1f}MB ({after / before:.0%})")


if __name__ == "__main__":
    main()
