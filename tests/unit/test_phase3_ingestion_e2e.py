"""End-to-end bounded X ingestion, offline from an explicitly mocked actor response.

No live Apify request is made: the adapter receives a mocked transport typical of
the documented ``data`` envelope. The records then flow through persistence and
the leakage-safe cutoff join, so the "bounded end-to-end X ingestion" acceptance
item is exercised without a paid provider run. The posts are a mock fixture —
evidence of wiring only, not evidence that a real X corpus was accepted.
"""

import asyncio
import json
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import httpx
import pytest
import pytest_asyncio
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import create_async_engine

from xsentiment.config.settings import Settings
from xsentiment.ingestion.apify_x import ApifyXAdapter
from xsentiment.ingestion.contracts import XPostRecord
from xsentiment.ingestion.prices import PriceCandle
from xsentiment.main import main
from xsentiment.storage import repositories

ACTOR_INPUT = {"searchTerms": ["BTC"]}
MOCK_RETRIEVED = datetime(2026, 10, 20, 23, 0, tzinfo=UTC)


def _in_window(records: list[XPostRecord]) -> list[XPostRecord]:
    """Test-only manipulation of a synthetic fixture.

    Bring records' retrieval time inside the window (never before their own
    creation, contract-checked) so the eligible-post rule has positive cases. A
    record keeping out-of-window retrieval stays excluded by the cutoff join.
    """
    return [
        record
        if record.post_id == "k1-late"
        else replace(
            record,
            retrieved_at=max(
                MOCK_RETRIEVED, record.created_at + timedelta(minutes=1)
            ),
        )
        for record in records
    ]



def _settings() -> Settings:
    return Settings(
        apify_api_token=SecretStr("mock-not-real"),
        apify_actor_id="mock~not-a-real-actor",
        http_timeout_seconds=2,
    )


def _handler(items: list[dict]):
    """Launch, poll and dataset responses typical of the documented envelope."""

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if request.method == "POST" and "/actors/" in path:
            return httpx.Response(
                201,
                json={
                    "data": {
                        "id": "run-e2e",
                        "status": "SUCCEEDED",
                        "exitCode": 0,
                        "defaultDatasetId": "ds-e2e",
                    }
                },
            )
        if request.method == "GET" and "/datasets/" in path:
            return httpx.Response(200, json=items)
        return httpx.Response(404)

    return handler


@pytest_asyncio.fixture
async def fetched_records() -> list[XPostRecord]:
    """One bounded run per documented query mode: keyword, ticker and cashtag."""
    families = {
        "keyword": (
            "Bitcoin after:2026-04-29 before:2026-10-26",
            [
                {
                    "id": "k1",
                    "text": "Bitcoin looks strong today",
                    "createdAt": "2026-10-20T10:00:00.000Z",
                    "author": {"id": "a1", "followers_count": 100},
                }
            ],
        ),
        "ticker": (
            "BTC",
            [
                {
                    "id": "t1",
                    "text": "BTC momentum",
                    "createdAt": "2026-10-21T08:00:00-05:00",
                    "likeCount": 3,
                }
            ],
        ),
        "cashtag": (
            "$BTC",
            [
                {
                    "id": "c1",
                    "text": "$BTC consolidating",
                    "createdAt": "2026-10-22T09:00:00Z",
                    "author": {"followers_count": 42},
                },
                {
                    "id": "k1-late",
                    "text": "Bitcoin duplicate",
                    "createdAt": "2026-10-20T11:00:00Z",
                },
            ],
        ),
    }
    records: list[XPostRecord] = []
    for mode, (query, items) in families.items():
        transport = httpx.MockTransport(_handler(items))
        async with httpx.AsyncClient(transport=transport) as client:
            async with ApifyXAdapter(settings=_settings(), client=client) as adapter:
                records.extend(
                    await adapter.run_and_fetch(
                        ACTOR_INPUT,
                        max_items=10,
                        max_total_charge_usd=1.0,
                        timeout_seconds=60,
                        query_mode=mode,
                        query=query,
                    )
                )
    return records


def _window_candles(start: date, days: int) -> list[PriceCandle]:
    """Synthetic BTC-USD daily bars with deterministic closes (unit-test only)."""
    return [
        PriceCandle(
            product_id="BTC-USD",
            timestamp=datetime(start.year, start.month, start.day, tzinfo=UTC)
            + timedelta(days=index),
            low=Decimal(100 + index),
            high=Decimal(102 + index),
            open=Decimal(101 + index),
            close=Decimal(101 + index),
            volume=Decimal("1"),
        )
        for index in range(days)
    ]


