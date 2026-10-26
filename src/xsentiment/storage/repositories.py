"""Idempotent persistence and database joins for price bars and X posts.

The join is deliberately split in two:

* :func:`daily_post_price_join` is a descriptive SQL join by UTC event date. Its
  same-day close would not be known at that day's forecast cutoff, so it must not
  feed a point-in-time model.
* :func:`cutoff_post_price_join` joins only posts published and first observed by a
  cutoff to the last completed price bar before that cutoff. This is the leakage-safe
  shape required by the forecast contract.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)

from xsentiment.ingestion.contracts import XPostRecord
from xsentiment.ingestion.prices import PriceCandle
from xsentiment.storage.models import Base, PriceBar, XPost


@dataclass(frozen=True, slots=True)
class DailyPostPriceRow:
    """Descriptive post aggregate joined to the same UTC day's price bar."""

    event_date: date
    post_count: int
    scored_post_count: int
    mean_sentiment: float | None
    close: Decimal


@dataclass(frozen=True, slots=True)
class CutoffPostPriceRow:
    """Leakage-safe aggregate at a UTC cutoff plus the last completed close."""

    cutoff: datetime
    previous_close: Decimal
    post_count: int
    scored_post_count: int
    mean_sentiment: float | None


async def create_schema(engine: AsyncEngine) -> None:
    """Create the versioned storage tables if they do not exist."""
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def upsert_price_bars(
    session: AsyncSession,
    candles: Sequence[PriceCandle],
    *,
    source_name: str = "coinbase_exchange",
    source_snapshot_id: str | None = None,
) -> int:
    """Insert or update bars keyed by ``(product_id, timestamp)``.

    Returns the number of distinct input rows processed. Repeating the same call
    leaves the table unchanged in row count.
    """
    ingested_at = datetime.now(UTC)
    for candle in candles:
        timestamp = _as_utc(candle.timestamp)
        values = {
            "bar_date": timestamp.date(),
            "open": candle.open,
            "high": candle.high,
            "low": candle.low,
            "close": candle.close,
            "volume": candle.volume,
            "source_name": source_name,
            "source_snapshot_id": source_snapshot_id,
            "ingested_at": ingested_at,
        }
        existing = await session.get(PriceBar, (candle.product_id, timestamp))
        if existing is None:
            session.add(PriceBar(product_id=candle.product_id, timestamp=timestamp, **values))
        else:
            for field, value in values.items():
                setattr(existing, field, value)
    await session.flush()
    return len({(candle.product_id, _as_utc(candle.timestamp)) for candle in candles})


async def upsert_posts(
    session: AsyncSession,
    posts: Sequence[XPostRecord],
    *,
    source_snapshot_id: str | None = None,
) -> int:
    """Insert or update normalized posts keyed by their stable source ID.

    ``retrieved_at`` keeps the earliest observation for a post so a later snapshot
    cannot backdate availability. Repeating the same call is idempotent.
    """
    ingested_at = datetime.now(UTC)
    for post in posts:
        created_at = _as_utc(post.created_at)
        retrieved_at = _as_utc(post.retrieved_at)
        existing = await session.get(XPost, post.post_id)
        if existing is None:
            session.add(
                XPost(
                    post_id=post.post_id,
                    created_at=created_at,
                    created_date=created_at.date(),
                    retrieved_at=retrieved_at,
                    text=post.text,
                    sentiment_score=post.sentiment_score,
                    likes=post.likes,
                    reposts=post.reposts,
                    views=post.views,
                    author_followers=post.author_followers,
                    provenance_url=post.provenance_url,
                    source_name=post.source_name,
                    source_platform=post.source_platform,
                    source_created_at_raw=post.source_created_at_raw,
                    source_utc_offset=post.source_utc_offset,
                    author_id=post.author_id,
                    query_mode=post.query_mode,
                    query=post.query,
                    source_record_hash=post.source_record_hash,
                    schema_version=post.schema_version,
                    warnings=list(post.warnings),
                    source_snapshot_id=source_snapshot_id,
                    ingested_at=ingested_at,
                )
            )
            continue
        existing.retrieved_at = min(_stored_utc(existing.retrieved_at), retrieved_at)
        existing.text = post.text
        existing.sentiment_score = post.sentiment_score
        existing.likes = post.likes
        existing.reposts = post.reposts
        existing.views = post.views
        existing.author_followers = post.author_followers
        existing.provenance_url = post.provenance_url
        existing.source_name = post.source_name
        existing.source_platform = post.source_platform
        existing.source_created_at_raw = post.source_created_at_raw
        existing.source_utc_offset = post.source_utc_offset
        existing.author_id = post.author_id
        existing.query_mode = post.query_mode
        existing.query = post.query
        existing.source_record_hash = post.source_record_hash
        existing.schema_version = post.schema_version
        existing.warnings = list(post.warnings)
        existing.source_snapshot_id = source_snapshot_id
        existing.ingested_at = ingested_at
    await session.flush()
    return len({post.post_id for post in posts})


