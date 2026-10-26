"""Validate Phase 1 documentation offline: links, requirement IDs and matrix completeness.

Checks performed:

1. every relative Markdown link in a tracked ``*.md`` file resolves to a real path;
2. the traceability matrix has the required twelve columns;
3. requirement IDs are unique and every expected ID appears exactly once;
4. every row has a non-empty requirement, acceptance criterion, evidence pointer and
   status, and the status comes from the fixed vocabulary;
5. the status summary in the document matches the rows, both in counts and in the
   exact requirement IDs listed for each status.

No network access is used.
"""
from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path

MATRIX_PATH = Path("docs/REQUIREMENTS_TRACEABILITY.md")

ALLOWED_STATUSES = (
    "Verified complete",
    "Partially complete",
    "Not implemented",
    "Blocked by external dependency",
    "Needs clarification",
)

REQUIRED_COLUMNS = (
    "ID",
    "Original requirement",
    "Source/reference",
    "Priority",
    "Acceptance criterion",
    "Relevant documentation",
    "Implementation or file path",
    "Required tests or evidence",
    "Current status",
    "Gap or defect",
    "Planned resolution",
    "Dependency or external blocker",
)

EXPECTED_IDS = (
    tuple(f"R{index}" for index in range(1, 16))
    + tuple(f"NFR{index}" for index in range(1, 7))
    + tuple(f"A{index}" for index in range(1, 8))
)

SKIP_DIRECTORIES = {".git", ".venv", ".venv-ci", "node_modules", "build", "dist", "__pycache__"}
LINK_PATTERN = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
SKIP_LINK_PREFIXES = ("http://", "https://", "mailto:", "#", "tel:")


def markdown_files(root: Path) -> list[Path]:
    """All Markdown files under ``root``, ignoring generated and vendor directories."""
    files: list[Path] = []
    for path in sorted(root.rglob("*.md")):
        if any(part in SKIP_DIRECTORIES for part in path.parts):
            continue
        if "egg-info" in str(path):
            continue
        files.append(path)
    return files


def check_links(root: Path, files: list[Path]) -> tuple[list[str], int]:
    """Return broken internal links and the number of links checked."""
    errors: list[str] = []
    checked = 0
    for path in files:
        text = path.read_text(encoding="utf-8")
        for raw_target in LINK_PATTERN.findall(text):
            target = raw_target.strip().split("#", 1)[0].strip()
            if not target or target.startswith(SKIP_LINK_PREFIXES):
                continue
            target = target.strip("<>")
            if target.startswith("/"):
                continue
            checked += 1
            resolved = (path.parent / target).resolve()
            try:
                resolved.relative_to(root.resolve())
            except ValueError:
                errors.append(f"{path}: link escapes the repository: {raw_target}")
                continue
            if not resolved.exists():
                errors.append(f"{path}: broken link target: {raw_target}")
    return errors, checked


def _cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _is_status_summary_row(cells: list[str]) -> bool:
    """True when the two-column status summary that follows the matrix has begun."""
    return len(cells) == 2 and (cells[0] == "Status" or cells[0] in ALLOWED_STATUSES)


def parse_matrix(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    """Return matrix errors plus the parsed rows keyed by column name."""
    errors: list[str] = []
    if not path.exists():
        return [f"missing traceability matrix: {path}"], []
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.startswith("|")]
    header_index = next(
        (index for index, line in enumerate(lines) if _cells(line)[:1] == ["ID"]), None
    )
    if header_index is None:
        return ["traceability matrix has no 'ID' header row"], []
    header = _cells(lines[header_index])
    if len(header) != len(REQUIRED_COLUMNS):
        return [
            "traceability matrix must have exactly twelve columns: "
            f"found {len(header)} columns {header}"
        ], []
    # A column may extend its heading (for example "Original requirement (summary)");
    # the leading phrase must still match so downstream checks can rely on the names.
    for expected, actual in zip(REQUIRED_COLUMNS, header):
        if actual != expected and not actual.startswith(expected):
            return [
                f"traceability matrix column {actual!r} does not start with the required "
                f"heading {expected!r}"
            ], []
    normalized = list(REQUIRED_COLUMNS)

    rows: list[dict[str, str]] = []
    for line in lines[header_index + 2 :]:
        cells = _cells(line)
        if cells[:1] == ["ID"]:
            break
        if not cells or set(cells) == {"---"}:
            continue
        if len(cells) != len(header):
            if _is_status_summary_row(cells):
                break
            errors.append(
                f"matrix row has {len(cells)} columns, expected {len(header)}: {cells[0]}"
            )
            continue
        rows.append(dict(zip(normalized, cells)))
    if not rows:
        errors.append("traceability matrix has no requirement rows")
    return errors, rows


