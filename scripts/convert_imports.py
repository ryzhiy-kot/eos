#!/usr/bin/env python3
"""Convert absolute imports to relative for imports within same package group.

Converts ALL files in the same package (not just handlers).
"""

import re
from pathlib import Path

APP_DIR = Path(
    "/run/media/ryzhiy/DATA/repos/finagent-platform-solid-refactor/backend/app"
)


def get_first_package(file_path: Path) -> str:
    """Get the first package (e.g., 'services', 'api', 'agents')."""
    rel = file_path.relative_to(APP_DIR)
    parts = rel.parts
    if len(parts) > 1:
        return parts[0]
    return ""


def convert_import(line: str, source_pkg: str) -> str:
    """Convert import to relative if in same first package."""
    if line.strip().startswith("from .") or "from __future__" in line:
        return line

    pattern = r"^(\s*)from app\.([\w.]+) import (.+)$"
    match = re.match(pattern, line)

    if not match:
        return line

    indent = match.group(1)
    target_module = match.group(2)
    imports = match.group(3)

    target_first = target_module.split(".")[0]

    if target_first != source_pkg:
        return line

    remaining = target_module.split(".", 1)[1] if "." in target_module else ""

    if remaining:
        return f"{indent}from .{remaining} import {imports}\n"
    else:
        return f"{indent}from . import {imports}\n"


def process_file(file_path: Path) -> bool:
    """Process a single Python file."""
    source_pkg = get_first_package(file_path)

    if not source_pkg:
        return False

    try:
        content = file_path.read_text()
    except Exception:
        return False

    lines = content.split("\n")
    new_lines = []
    modified = False

    for line in lines:
        if "from app." in line and not line.strip().startswith("#"):
            new_line = convert_import(line, source_pkg)
            if new_line != line:
                modified = True
                new_lines.append(new_line.rstrip())
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    if modified:
        file_path.write_text("\n".join(new_lines))
        print(f"Modified: {file_path}")
        return True

    return False


def main():
    count = 0
    for py_file in APP_DIR.rglob("*.py"):
        if process_file(py_file):
            count += 1
    print(f"\nProcessed {count} files")


if __name__ == "__main__":
    main()
