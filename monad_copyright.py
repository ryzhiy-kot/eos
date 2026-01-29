# PROJECT: MONAD
# AUTHOR: Kyrylo Yatsenko
# YEAR: 2026
# * COPYRIGHT NOTICE:
# © 2026 Kyrylo Yatsenko. All rights reserved.
#
# This work represents a proprietary methodology for Human-Machine Interaction (HMI).
# All source code, logic structures, and User Experience (UX) frameworks
# contained herein are the sole intellectual property of Kyrylo Yatsenko.
#
# ATTRIBUTION REQUIREMENT:
# Any use of this program, or any portion thereof (including code snippets and
# interaction patterns), may not be used, redistributed, or adapted
# without explicit, visible credit to Kyrylo Yatsenko as the original author.

import os

# --- CONFIGURATION ---
AUTHOR = "Kyrylo Yatsenko"
PROJECT_NAME = "MONAD"
YEAR = "2026"

# Folders and files to strictly ignore
IGNORE_FOLDERS = {".venv", "__pycache__", "node_modules", ".git"}
IGNORE_FILES = {"__init__.py"}


def get_header(extension):
    """Returns the header formatted for the specific file type."""
    body = f"""PROJECT: {PROJECT_NAME}
AUTHOR: {AUTHOR}
YEAR: {YEAR}
* COPYRIGHT NOTICE:
© {YEAR} {AUTHOR}. All rights reserved.

This work represents a proprietary methodology for Human-Machine Interaction (HMI).
All source code, logic structures, and User Experience (UX) frameworks
contained herein are the sole intellectual property of {AUTHOR}.

ATTRIBUTION REQUIREMENT:
Any use of this program, or any portion thereof (including code snippets and
interaction patterns), may not be used, redistributed, or adapted
without explicit, visible credit to {AUTHOR} as the original author."""

    if extension == ".py":
        return "\n".join([f"# {line}" for line in body.split("\n")]) + "\n"
    else:
        return "/**\n * " + body.replace("\n", "\n * ") + "\n */\n"


TARGET_EXTENSIONS = (".py", ".ts", ".tsx")


def apply_copyright(directory):
    for root, dirs, files in os.walk(directory):
        # Modifying dirs in-place allows os.walk to skip ignored folders
        dirs[:] = [d for d in dirs if d not in IGNORE_FOLDERS]

        for file in files:
            if file in IGNORE_FILES:
                continue

            ext = os.path.splitext(file)[1]
            if ext in TARGET_EXTENSIONS:
                file_path = os.path.join(root, file)

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    if f"AUTHOR: {AUTHOR}" in content:
                        print(f"Skipping: {file_path} (Already Protected)")
                        continue

                    header = get_header(ext)
                    new_content = header + "\n" + content

                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    print(f"Updated: {file_path}")
                except Exception as e:
                    print(f"Could not update {file_path}: {e}")


if __name__ == "__main__":
    current_dir = os.getcwd()
    print(f"Starting scoped copyright update in: {current_dir}")
    print(f"Ignoring: {', '.join(IGNORE_FOLDERS)} and {', '.join(IGNORE_FILES)}")
    apply_copyright(current_dir)
    print("\nProcess complete.")