async def daily_post_price_join(
    session: AsyncSession,
    *,
    product_id: str,
    start: date,
    end: date,
) -> list[DailyPostPriceRow]:
    """Descriptive SQL join of post aggregates to the same UTC event day's bar.

    This is a reporting join only. The same-day close is not available at that UTC
    day's forecast cutoff, so it must never be used as a historical model feature.
    """
    post_aggregates = (
        select(
            XPost.created_date.label("event_date"),
            func.count(XPost.post_id).label("post_count"),
            func.count(XPost.sentiment_score).label("scored_post_count"),
            func.avg(XPost.sentiment_score).label("mean_sentiment"),
        )
        .where(XPost.created_date >= start, XPost.created_date <= end)
        .group_by(XPost.created_date)
        .subquery()
    )
    statement = (
        select(
            post_aggregates.c.event_date,
            post_aggregates.c.post_count,
            post_aggregates.c.scored_post_count,
            post_aggregates.c.mean_sentiment,
            PriceBar.close,
        )
        .select_from(post_aggregates)
        .join(
            PriceBar,
            (PriceBar.bar_date == post_aggregates.c.event_date)
            & (PriceBar.product_id == product_id),
        )
        .order_by(post_aggregates.c.event_date)
    )
    rows = (await session.execute(statement)).all()
    return [
        DailyPostPriceRow(
            event_date=row[0],
            post_count=int(row[1]),
            scored_post_count=int(row[2]),
            mean_sentiment=float(row[3]) if row[3] is not None else None,
            close=Decimal(row[4]),
        )
        for row in rows
    ]


async def cutoff_post_price_join(
    session: AsyncSession,
    *,
    product_id: str,
    start: date,
    end: date,
) -> list[CutoffPostPriceRow]:
    """Join eligible posts to the last completed bar before each UTC cutoff.

    A post is eligible only when ``created_at`` is in ``(cutoff - 24h, cutoff]`` and
    ``retrieved_at <= cutoff``. The joined close belongs to the previous completed
    bar, never the bar whose close is the n+0 target.
    """
    if start > end:
        raise ValueError("start must not be later than end")
    bars = (
        await session.execute(
            select(PriceBar)
            .where(
                PriceBar.product_id == product_id,
                PriceBar.bar_date <= end,
            )
            .order_by(PriceBar.bar_date)
        )
    ).scalars().all()
    rows: list[CutoffPostPriceRow] = []
    previous: PriceBar | None = None
    for bar in bars:
        if previous is not None and start <= bar.bar_date <= end:
            cutoff = datetime.combine(bar.bar_date, time.min, tzinfo=UTC)
            aggregate = (
                await session.execute(
                    select(
                        func.count(XPost.post_id),
                        func.count(XPost.sentiment_score),
                        func.avg(XPost.sentiment_score),
                    ).where(
                        XPost.created_at > cutoff - timedelta(days=1),
                        XPost.created_at <= cutoff,
                        XPost.retrieved_at <= cutoff,
                    )
                )
            ).one()
            rows.append(
                CutoffPostPriceRow(
                    cutoff=cutoff,
                    previous_close=Decimal(previous.close),
                    post_count=int(aggregate[0]),
                    scored_post_count=int(aggregate[1]),
                    mean_sentiment=float(aggregate[2]) if aggregate[2] is not None else None,
                )
            )
        previous = bar
    return rows


