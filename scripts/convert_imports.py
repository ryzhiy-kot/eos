#!/usr/bin/env python3
"""Convert absolute imports to relative for handler files within same package.

Only converts for files that are NOT __init__.py files, to avoid package import issues.
"""

import re
from pathlib import Path

APP_DIR = Path(
    "/run/media/ryzhiy/DATA/repos/finagent-platform-solid-refactor/backend/app"
)


def get_package_info(file_path: Path) -> tuple[str, str, bool]:
    """Get first package, subpackage, and whether it's a handler file.

    Returns: (first_pkg, subpkg, is_handler)
    E.g., services/mock_responses/handler_pnl.py -> ("services", "mock_responses", True)
    """
    rel = file_path.relative_to(APP_DIR)
    parts = list(rel.parts[:-1])  # Exclude filename

    if len(parts) < 2:
        return "", "", False

    is_handler = file_path.stem != "__init__"
    return parts[0], parts[1] if len(parts) > 1 else "", is_handler


def convert_import(line: str, source_pkg: str, subpkg: str) -> str:
    """Convert import to relative if in same subpackage."""
    if line.strip().startswith("from .") or "from __future__" in line:
        return line

    pattern = r"^(\s*)from app\.([\w.]+) import (.+)$"
    match = re.match(pattern, line)

    if not match:
        return line

    indent = match.group(1)
    target_module = match.group(2)
    imports = match.group(3)

    target_parts = target_module.split(".")

    # Only convert if target is in the same subpackage (e.g., services.mock_responses -> mock_responses)
    if (
        len(target_parts) >= 2
        and target_parts[0] == source_pkg
        and target_parts[1] == subpkg
    ):
        remaining = target_module.split(".", 2)[2] if len(target_parts) > 2 else ""

        if remaining:
            return f"{indent}from .{remaining} import {imports}\n"
        else:
            return f"{indent}from . import {imports}\n"

    return line


def process_file(file_path: Path) -> bool:
    """Process a single Python file."""
    source_pkg, subpkg, is_handler = get_package_info(file_path)

    if not is_handler or not source_pkg or not subpkg:
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
            new_line = convert_import(line, source_pkg, subpkg)
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
