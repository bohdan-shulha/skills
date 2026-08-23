#!/usr/bin/env python3
"""Verify a .repo-wiki/ knowledge base.

Usage: verify.py [repo_root]

Errors (exit 1): a backticked path that does not resolve, a relative link
that does not resolve. Warnings (exit 0): a durability hit that the agent
must justify against the skill's number rule, or delete.

A line that contains the words "deliberately absent" is exempt from path
errors on that line.
"""
import re
import sys
from pathlib import Path

PATH_EXTENSIONS = (
    ".md .ts .tsx .js .jsx .mjs .cjs .json .jsonc .yaml .yml .toml .py .go "
    ".rs .sql .sh .css .html .prisma .env .txt .xml .graphql .proto"
).split()

DURABILITY_CHECKS = [
    ("percentage", re.compile(r"\d+(\.\d+)?\s?%")),
    ("bare decimal", re.compile(r"\b\d+\.\d+\b(?!\s?%)")),
    ("count", re.compile(r"\b\d+ (files|lines|modules|tables|rows|tests|packages|apps|services|endpoints|routes|jobs|columns)\b")),
    ("ranking", re.compile(r"\b(most|least|lowest|highest|fewest|largest|smallest|busiest|by far|almost all)\b", re.I)),
    ("volatility", re.compile(r"\b(currently|recently|for now|as of)\b", re.I)),
    ("change narration", re.compile(r"\b(previously|formerly|migrated (from|to)|renamed from|used to be)\b", re.I)),
    ("date", re.compile(r"\b20\d{2}-\d{2}(-\d{2})?\b")),
    ("issue reference", re.compile(r"(?<!\w)#\d+\b")),
]

INLINE_CODE = re.compile(r"`([^`]+)`")
LINK = re.compile(r"\]\(([^)\s#]+)(#[^)]*)?\)")
FENCE = re.compile(r"^\s*(```|~~~)")


def looks_like_path(span):
    if any(ch in span for ch in "*{}<>=$ \t") or "://" in span:
        return None
    if span.startswith(("/", "@", "-", "#", "http")):
        return None
    if ":" in span:
        head = span.split(":", 1)[0]
        return head if "/" in head else None
    if "/" in span:
        return span.rstrip("/")
    if any(span.endswith(ext) for ext in PATH_EXTENSIONS) and len(span) > len(Path(span).suffix):
        return span
    return None


def resolves(path, page, repo_root, wiki_root):
    return any((base / path).exists() for base in (repo_root, wiki_root, page.parent))


def main():
    repo_root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    wiki_root = repo_root / ".repo-wiki"
    if not wiki_root.is_dir():
        print(f"no wiki root at {wiki_root}", file=sys.stderr)
        return 2

    errors = warnings = 0
    for page in sorted(wiki_root.rglob("*.md")):
        rel_page = page.relative_to(repo_root)
        in_fence = False
        for lineno, line in enumerate(page.read_text().splitlines(), 1):
            if FENCE.match(line):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            exempt = "deliberately absent" in line.lower()

            for span in INLINE_CODE.findall(line):
                path = looks_like_path(span)
                if path and not exempt and not resolves(path, page, repo_root, wiki_root):
                    print(f"ERROR path {rel_page}:{lineno}: `{span}` does not resolve")
                    errors += 1

            for target, _ in LINK.findall(line):
                if target.startswith(("http", "mailto:", "/")):
                    continue
                if not (page.parent / target).exists():
                    print(f"ERROR link {rel_page}:{lineno}: ({target}) does not resolve")
                    errors += 1

            prose = INLINE_CODE.sub("", line)
            for name, pattern in DURABILITY_CHECKS:
                for match in pattern.finditer(prose):
                    print(f'WARN {name} {rel_page}:{lineno}: "{match.group(0)}"')
                    warnings += 1

    print(f"{errors} errors, {warnings} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