def session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Build an ``expire_on_commit=False`` session factory for unit-of-work use."""
    return async_sessionmaker(engine, expire_on_commit=False)


async def storage_snapshot_ids(session: AsyncSession) -> list[str]:
    """Distinct non-null source snapshot IDs persisted across both tables."""
    price_ids = (
        await session.execute(
            select(PriceBar.source_snapshot_id)
            .where(PriceBar.source_snapshot_id.is_not(None))
            .distinct()
        )
    ).scalars().all()
    post_ids = (
        await session.execute(
            select(XPost.source_snapshot_id)
            .where(XPost.source_snapshot_id.is_not(None))
            .distinct()
        )
    ).scalars().all()
    return sorted({str(value) for value in (*price_ids, *post_ids)})


async def load_price_candles(
    session: AsyncSession,
    *,
    product_id: str,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[PriceCandle]:
    """Read persisted daily bars back as validated :class:`PriceCandle` values.

    Reconstruction re-runs the ``PriceCandle`` validation, so a malformed row fails
    closed instead of silently feeding the pipeline. Rows are ordered by candle start.
    """
    statement = (
        select(PriceBar)
        .where(PriceBar.product_id == product_id)
        .order_by(PriceBar.timestamp)
    )
    if start_date is not None:
        statement = statement.where(PriceBar.bar_date >= start_date)
    if end_date is not None:
        statement = statement.where(PriceBar.bar_date <= end_date)
    bars = (await session.execute(statement)).scalars().all()
    return [
        PriceCandle(
            product_id=bar.product_id,
            timestamp=_stored_utc(bar.timestamp),
            low=Decimal(str(bar.low)),
            high=Decimal(str(bar.high)),
            open=Decimal(str(bar.open)),
            close=Decimal(str(bar.close)),
            volume=Decimal(str(bar.volume)),
        )
        for bar in bars
    ]


async def load_posts(
    session: AsyncSession,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[XPostRecord]:
    """Read persisted posts back as normalized :class:`XPostRecord` values.

    Records are ordered by event time then post ID for deterministic runs. All
    provenance fields round-trip; raw text stays inside the locally owned database.
    """
    statement = select(XPost).order_by(XPost.created_at, XPost.post_id)
    if start_date is not None:
        statement = statement.where(XPost.created_date >= start_date)
    if end_date is not None:
        statement = statement.where(XPost.created_date <= end_date)
    rows = (await session.execute(statement)).scalars().all()
    return [_post_record_from_row(row) for row in rows]


def _post_record_from_row(row: XPost) -> XPostRecord:
    warnings_value = row.warnings or []
    sentiment = row.sentiment_score
    return XPostRecord(
        post_id=row.post_id,
        # SQLite returns naive datetimes; stored values are UTC by contract, so
        # re-tag them instead of passing naive values on to the strict contract.
        created_at=_stored_utc(row.created_at),
        retrieved_at=_stored_utc(row.retrieved_at),
        text=row.text,
        sentiment_score=float(sentiment) if sentiment is not None else None,
        likes=row.likes,
        reposts=row.reposts,
        views=row.views,
        author_followers=row.author_followers,
        provenance_url=row.provenance_url,
        source_name=row.source_name,
        source_platform=row.source_platform,
        source_created_at_raw=row.source_created_at_raw,
        source_utc_offset=row.source_utc_offset,
        author_id=row.author_id,
        query_mode=row.query_mode,
        query=row.query,
        source_record_hash=row.source_record_hash,
        schema_version=row.schema_version,
        warnings=tuple(warnings_value),
    )


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("persisted timestamps must be timezone-aware")
    return value.astimezone(UTC)


def _stored_utc(value: datetime) -> datetime:
    """SQLite returns naive datetimes; stored values are UTC by contract."""
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
