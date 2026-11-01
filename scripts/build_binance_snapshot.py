"""Build a checked BTCUSDT daily snapshot from official Binance Vision ZIP archives.

Archive ZIPs and matching .CHECKSUM sidecars are input-only and are not copied to
the repository. Timestamps in the downloaded 2026 files are microseconds since UTC.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import zipfile
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

ARCHIVE_NAME = re.compile(r"BTCUSDT-1d-2026-(?:0[5-9]|10)(?:-\d{2})?\.zip$")
LICENSE_URL = "https://github.com/binance/binance-public-data/blob/master/TERMS_AND_CONDITIONS.md"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _archives(directory: Path) -> list[Path]:
    files = sorted(
        path
        for path in directory.glob("BTCUSDT-1d-2026-*.zip")
        if ARCHIVE_NAME.fullmatch(path.name)
    )
    if not files:
        raise ValueError("no matching May-October 2026 BTCUSDT daily archives found")
    for path in files:
        sidecar = path.with_suffix(path.suffix + ".CHECKSUM")
        if not sidecar.is_file():
            raise ValueError(f"missing published checksum sidecar for {path.name}")
        expected = sidecar.read_text(encoding="utf-8").strip().split()[0]
        if not re.fullmatch(r"[0-9a-fA-F]{64}", expected) or _sha256(path) != expected.lower():
            raise ValueError(f"checksum mismatch for {path.name}")
    return files


def build_snapshot(directory: Path, start: date, end: date) -> dict[str, object]:
    """Parse archives, verify published checksums and require every UTC day in [start,end)."""
    if start >= end:
        raise ValueError("start must be earlier than end")
    archives = _archives(directory)
    start_at = datetime.combine(start, datetime.min.time(), UTC)
    end_at = datetime.combine(end, datetime.min.time(), UTC)
    candles: dict[datetime, dict[str, str]] = {}
    for archive in archives:
        with zipfile.ZipFile(archive) as bundle:
            csv_files = [name for name in bundle.namelist() if name.endswith(".csv")]
            if len(csv_files) != 1:
                raise ValueError(f"{archive.name} must contain exactly one CSV")
            reader = csv.reader(io.StringIO(bundle.read(csv_files[0]).decode("utf-8")))
            for values in reader:
                if len(values) < 6:
                    raise ValueError(f"{archive.name} contains a row with fewer than six fields")
                timestamp = datetime.fromtimestamp(int(values[0]) / 1_000_000, tz=UTC)
                if start_at <= timestamp < end_at:
                    if timestamp in candles:
                        raise ValueError(f"duplicate candle start {timestamp.isoformat()}")
                    candles[timestamp] = {
                        "product_id": "BTCUSDT",
                        "timestamp": timestamp.isoformat(),
                        "low": values[3],
                        "high": values[2],
                        "open": values[1],
                        "close": values[4],
                        "volume": values[5],
                    }
    expected_days = (end_at - start_at).days
    expected_timestamps = [start_at + timedelta(days=index) for index in range(expected_days)]
    if sorted(candles) != expected_timestamps:
        missing = sorted(set(expected_timestamps) - set(candles))
        raise ValueError(
            f"daily coverage incomplete: expected {expected_days}; missing {len(missing)}"
        )
    return {
        "product_id": "BTCUSDT",
        "granularity_seconds": 86400,
        "requested_start": start_at.isoformat(),
        "requested_end": end_at.isoformat(),
        "fetched_at": datetime.now(UTC).isoformat(),
        "fetch_mode": "binance_vision_public_archive",
        "venue": "Binance Spot",
        "quote_currency": "USDT",
        "timestamp_unit": "microseconds",
        "source_license": "CC BY-NC-SA 4.0",
        "source_license_url": LICENSE_URL,
        "source_archive_count": len(archives),
        "source_archive_sha256": {path.name: _sha256(path) for path in archives},
        "candles": [candles[stamp] for stamp in expected_timestamps],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archives-dir", type=Path, required=True)
    parser.add_argument("--start", type=date.fromisoformat, default=date(2026, 5, 5))
    parser.add_argument("--end", type=date.fromisoformat, default=date(2026, 11, 1))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    snapshot = build_snapshot(args.archives_dir, args.start, args.end)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {len(snapshot['candles'])} verified BTCUSDT candles to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
