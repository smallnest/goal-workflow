#!/usr/bin/env python3
"""Fetch an itshover icon and emit a clean, static, inline-able SVG.

itshover ships icons as shadcn registry items: each is a React/motion
component (`https://itshover.com/r/<name>.json`). This script downloads that
JSON, isolates the <svg> markup, strips all React/motion-only attributes
(ref, onHover*, className, style, animate, ...), resolves the component props
(size/color/strokeWidth) into literal values, kebab-cases SVG attributes, and
returns plain SVG suitable for embedding directly into HTML or Markdown.

Usage:
  python3 fetch_icon.py <icon-name> [--size N] [--color C] [--stroke-width W]
  python3 fetch_icon.py --list                 # print all available icon names
  python3 fetch_icon.py --search <term>        # filter icon names by substring

Examples:
  python3 fetch_icon.py heart-icon --size 32 --color "#e11d48"
  python3 fetch_icon.py brand-anthropic-icon --color "#d97757"
"""
import argparse
import json
import re
import sys
import urllib.request

BASE = "https://itshover.com/r"
REGISTRY = f"{BASE}/registry.json"

# camelCase React attrs -> kebab-case / lowercase SVG attrs
KEBAB = {
    "strokeWidth": "stroke-width", "strokeLinecap": "stroke-linecap",
    "strokeLinejoin": "stroke-linejoin", "strokeDasharray": "stroke-dasharray",
    "strokeDashoffset": "stroke-dashoffset", "strokeMiterlimit": "stroke-miterlimit",
    "strokeOpacity": "stroke-opacity", "fillOpacity": "fill-opacity",
    "fillRule": "fill-rule", "clipRule": "clip-rule", "clipPath": "clip-path",
    "stopColor": "stop-color", "stopOpacity": "stop-opacity",
    "gradientUnits": "gradientUnits", "gradientTransform": "gradientTransform",
    "xmlnsXlink": "xmlns:xlink", "xlinkHref": "xlink:href",
}

# attributes safe to keep on a static SVG
ALLOWED = {
    "xmlns", "xmlns:xlink", "xlink:href", "viewBox", "width", "height", "fill",
    "stroke", "stroke-width", "stroke-linecap", "stroke-linejoin",
    "stroke-dasharray", "stroke-dashoffset", "stroke-miterlimit",
    "stroke-opacity", "fill-opacity", "fill-rule", "clip-rule", "clip-path",
    "d", "cx", "cy", "r", "rx", "ry", "x", "y", "x1", "y1", "x2", "y2",
    "points", "transform", "opacity", "offset", "stop-color", "stop-opacity",
    "gradientUnits", "gradientTransform", "id", "preserveAspectRatio",
}


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def list_icons():
    return sorted(i["name"] for i in _get(REGISTRY).get("items", []))


def fetch_component(name):
    data = _get(f"{BASE}/{name}.json")
    return data["files"][0]["content"]


def convert(content, size=24, color="currentColor", stroke_width=2):
    """Convert a React/motion icon component's source into a static SVG string."""
    c = content.replace("motion.", "")
    # remove JSX comments {/* ... */}
    c = re.sub(r"\{/\*.*?\*/\}", "", c, flags=re.S)
    m = re.search(r"<svg\b.*?</svg>", c, re.S)
    if not m:
        return None
    block = m.group(0)

    out = []
    for piece in re.split(r"(<[^>]+>)", block):
        if not piece.startswith("<"):
            out.append(piece)
            continue
        tm = re.match(r"<(/?)([\w:]+)(.*?)(/?)>", piece, re.S)
        if not tm:
            out.append(piece)
            continue
        close, tag, attrs, selfclose = tm.groups()
        if close:
            out.append(f"</{tag}>")
            continue
        kept = []
        # attr=value where value is "...", {...balanced...}, or `...`
        for am in re.finditer(
            r'([\w:-]+)=(\{(?:[^{}]|\{[^{}]*\})*\}|"[^"]*"|`[^`]*`)', attrs
        ):
            k, v = am.group(1), am.group(2)
            k = KEBAB.get(k, k)
            if v.startswith('"'):
                val = v[1:-1]
            elif v.startswith("{"):
                inner = v[1:-1].strip()
                if inner == "size":
                    val = str(size)
                elif inner == "color":
                    val = color
                elif inner == "strokeWidth":
                    val = str(stroke_width)
                elif re.fullmatch(r"-?\d+(\.\d+)?", inner):
                    val = inner
                elif re.fullmatch(r'"[^"]*"', inner) or re.fullmatch(r"'[^']*'", inner):
                    val = inner[1:-1]
                else:
                    continue  # unresolved expression -> drop
            else:
                continue  # backtick template (className) -> drop
            if k in ALLOWED:
                kept.append(f'{k}="{val}"')
        attrstr = (" " + " ".join(kept)) if kept else ""
        out.append(f"<{tag}{attrstr}{'/' if selfclose else ''}>")

    svg = "".join(out)
    svg = re.sub(r"\s+", " ", svg).strip()
    svg = re.sub(r"\s*>\s*<\s*", "><", svg)
    # guard: reject anything still carrying React residue
    if "{" in svg or "motion" in svg or "className" in svg:
        return None
    return svg


def main():
    ap = argparse.ArgumentParser(description="Fetch an itshover icon as static SVG.")
    ap.add_argument("name", nargs="?", help="icon name, e.g. heart-icon")
    ap.add_argument("--size", type=int, default=24)
    ap.add_argument("--color", default="currentColor")
    ap.add_argument("--stroke-width", type=float, default=2)
    ap.add_argument("--list", action="store_true", help="list all icon names")
    ap.add_argument("--search", help="filter icon names by substring")
    args = ap.parse_args()

    if args.list or args.search:
        names = list_icons()
        if args.search:
            names = [n for n in names if args.search.lower() in n.lower()]
        print("\n".join(names))
        return 0

    if not args.name:
        ap.error("icon name required (or use --list / --search)")

    try:
        content = fetch_component(args.name)
    except Exception as e:
        print(f"ERROR: could not fetch '{args.name}': {e}", file=sys.stderr)
        print("Try --search <term> to find the right name.", file=sys.stderr)
        return 1

    svg = convert(content, size=args.size, color=args.color, stroke_width=args.stroke_width)
    if not svg:
        print(f"ERROR: could not convert '{args.name}' to static SVG.", file=sys.stderr)
        return 2
    print(svg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
