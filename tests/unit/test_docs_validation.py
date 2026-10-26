"""Tests for the Phase 1 documentation validator. Structure only; no network access."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MATRIX = ROOT / "docs" / "REQUIREMENTS_TRACEABILITY.md"


def _load_validator():
    spec = importlib.util.spec_from_file_location(
        "validate_docs", ROOT / "scripts" / "validate_docs.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validate_docs = _load_validator()


def _summary_rows(text: str) -> dict[str, list[str]]:
    summary: dict[str, list[str]] = {}
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) == 2 and cells[0] in validate_docs.ALLOWED_STATUSES:
            summary[cells[0]] = [] if cells[1].lower() == "none" else [
                item.strip() for item in cells[1].split(",")
            ]
    return summary


def test_every_relative_markdown_link_resolves() -> None:
    errors, checked = validate_docs.check_links(ROOT, validate_docs.markdown_files(ROOT))

    assert checked > 20
    assert errors == []


def test_traceability_matrix_is_structurally_complete() -> None:
    errors, counts = validate_docs.check_matrix(MATRIX)

    assert errors == []
    assert set(counts) <= set(validate_docs.ALLOWED_STATUSES)
    assert sum(counts.values()) == len(validate_docs.EXPECTED_IDS)


def test_matrix_covers_every_expected_requirement_id_once() -> None:
    _, rows = validate_docs.parse_matrix(MATRIX)
    ids = [row["ID"] for row in rows]

    assert sorted(ids) == sorted(validate_docs.EXPECTED_IDS)


def test_documented_status_summary_matches_the_matrix_rows() -> None:
    errors, counts = validate_docs.check_matrix(MATRIX)
    assert errors == []
    summary = _summary_rows(MATRIX.read_text(encoding="utf-8"))

    for status in validate_docs.ALLOWED_STATUSES:
        assert status in summary, f"status summary is missing a row for {status}"
        assert len(summary[status]) == counts.get(status, 0), (
            f"{status}: summary lists {len(summary[status])} rows but the matrix has "
            f"{counts.get(status, 0)}"
        )
    assert sum(len(ids) for ids in summary.values()) == len(validate_docs.EXPECTED_IDS)


def test_validator_flags_a_broken_link_and_a_bad_status(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (tmp_path / "real.md").write_text("# real\n", encoding="utf-8")
    linked = tmp_path / "linked.md"
    linked.write_text("[ok](real.md)\n[bad](missing.md)\n", encoding="utf-8")

    errors, checked = validate_docs.check_links(tmp_path, [linked])

    assert checked == 2
    assert any("missing.md" in error for error in errors)

    header = "| " + " | ".join(validate_docs.REQUIRED_COLUMNS) + " |"
    separator = "| " + " | ".join("---" for _ in validate_docs.REQUIRED_COLUMNS) + " |"
    row = "| R1 | req | src | Must | ac | doc | path | ev | Almost done | none | fix | none |"
    matrix = docs / "REQUIREMENTS_TRACEABILITY.md"
    matrix.write_text("\n".join([header, separator, row]) + "\n", encoding="utf-8")

    matrix_errors, _ = validate_docs.check_matrix(matrix)

    assert any("outside the allowed vocabulary" in error for error in matrix_errors)
    assert any("requirement IDs missing" in error for error in matrix_errors)