def _status_summary(text: str) -> dict[str, list[str]]:
    """Parse the two-column status summary that follows the traceability matrix."""
    summary: dict[str, list[str]] = {}
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = _cells(line)
        if len(cells) == 2 and cells[0] in ALLOWED_STATUSES:
            summary[cells[0]] = (
                [] if cells[1].lower() == "none" else [item.strip() for item in cells[1].split(",")]
            )
    return summary


def _check_status_summary(
    matrix_path: Path, rows: list[dict[str, str]], counts: Counter
) -> list[str]:
    """Return errors when the documented status summary disagrees with the rows."""
    summary = _status_summary(matrix_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    for status in ALLOWED_STATUSES:
        if status not in summary:
            errors.append(f"status summary is missing a row for {status!r}")
            continue
        expected = sorted(row["ID"] for row in rows if row["Current status"] == status)
        actual = sorted(summary[status])
        if actual != expected:
            errors.append(
                f"status summary for {status!r} lists {actual} but the matrix rows are {expected}"
            )
        if len(actual) != counts.get(status, 0):
            errors.append(
                f"status summary for {status!r} lists {len(actual)} rows but the matrix has "
                f"{counts.get(status, 0)}"
            )
    return errors


def check_matrix(matrix_path: Path = MATRIX_PATH) -> tuple[list[str], Counter]:
    """Validate the matrix structure, IDs, statuses and summary; return errors and counts."""
    errors, rows = parse_matrix(matrix_path)
    if errors:
        return errors, Counter()

    ids = [row["ID"] for row in rows]
    duplicates = sorted({seen for seen in ids if ids.count(seen) > 1})
    if duplicates:
        errors.append(f"duplicate requirement IDs: {', '.join(duplicates)}")
    missing = [expected for expected in EXPECTED_IDS if expected not in set(ids)]
    if missing:
        errors.append(f"requirement IDs missing from the matrix: {', '.join(missing)}")
    unexpected = sorted(set(ids) - set(EXPECTED_IDS))
    if unexpected:
        errors.append(f"unexpected requirement IDs outside the documented namespaces: {unexpected}")

    counts: Counter = Counter()
    for row in rows:
        for column in ("Acceptance criterion", "Required tests or evidence", "Current status"):
            if not row[column]:
                errors.append(f"{row['ID']}: empty {column.lower()}")
        status = row["Current status"]
        if status not in ALLOWED_STATUSES:
            errors.append(f"{row['ID']}: status {status!r} is outside the allowed vocabulary")
        else:
            counts[status] += 1
        if not row["Dependency or external blocker"]:
            errors.append(f"{row['ID']}: empty dependency/blocker column (write 'None' when clear)")
        if not row["Original requirement"]:
            errors.append(f"{row['ID']}: empty requirement description")
    errors.extend(_check_status_summary(matrix_path, rows, counts))
    return errors, counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()

    link_errors, checked = check_links(root, markdown_files(root))
    matrix_errors, counts = check_matrix(root / MATRIX_PATH)
    errors = link_errors + matrix_errors

    print(f"Checked {checked} relative Markdown links across the repository.")
    if counts:
        print("Requirement status counts from the matrix:")
        total = sum(counts.values())
        for status in ALLOWED_STATUSES:
            print(f"  {status}: {counts.get(status, 0)}")
        print(f"  TOTAL: {total}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("OK: documentation links, requirement IDs and matrix rows are valid.")
    print("Note: this checks documentation structure only, not implementation evidence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