@pytest.mark.asyncio
async def test_bounded_end_to_end_ingestion_persists_and_joins(
    tmp_path: Path, fetched_records: list[XPostRecord]
) -> None:
    """Adapter output -> provenance-preserving persistence -> leakage-safe cutoff join."""
    assert {record.post_id for record in fetched_records} == {"k1", "t1", "c1", "k1-late"}
    assert {record.query_mode for record in fetched_records} == {"keyword", "ticker", "cashtag"}
    non_utc = next(record for record in fetched_records if record.post_id == "t1")
    assert non_utc.created_at == datetime(2026, 10, 21, 13, 0, tzinfo=UTC)

    # Test-only manipulation of a synthetic fixture: see _in_window; the
    # "k1-late" record keeps its real adapter-stamped retrieval time and must be
    # excluded by every cutoff join as unavailable at its own timestamp.
    adjusted = _in_window(fetched_records)

    candles = _window_candles(date(2026, 10, 19), 3)
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'e2e.db'}")
    try:
        await repositories.create_schema(engine)
        async with repositories.session_factory(engine)() as session:
            price_rows = await repositories.upsert_price_bars(
                session, candles, source_snapshot_id="mock-snapshot"
            )
            post_rows = await repositories.upsert_posts(
                session, adjusted, source_snapshot_id="mock-actor-ds-e2e"
            )
            await session.commit()

        async with repositories.session_factory(engine)() as session:
            stored_candles = await repositories.load_price_candles(
                session, product_id="BTC-USD"
            )
            assert [candle.timestamp.date() for candle in stored_candles] == [
                date(2026, 10, 19),
                date(2026, 10, 20),
                date(2026, 10, 21),
            ]
            posts = await repositories.load_posts(session)
            assert {post.post_id for post in posts} == {"k1", "t1", "c1", "k1-late"}
            assert await repositories.storage_snapshot_ids(session) == [
                "mock-actor-ds-e2e",
                "mock-snapshot",
            ]

            rows = await repositories.cutoff_post_price_join(
                session, product_id="BTC-USD", start=date(2026, 10, 21), end=date(2026, 10, 21)
            )
    finally:
        await engine.dispose()

    assert price_rows == 3 and post_rows == 4
    first = rows[0]
    assert first.cutoff == datetime(2026, 10, 21, tzinfo=UTC)
    assert first.previous_close == Decimal("102")  # close of the 2026-10-20 bar
    assert first.post_count == 1  # only "k1" published and first observed by the cutoff
    assert first.mean_sentiment is None  # sentiment comes from the model, not the store


def test_run_cli_consumes_the_persisted_inputs(tmp_path: Path) -> None:
    """The run CLI finishes on rows loaded straight out of the persisted storage.

    Posts are built directly (the adapter path is covered by the first test) and
    the CLI's internal ``asyncio.run`` needs a sync test scope.
    """
    adjusted = [
        XPostRecord(
            post_id="p1",
            created_at=datetime(2026, 10, 20, 10, 0, tzinfo=UTC),
            retrieved_at=datetime(2026, 10, 20, 23, 0, tzinfo=UTC),
            text="Bitcoin looks strong today",
            query_mode="keyword",
            query="Bitcoin",
        ),
        XPostRecord(
            post_id="p2",
            created_at=datetime(2026, 10, 21, 10, 0, tzinfo=UTC),
            retrieved_at=datetime(2026, 10, 21, 23, 0, tzinfo=UTC),
            text="BTC momentum",
            query_mode="ticker",
            query="BTC",
        ),
    ]

    candles = _window_candles(date(2026, 6, 25), 120)
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'e2e.db'}"

    async def populate() -> None:
        engine = create_async_engine(database_url)
        try:
            await repositories.create_schema(engine)
            async with repositories.session_factory(engine)() as session:
                await repositories.upsert_price_bars(
                    session, candles, source_snapshot_id="mock-snapshot"
                )
                await repositories.upsert_posts(session, adjusted, source_snapshot_id="mock")
                await session.commit()
        finally:
            await engine.dispose()

    asyncio.run(populate())

    out = tmp_path / "run"
    exit_code = main(
        [
            "run",
            "--database-url",
            database_url,
            "--out",
            str(out),
            "--now",
            datetime(2026, 10, 24, tzinfo=UTC).isoformat(),
        ]
    )
    assert exit_code == 0, "run on persisted inputs must succeed"
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    provenance = manifest.get("provenance") or manifest
    assert provenance.get("input_source") == "persisted_storage"
    assert provenance.get("posts_supplied") == 2
    assert (out / "evaluation-report.md").exists()
    assert (out / "sentiment-vs-price.svg").exists()
    metrics = json.loads((out / "metrics.json").read_text(encoding="utf-8"))
    assert set(metrics["mean_mae_by_model"]) == {"naive", "price_only", "sentiment_price"}
