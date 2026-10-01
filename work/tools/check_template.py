#!/usr/bin/env python3
"""Template integrity check.

Verifies the Tiny Tapeout CMOS5L template freeze rules against the
`template-cmos5l` tag and the structural invariants in
knowledgebase/versioning.md. Run from the repo root:

    python work/tools/check_template.py

Exit code 0 = template intact, 1 = freeze broken.
"""

import re
import subprocess
import sys
from pathlib import Path

TAG = "template-cmos5l"
FROZEN_IDENTICAL = ["src/config.json", ".github/workflows"]
MUST_EXIST = [
    "src/project.v",
    "test/Makefile",
    "test/tb.v",
    "test/test.py",
    "info.yaml",
]

errors = []


def check(ok, message):
    if not ok:
        errors.append(message)


def main():
    root = Path(
        subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    )

    # 1. Byte-identical files versus the pristine template tag.
    diff = subprocess.run(
        ["git", "diff", "--name-only", TAG, "--"] + FROZEN_IDENTICAL,
        capture_output=True, text=True, cwd=root,
    )
    check(diff.returncode == 0, f"git diff against tag {TAG} failed: {diff.stderr.strip()}")
    for line in diff.stdout.split():
        check(False, f"frozen file differs from {TAG}: {line}")

    # 2. Required files exist.
    for rel in MUST_EXIST:
        check((root / rel).is_file(), f"missing template file: {rel}")

    # 3. Top module name.
    project_v = root / "src" / "project.v"
    if project_v.is_file():
        check(
            re.search(r"^\s*module\s+tt_um_\w+", project_v.read_text(encoding="utf-8"), re.M),
            "src/project.v has no tt_um_ module",
        )

    # 4. Makefile structure.
    makefile_path = root / "test" / "Makefile"
    makefile = makefile_path.read_text(encoding="utf-8") if makefile_path.is_file() else ""
    sources_match = re.search(r"^PROJECT_SOURCES\s*=\s*(.*)$", makefile, re.M)
    check(sources_match is not None, "test/Makefile lost PROJECT_SOURCES")
    check("cocotb-config --makefiles" in makefile, "test/Makefile lost the cocotb include")

    # 5. info.yaml invariants.
    info_path = root / "info.yaml"
    info = info_path.read_text(encoding="utf-8") if info_path.is_file() else ""
    check(re.search(r"^yaml_version:\s*6\s*$", info, re.M), "info.yaml yaml_version is not 6")
    for group, prefix in (("ui", "ui"), ("uo", "uo"), ("uio", "uio")):
        for i in range(8):
            check(
                re.search(rf"^\s*{prefix}\[{i}\]:", info, re.M),
                f"info.yaml is missing pin {prefix}[{i}]",
            )

    # 6. Source lists agree and files exist.
    yaml_sources = re.findall(r'^\s*-\s*"([^"]+\.s?v)"\s*$', info, re.M)
    check(bool(yaml_sources), "info.yaml source_files is empty")
    makefile_sources = sources_match.group(1).split() if sources_match else []
    check(
        set(yaml_sources) == set(makefile_sources),
        "info.yaml source_files != test/Makefile PROJECT_SOURCES: "
        f"{sorted(set(yaml_sources) ^ set(makefile_sources))}",
    )
    for src in yaml_sources:
        check((root / "src" / src).is_file(), f"listed source missing from src/: {src}")

    if errors:
        print("TEMPLATE FREEZE BROKEN:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("Template intact: frozen files match "
          f"{TAG}, structure and source lists are consistent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
