"""Archive ingestion checks; fixture rows are synthetic and never report data."""
from __future__ import annotations

import hashlib
import importlib.util
import zipfile
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "build_binance_snapshot.py"
_SPEC = importlib.util.spec_from_file_location("build_binance_snapshot", _SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
build_snapshot = _MODULE.build_snapshot


def _archive(directory: Path, day: datetime, *, checksum_ok: bool = True) -> None:
    name = f"BTCUSDT-1d-2026-05-{day.day:02d}.zip"
    csv = (
        f"{int(day.timestamp() * 1_000_000)},100,110,90,105,4,"
        f"{int((day + timedelta(days=1)).timestamp() * 1_000_000)-1},0,1,2,3,0\n"
    )
    path = directory / name
    with zipfile.ZipFile(path, "w") as bundle:
        bundle.writestr(name.removesuffix(".zip") + ".csv", csv)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if not checksum_ok:
        digest = "0" * 64
    path.with_suffix(path.suffix + ".CHECKSUM").write_text(f"{digest}  {name}\n")


def test_binance_snapshot_verifies_checksum_and_daily_coverage(tmp_path: Path) -> None:
    start = datetime(2026, 5, 5, tzinfo=UTC)
    _archive(tmp_path, start)
    _archive(tmp_path, start + timedelta(days=1))

    snapshot = build_snapshot(tmp_path, date(2026, 5, 5), date(2026, 5, 7))

    assert snapshot["product_id"] == "BTCUSDT"
    assert snapshot["quote_currency"] == "USDT"
    assert len(snapshot["candles"]) == 2
    assert snapshot["candles"][0]["timestamp"] == "2026-05-05T00:00:00+00:00"


def test_binance_snapshot_rejects_checksum_mismatch(tmp_path: Path) -> None:
    _archive(tmp_path, datetime(2026, 5, 5, tzinfo=UTC), checksum_ok=False)

    with pytest.raises(ValueError, match="checksum mismatch"):
        build_snapshot(tmp_path, date(2026, 5, 5), date(2026, 5, 6))


def test_binance_snapshot_rejects_missing_day(tmp_path: Path) -> None:
    _archive(tmp_path, datetime(2026, 5, 5, tzinfo=UTC))

    with pytest.raises(ValueError, match="coverage incomplete"):
        build_snapshot(tmp_path, date(2026, 5, 5), date(2026, 5, 7))
