from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from xsentiment.ingestion.contracts import XPostRecord
from xsentiment.ingestion.prices import PriceCandle
from xsentiment.storage.models import PriceBar, XPost
from xsentiment.storage.repositories import (
    create_schema,
    cutoff_post_price_join,
    daily_post_price_join,
    upsert_posts,
    upsert_price_bars,
)


def candle(day: int, close: str) -> PriceCandle:
    value = Decimal(close)
    return PriceCandle(
        "BTC-USD",
        datetime(2026, 10, day, tzinfo=UTC),
        value - Decimal("1"),
        value + Decimal("1"),
        value,
        value,
        Decimal("10"),
    )


def at(day: int, hour: int = 0) -> datetime:
    return datetime(2026, 10, day, hour, tzinfo=UTC)


def post(
    post_id: str,
    created: datetime,
    retrieved: datetime,
    score: float | None = 0.5,
) -> XPostRecord:
    return XPostRecord(
        post_id=post_id,
        created_at=created,
        retrieved_at=retrieved,
        text=f"post {post_id}",
        sentiment_score=score,
        likes=4,
    )


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    await create_schema(engine)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as db:
        yield db
    await engine.dispose()


@pytest.mark.asyncio
async def test_price_upsert_is_idempotent_and_keeps_one_row_per_day(session) -> None:
    bars = [candle(20, "100"), candle(21, "110")]

    assert await upsert_price_bars(session, bars, source_snapshot_id="snapshot-1") == 2
    assert await upsert_price_bars(session, bars, source_snapshot_id="snapshot-1") == 2
    await session.commit()

    count = await session.scalar(select(func.count()).select_from(PriceBar))
    assert count == 2


@pytest.mark.asyncio
async def test_post_upsert_is_idempotent_and_keeps_earliest_observation(session) -> None:
    created = datetime(2026, 10, 20, 12, tzinfo=UTC)
    first = post("p1", created, created + timedelta(minutes=5), 0.8)
    assert await upsert_posts(session, [first], source_snapshot_id="snapshot-1") == 1
    assert await upsert_posts(session, [first], source_snapshot_id="snapshot-1") == 1

    later = post("p1", created, created + timedelta(minutes=30), -0.8)
    await upsert_posts(session, [later], source_snapshot_id="snapshot-2")
    await session.commit()

    count = await session.scalar(select(func.count()).select_from(XPost))
    stored = await session.get(XPost, "p1")
    assert count == 1
    assert stored is not None
    assert stored.retrieved_at.replace(tzinfo=UTC) == datetime(2026, 10, 20, 12, 5, tzinfo=UTC)
    assert float(stored.sentiment_score) == pytest.approx(-0.8)


@pytest.mark.asyncio
async def test_daily_join_is_a_descriptive_same_day_join(session) -> None:
    await upsert_price_bars(session, [candle(20, "100"), candle(21, "110"), candle(22, "120")])
    await upsert_posts(
        session,
        [
            post("a", at(20, 1), at(20, 2), 1.0),
            post("b", at(20, 3), at(20, 4), -1.0),
            post("c", at(21, 5), at(21, 6), None),
            post("outside", at(23, 5), at(23, 6), 0.0),
        ],
    )
    await session.commit()

    rows = await daily_post_price_join(
        session, product_id="BTC-USD", start=date(2026, 10, 20), end=date(2026, 10, 22)
    )

    assert [row.event_date for row in rows] == [date(2026, 10, 20), date(2026, 10, 21)]
    assert rows[0].post_count == 2
    assert rows[0].scored_post_count == 2
    assert rows[0].mean_sentiment == pytest.approx(0.0)
    assert rows[0].close == Decimal("100")
    assert rows[1].post_count == 1
    assert rows[1].scored_post_count == 0
    assert rows[1].mean_sentiment is None


@pytest.mark.asyncio
async def test_cutoff_join_uses_prior_close_and_excludes_late_or_future_posts(session) -> None:
    await upsert_price_bars(
        session,
        [candle(19, "90"), candle(20, "100"), candle(21, "110"), candle(22, "120")],
    )
    await upsert_posts(
        session,
        [
            post("available", at(20, 12), at(20, 13), 0.5),
            post("late", at(20, 12), at(21, 1), -1.0),
            post("future", at(22, 1), at(22, 2), -1.0),
        ],
    )
    await session.commit()

    rows = await cutoff_post_price_join(
        session, product_id="BTC-USD", start=date(2026, 10, 21), end=date(2026, 10, 22)
    )

    assert len(rows) == 2
    first, second = rows
    assert first.cutoff == datetime(2026, 10, 21, tzinfo=UTC)
    assert first.previous_close == Decimal("100")
    assert first.post_count == 1
    assert first.mean_sentiment == pytest.approx(0.5)
    assert second.cutoff == datetime(2026, 10, 22, tzinfo=UTC)
    assert second.previous_close == Decimal("110")
    assert second.post_count == 0
    assert second.mean_sentiment is None
