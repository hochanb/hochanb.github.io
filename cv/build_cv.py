#!/usr/bin/env python3
"""Build a one-page PDF CV from cv/cv.yml (independent of the site data).

Sources
  cv/cv.yml        all CV content
  cv/private.yml   optional, git-ignored (phone number, ...)
  cv/template.html layout (Jinja2), cv/style.css styling

Usage
  python cv/build_cv.py                     # -> assets/cv.pdf
  python cv/build_cv.py -o out.pdf --html   # also keep the intermediate HTML
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import qrcode
import qrcode.image.svg
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup, escape

ROOT = Path(__file__).resolve().parent.parent
CV_DIR = ROOT / "cv"

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "google-chrome",
    "chromium",
    "chromium-browser",
]


def load_yaml(path, default=None):
    if not path.exists():
        return default
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return default if data is None else data


def find_chrome():
    if os.environ.get("CHROME"):
        return os.environ["CHROME"]
    for c in CHROME_CANDIDATES:
        if Path(c).exists() or shutil.which(c):
            return c
    sys.exit("Chrome/Chromium not found. Set the CHROME environment variable to its path.")


def qr_svg(url):
    """Inline SVG QR code for `url`; size is set by CSS (.qr)."""
    img = qrcode.make(url, image_factory=qrcode.image.svg.SvgPathImage, border=0,
                      error_correction=qrcode.constants.ERROR_CORRECT_M)
    svg = img.to_string(encoding="unicode")
    return re.sub(r'\s(width|height)="[^"]*"', "", svg, count=2)


def collect():
    cv = load_yaml(CV_DIR / "cv.yml", {})
    private = load_yaml(CV_DIR / "private.yml", {})
    profile = cv.get("profile", {})

    photo = profile.get("photo")
    photo_path = ROOT / photo.lstrip("/") if photo else None
    if photo_path and not photo_path.exists():
        print(f"warning: photo not found: {photo}", file=sys.stderr)
        photo_path = None

    return {
        "cv": cv,
        "p": profile,
        "c": cv.get("contact", {}),
        "phone": private.get("phone"),
        "photo": photo_path.as_uri() if photo_path else None,
        "qr": Markup(qr_svg(profile["qr"])) if profile.get("qr") else None,
        "css": (CV_DIR / "style.css").read_text(encoding="utf-8"),
    }


def link_text(url, key):
    """Short label for a profile link: 'github.com/hochanb', 'Google Scholar', ..."""
    if key == "scholar":
        return "Google Scholar"
    return re.sub(r"^https?://(www\.)?|/$", "", url)


def inline_markdown(text):
    """Tiny subset of Markdown for one-line fields: **bold**, *italic*, [text](url)."""
    s = str(escape(text))
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\*(.+?)\*", r"<em>\1</em>", s)
    return Markup(s)


def render_html(context):
    env = Environment(
        loader=FileSystemLoader(CV_DIR),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    # Bold my own name in an author list.
    env.filters["me"] = lambda authors, name: Markup(
        str(escape(authors)).replace(str(escape(name)), f'<span class="me">{escape(name)}</span>')
    )
    env.filters["md"] = inline_markdown
    env.filters["linktext"] = link_text
    context["css"] = Markup(context["css"])
    return env.get_template("template.html").render(**context)


def html_to_pdf(html_path, pdf_path):
    chrome = find_chrome()
    with tempfile.TemporaryDirectory() as profile:
        cmd = [
            chrome,
            "--headless=new",
            "--disable-gpu",
            "--no-pdf-header-footer",
            "--allow-file-access-from-files",
            "--virtual-time-budget=10000",  # let web fonts load before printing
            f"--user-data-dir={profile}",
            f"--print-to-pdf={pdf_path}",
            html_path.as_uri(),
        ]
        # Headless Chrome sometimes keeps running after the PDF is written,
        # so wait until the file stops growing and then shut it down ourselves.
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        deadline = time.time() + 60
        last_size = -1
        while time.time() < deadline and proc.poll() is None:
            time.sleep(0.5)
            size = pdf_path.stat().st_size if pdf_path.exists() else -1
            if size > 0 and size == last_size:
                break
            last_size = size
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
    if not pdf_path.exists() or pdf_path.stat().st_size == 0:
        sys.exit(f"PDF generation failed:\n{proc.stderr.read() if proc.stderr else ''}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-o", "--output", default=str(ROOT / "assets/cv.pdf"), help="output PDF path")
    parser.add_argument("--html", action="store_true", help="also write the intermediate HTML next to the PDF")
    args = parser.parse_args()

    html = render_html(collect())

    pdf_path = Path(args.output).resolve()
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    if pdf_path.exists():
        pdf_path.unlink()

    # The HTML must sit inside the project so file:// image paths resolve.
    html_path = CV_DIR / ".cv.html"
    html_path.write_text(html, encoding="utf-8")
    try:
        html_to_pdf(html_path, pdf_path)
    finally:
        if args.html:
            shutil.copy(html_path, pdf_path.with_suffix(".html"))
        html_path.unlink(missing_ok=True)

    pages = len(re.findall(rb"/Type\s*/Page[^s]", pdf_path.read_bytes()))
    print(f"wrote {pdf_path.relative_to(ROOT) if pdf_path.is_relative_to(ROOT) else pdf_path} ({pages} page{'s' if pages != 1 else ''})")
    if pages > 1:
        print("warning: CV overflows one page — trim content or tighten cv/style.css", file=sys.stderr)


if __name__ == "__main__":
    main()
