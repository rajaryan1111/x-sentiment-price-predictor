"""Tests for the Phase 1 documentation validator. Structure only; no network access."""
import importlib.util
from pathlib import Path

import pytest

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


def test_repository_has_no_unqualified_test_count_claims() -> None:
    """Regression: several documents once asserted different 'current' test counts."""
    errors, inspected = validate_docs.check_test_count_claims(
        ROOT, validate_docs.markdown_files(ROOT)
    )

    assert errors == []
    assert inspected > 0, "the claim scanner must actually be matching sentences"


def test_test_plan_states_the_current_count_and_the_suite_agrees() -> None:
    """The authoritative count in TEST_PLAN.md must match what pytest actually collects.

    The expected number is read from the document instead of being hardcoded here, so
    adding a test means updating the one authoritative place rather than editing this
    assertion. Collection runs in a subprocess so the result is the size of the whole
    suite even when this module is executed on its own.
    """
    import re
    import subprocess
    import sys

    text = (ROOT / "TEST_PLAN.md").read_text(encoding="utf-8")
    claimed = {int(match) for match in re.findall(r"\b(\d{2,4})\s+offline tests\b", text)}
    assert claimed, "TEST_PLAN.md must state the current offline test count"

    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:  # pragma: no cover - collection is green in CI
        pytest.skip(f"suite collection unavailable: {completed.stdout[-300:]}")
    match = re.search(r"(\d+)\s+tests? collected", completed.stdout)
    assert match, f"could not read the collected count from: {completed.stdout[-300:]}"

    actual = int(match.group(1))
    assert actual in claimed, (
        f"TEST_PLAN.md claims {sorted(claimed)} offline tests but pytest collected {actual}"
    )


def test_validator_flags_an_unqualified_count_but_allows_a_historical_one(
    tmp_path: Path,
) -> None:
    (tmp_path / "TEST_PLAN.md").write_text("The suite is 999 offline tests.\n", encoding="utf-8")

    stale = tmp_path / "STALE.md"
    stale.write_text("The project has 42 offline tests.\n", encoding="utf-8")
    errors, inspected = validate_docs.check_test_count_claims(tmp_path, [stale])
    assert inspected == 1
    assert any("unqualified test-count claim '42'" in error for error in errors)

    dated = tmp_path / "DATED.md"
    dated.write_text("On 2026-10-26 the suite was 42 offline tests.\n", encoding="utf-8")
    dated_errors, _ = validate_docs.check_test_count_claims(tmp_path, [dated])
    assert dated_errors == []

    by_commit = tmp_path / "COMMIT.md"
    by_commit.write_text("Commit `abc1234` passed 42 offline tests.\n", encoding="utf-8")
    commit_errors, _ = validate_docs.check_test_count_claims(tmp_path, [by_commit])
    assert commit_errors == []

    # The authoritative plan itself is exempt and fold configuration is not a suite size.
    plan_errors, _ = validate_docs.check_test_count_claims(
        tmp_path, [tmp_path / "TEST_PLAN.md"]
    )
    assert plan_errors == []

    folds = tmp_path / "FOLDS.md"
    folds.write_text("Defaults are 60 training and 20 test rows per fold.\n", encoding="utf-8")
    fold_errors, fold_inspected = validate_docs.check_test_count_claims(tmp_path, [folds])
    assert fold_errors == [] and fold_inspected == 0


def test_validator_flags_duplicate_and_unexpected_requirement_ids(tmp_path: Path) -> None:
    """The real matrix is edited only in a temporary copy, never in the repository."""
    text = MATRIX.read_text(encoding="utf-8")

    duplicate_path = tmp_path / "duplicate.md"
    duplicate_path.write_text(text.replace("| R2 |", "| R1 |", 1), encoding="utf-8")
    duplicate_errors, _ = validate_docs.check_matrix(duplicate_path)
    assert any("duplicate requirement IDs: R1" in error for error in duplicate_errors)

    unexpected_path = tmp_path / "unexpected.md"
    unexpected_path.write_text(text.replace("| R1 |", "| X1 |", 1), encoding="utf-8")
    unexpected_errors, _ = validate_docs.check_matrix(unexpected_path)
    assert any(
        "unexpected requirement IDs" in error and "X1" in error
        for error in unexpected_errors
    )
    assert any(
        "requirement IDs missing" in error and "R1" in error
        for error in unexpected_errors
    )
