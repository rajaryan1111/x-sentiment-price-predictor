"""Persisted price bars and normalized X posts for the required database join.

The schema deliberately keeps event time separate from first-observed time. A post
may only join a forecast cutoff when both its event time and retrieval time are at
or before that cutoff. Raw post text belongs in a local, ignored database, never in
Git or committed artefacts.
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Date,
    DateTime,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base for this repository's own models (not copied from GraphOne)."""


class PriceBar(Base):
    """A validated UTC daily candle, keyed by product and candle-start time."""

    __tablename__ = "price_bars"
    __table_args__ = (
        UniqueConstraint("product_id", "timestamp", name="uq_price_bars_product_timestamp"),
        UniqueConstraint("product_id", "bar_date", name="uq_price_bars_product_date"),
    )

    product_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    bar_date: Mapped[date] = mapped_column(Date, nullable=False)
    open: Mapped[Decimal] = mapped_column(Numeric(24, 8), nullable=False)
    high: Mapped[Decimal] = mapped_column(Numeric(24, 8), nullable=False)
    low: Mapped[Decimal] = mapped_column(Numeric(24, 8), nullable=False)
    close: Mapped[Decimal] = mapped_column(Numeric(24, 8), nullable=False)
    volume: Mapped[Decimal] = mapped_column(Numeric(30, 8), nullable=False)
    source_name: Mapped[str] = mapped_column(String(64), nullable=False)
    source_snapshot_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class XPost(Base):
    """A normalized X post preserving provenance and nullable engagement fields."""

    __tablename__ = "x_posts"
    __table_args__ = (Index("ix_x_posts_created_date", "created_date"),)

    post_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_date: Mapped[date] = mapped_column(Date, nullable=False)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    sentiment_score: Mapped[float | None] = mapped_column(Numeric(7, 6), nullable=True)
    likes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reposts: Mapped[int | None] = mapped_column(Integer, nullable=True)
    views: Mapped[int | None] = mapped_column(Integer, nullable=True)
    author_followers: Mapped[int | None] = mapped_column(Integer, nullable=True)
    provenance_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    source_name: Mapped[str] = mapped_column(String(64), nullable=False)
    source_platform: Mapped[str] = mapped_column(String(32), nullable=False)
    source_created_at_raw: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source_utc_offset: Mapped[str | None] = mapped_column(String(16), nullable=True)
    author_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    query_mode: Mapped[str | None] = mapped_column(String(16), nullable=True)
    query: Mapped[str | None] = mapped_column(String(512), nullable=True)
    source_record_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    schema_version: Mapped[str] = mapped_column(String(32), nullable=False)
    warnings: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    source_snapshot_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
