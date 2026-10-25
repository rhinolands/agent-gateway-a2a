"""Docs gates for a docs-only repo. Stdlib only.

  python tools/check_docs.py svg    every .svg parses as XML and has a viewBox
  python tools/check_docs.py links  every relative link or image in *.md exists

Exits non-zero on the first failing gate, listing each problem.
"""

from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP = {".git", "node_modules"}
LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")


def files(suffix: str) -> list[Path]:
    return [
        p
        for p in sorted(ROOT.rglob(f"*{suffix}"))
        if not SKIP.intersection(p.relative_to(ROOT).parts)
    ]


def check_svg() -> list[str]:
    problems = []
    for p in files(".svg"):
        try:
            root = ET.parse(p).getroot()
        except ET.ParseError as e:
            problems.append(f"{p.relative_to(ROOT)}: not well-formed ({e})")
            continue
        if "viewBox" not in root.attrib:
            problems.append(f"{p.relative_to(ROOT)}: no viewBox")
    return problems


def check_links() -> list[str]:
    problems = []
    for md in files(".md"):
        for target in LINK.findall(md.read_text(encoding="utf-8")):
            if re.match(r"^[a-z]+:|^#", target):
                continue  # external URL, mailto or in-page anchor
            path = target.split("#", 1)[0]
            if not (md.parent / path).exists():
                problems.append(f"{md.relative_to(ROOT)}: missing {target}")
    return problems


def main() -> int:
    gates = {"svg": check_svg, "links": check_links}
    names = sys.argv[1:] or list(gates)
    failed = False
    for name in names:
        problems = gates[name]()
        print(f"{name}: {'FAIL' if problems else 'ok'}")
        for p in problems:
            print(f"  - {p}")
        failed = failed or bool(problems)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
