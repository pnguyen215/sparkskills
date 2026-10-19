#!/usr/bin/env python3
"""Repository validator for the skills library.

Modes:
  (no args)            Validate every SKILL.md (structure, frontmatter, placeholders).
  --markdown-only      Lightweight markdown checks only (fallback when markdownlint is absent).
  --tree               Print the repository tree (excludes .git).

Exits non-zero when validation errors are found.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

EXCLUDED_DIRS = {".git", "node_modules", ".markdownlint-cache", ".markdownlint-cli2-cache"}
AUX_DIRS = {"templates", "scripts"}  # repo-level dirs that are not skill folders
SKILL_AUX_DIRS = {"references", "examples", "templates", "scripts"}  # allowed inside skill folders

REQUIRED_SECTIONS = [
    "purpose",
    "when to use / when not to use",
    "prerequisites & assumptions",
    "step-by-step workflow",
    "enterprise rules & standards",
    "examples",
    "checklist",
    "common pitfalls",
    "references",
]

PLACEHOLDER_PATTERNS = [
    re.compile(r"\bTODO\b"),
    re.compile(r"\bFIXME\b"),
    re.compile(r"\bTBD\b"),
    re.compile(r"lorem ipsum", re.IGNORECASE),
    re.compile(r"\{\{[A-Za-z_]+\}\}"),  # unfilled template variables
    re.compile(r"REPLACE:"),
]

NAME_RE = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$")

errors: list[str] = []
warnings: list[str] = []


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip()).lower()


def iter_md_files(root: Path):
    for path in sorted(root.rglob("*.md")):
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        yield path


def check_markdown_style(path: Path) -> None:
    try:
        raw = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        errors.append(f"{path}: file is not valid UTF-8")
        return
    for lineno, line in enumerate(raw.splitlines(), start=1):
        if line != line.rstrip():
            warnings.append(f"{path}:{lineno}: trailing whitespace")
    if raw and not raw.endswith("\n"):
        warnings.append(f"{path}: missing trailing newline at EOF")


def parse_frontmatter(text: str, path: Path) -> dict | None:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        errors.append(f"{path}: SKILL.md must start with '---' YAML frontmatter")
        return None
    try:
        closing = lines.index("---", 1)
    except ValueError:
        errors.append(f"{path}: frontmatter is not closed with '---'")
        return None
    meta: dict[str, str] = {}
    current_key = None
    for line in lines[1:closing]:
        if not line.strip() or line.strip().startswith("#"):
            continue
        if re.match(r"^\s", line) and current_key:
            meta[current_key] += " " + line.strip()
            continue
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$", line)
        if m:
            current_key = m.group(1)
            meta[current_key] = m.group(2).strip()
    return meta


def validate_skill_md(path: Path, skill_name: str, seen_names: dict[str, str]) -> None:
    text = path.read_text(encoding="utf-8")
    line_count = len(text.splitlines())
    if line_count >= 500:
        errors.append(f"{path}: {line_count} lines (limit: <500); move bulk material into references/")

    meta = parse_frontmatter(text, path)
    if meta is None:
        return
    name = meta.get("name", "")
    description = meta.get("description", "")

    if not name:
        errors.append(f"{path}: frontmatter missing 'name'")
    elif not NAME_RE.match(name):
        errors.append(f"{path}: name '{name}' must be kebab-case (lowercase letters, digits, hyphens)")
    elif len(name) > 64:
        errors.append(f"{path}: name '{name}' exceeds 64 characters ({len(name)})")
    elif name != skill_name:
        errors.append(f"{path}: name '{name}' does not match folder name '{skill_name}'")
    if name and name in seen_names:
        errors.append(f"{path}: duplicate skill name '{name}' (also used by {seen_names[name]})")
    elif name:
        seen_names[name] = str(path)

    if not description:
        errors.append(f"{path}: frontmatter missing 'description'")
    elif len(description) < 20:
        errors.append(f"{path}: description too short ({len(description)} chars, min 20)")
    elif len(description) > 1024:
        errors.append(f"{path}: description exceeds 1024 characters ({len(description)})")

    body = text[text.index("\n---", 3) + 4 :] if "\n---" in text[3:] else text
    headings = [norm(m.group(1)) for m in re.finditer(r"^##\s+(.+)$", body, re.MULTILINE)]
    for required in REQUIRED_SECTIONS:
        if not any(h.startswith(required) for h in headings):
            errors.append(f"{path}: missing required section '## {required.title()}'")

    rel = path.relative_to(REPO_ROOT)
    if rel.parts[0] in AUX_DIRS:
        return  # template files may contain {{variables}}
    for pattern in PLACEHOLDER_PATTERNS:
        m = pattern.search(text)
        if m:
            errors.append(f"{path}: placeholder-like text found: '{m.group(0)}'")


def validate() -> int:
    seen_names: dict[str, str] = {}
    skill_count = 0
    if not REPO_ROOT.exists():
        print(f"ERROR: repository root not found: {REPO_ROOT}")
        return 1
    for skill_md in sorted(REPO_ROOT.rglob("SKILL.md")):
        if any(part in EXCLUDED_DIRS for part in skill_md.parts):
            continue
        rel = skill_md.relative_to(REPO_ROOT)
        parts = rel.parts
        if len(parts) < 2:
            errors.append(f"{rel}: SKILL.md must live in its own named folder, not the repo root")
            continue
        folder_name = parts[-2]
        if not NAME_RE.match(folder_name):
            errors.append(f"{rel}: folder '{folder_name}' must be kebab-case")
            continue
        validate_skill_md(skill_md, folder_name, seen_names)
        skill_count += 1
        for sibling in skill_md.parent.iterdir():
            if sibling.is_dir() and sibling.name not in SKILL_AUX_DIRS:
                errors.append(f"{rel}: unexpected subfolder '{sibling.name}/' (allowed: {sorted(SKILL_AUX_DIRS)})")

    # One skill per folder: every non-aux directory must contain a SKILL.md.
    for d in sorted(REPO_ROOT.rglob("*")):
        if not d.is_dir() or any(part in EXCLUDED_DIRS or part in AUX_DIRS for part in d.parts):
            continue
        rel = d.relative_to(REPO_ROOT)
        if rel.parts[-1] in SKILL_AUX_DIRS or len(rel.parts) == 1 and rel.parts[0] in AUX_DIRS:
            continue
        if (d / "SKILL.md").exists():
            continue
        # A category root holds skill folders instead of its own SKILL.md.
        if any(c.is_dir() and (c / "SKILL.md").exists() for c in d.iterdir()):
            continue
        errors.append(f"{rel}: folder has no SKILL.md (one skill per folder)")

    for md in iter_md_files(REPO_ROOT):
        if md.name == "SKILL.md" or md.name == "SKILL.template.md":
            continue
        check_markdown_style(md)

    if warnings:
        print(f"Warnings: {len(warnings)}")
        for w in warnings[:20]:
            print(f"  ! {w}")
    if errors:
        print(f"FAILED: {len(errors)} error(s)")
        for e in errors:
            print(f"  x {e}")
        return 1
    print(f"OK: {skill_count} skills validated, all SKILL.md files complete.")
    return 0


def print_tree() -> None:
    root = REPO_ROOT

    def walk(directory: Path, prefix: str = "") -> None:
        entries = [e for e in sorted(directory.iterdir(), key=lambda p: (p.is_file(), p.name))
                   if e.name not in EXCLUDED_DIRS]
        for index, entry in enumerate(entries):
            connector = "└── " if index == len(entries) - 1 else "├── "
            print(f"{prefix}{connector}{entry.name}")
            if entry.is_dir():
                extension = "    " if index == len(entries) - 1 else "│   "
                walk(entry, prefix + extension)

    print(f"{root.name}/")
    walk(root)


def main() -> int:
    if "--tree" in sys.argv:
        print_tree()
        return 0
    if "--markdown-only" in sys.argv:
        for md in iter_md_files(REPO_ROOT):
            check_markdown_style(md)
        for w in warnings:
            print(f"  ! {w}")
        print(f"Markdown checks done: {len(warnings)} warning(s), no errors.")
        return 0
    return validate()


if __name__ == "__main__":
    sys.exit(main())
