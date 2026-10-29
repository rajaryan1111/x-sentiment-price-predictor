"""Deterministic, dependency-free SVG charts comparing sentiment and price.

Charts are rendered as plain SVG with no third-party plotting dependency, so the
report is reproducible inside the project's default test environment and the file
can be opened or diffed as text.

The sentiment panels draw *observed* scored sentiment: the trailing-24h mean
level and its day-over-day change (the R10 series). When no permitted scored
posts exist, each panel states that explicitly instead of drawing a fabricated
or zero-filled curve, which would misrepresent missing data as neutral
sentiment or as zero change.

The change series is defined as ``mean_sentiment_24h(T) - mean_sentiment_24h(T-1)``
for consecutive scored UTC cutoffs; it stays unavailable when either day is
unscored. It is reporting-only and is never a model feature.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from html import escape
from pathlib import Path

from xsentiment.features.dataset import SupervisedRow
from xsentiment.ingestion.prices import PriceCandle
from xsentiment.pipeline.phase2 import completed_candles

WIDTH = 980
PANEL_HEIGHT = 170
PANEL_GAP = 46
PADDING_LEFT = 84
PADDING_RIGHT = 26
PADDING_TOP = 64
PADDING_BOTTOM = 48
Y_TICKS = 4
X_TICKS = 6
PRICE_COLOR = "#1f77b4"
SENTIMENT_COLOR = "#d62728"
EMPTY_SENTIMENT_MESSAGE = (
    "No scored posts are available for this window, so no sentiment curve is drawn."
)
SENTIMENT_CHANGE_EMPTY_MESSAGE = (
    "No day-over-day sentiment change is drawn because no two consecutive UTC "
    "days in this window carry scored sentiment."
)
ONE_DAY = timedelta(days=1)

ChartPoint = tuple[datetime, float]


@dataclass(frozen=True, slots=True)
class ChartPanel:
    """One stacked panel with its own y scale and a shared time axis."""

    title: str
    y_label: str
    color: str
    points: tuple[ChartPoint, ...]
    empty_message: str
    baseline: float | None = None


def price_points(
    candles: Sequence[PriceCandle], now: datetime | None = None
) -> tuple[ChartPoint, ...]:
    ordered = sorted(completed_candles(candles, now), key=lambda candle: candle.timestamp)
    return tuple((candle.timestamp.astimezone(UTC), float(candle.close)) for candle in ordered)


def sentiment_points(rows: Sequence[SupervisedRow]) -> tuple[ChartPoint, ...]:
    points: list[ChartPoint] = []
    for row in sorted(rows, key=lambda item: item.cutoff):
        value = row.features.get("mean_sentiment_24h")
        if value is not None:
            points.append((row.cutoff, float(value)))
    return tuple(points)


def sentiment_change_points(rows: Sequence[SupervisedRow]) -> tuple[ChartPoint, ...]:
    """Day-over-day change of the trailing-24h mean sentiment (the R10 series).

    The value at cutoff ``T`` is
    ``mean_sentiment_24h(T) - mean_sentiment_24h(T - 1 UTC day)`` and is emitted
    only when both cutoffs exist exactly one day apart and both means are
    available. Anything else stays absent: an unscored day is missing data, not
    neutral sentiment and not zero change, so a genuine zero change (both days
    scored, equal means) remains distinguishable from unavailability.
    Both means were already point-in-time at their own cutoffs, so a change
    value never reads information beyond ``T``. Series values are reporting-only.
    """
    means = {row.cutoff: row.features.get("mean_sentiment_24h") for row in rows}
    points: list[ChartPoint] = []
    for row in sorted(rows, key=lambda item: item.cutoff):
        if row.cutoff.tzinfo is None:
            raise ValueError("supervised rows must carry timezone-aware cutoffs")
        current = row.features.get("mean_sentiment_24h")
        if current is None:
            continue
        previous = means.get(row.cutoff - ONE_DAY)
        if previous is None:
            continue
        points.append((row.cutoff, float(current) - float(previous)))
    return tuple(points)


def render_sentiment_price_chart(
    candles: Sequence[PriceCandle],
    rows: Sequence[SupervisedRow],
    path: str | Path,
    *,
    title: str = "BTC-USD close and X sentiment",
    subtitle: str = "",
    now: datetime | None = None,
) -> Path:
    """Write one SVG with the close panel plus level and change sentiment panels."""
    panels = (
        ChartPanel(
            title="Observed daily close (UTC bars)",
            y_label="USD close",
            color=PRICE_COLOR,
            points=price_points(candles, now),
            empty_message="No completed price bars are available for this window.",
        ),
        ChartPanel(
            title="Mean sentiment of eligible posts over the trailing 24 hours",
            y_label="sentiment score",
            color=SENTIMENT_COLOR,
            points=sentiment_points(rows),
            empty_message=EMPTY_SENTIMENT_MESSAGE,
            baseline=0.0,
        ),
        ChartPanel(
            title="Day-over-day change of the trailing-24h mean sentiment",
            y_label="change",
            color=SENTIMENT_COLOR,
            points=sentiment_change_points(rows),
            empty_message=SENTIMENT_CHANGE_EMPTY_MESSAGE,
            baseline=0.0,
        ),
    )
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        render_panels(panels, title=title, subtitle=subtitle), encoding="utf-8"
    )
    return destination


def _format_value(value: float, reference: float) -> str:
    if abs(reference) >= 1000:
        return f"{value:,.0f}"
    if abs(reference) <= 1.0:
        return f"{value:+.2f}"
    return f"{value:,.2f}"


def _time_bounds(points: Sequence[ChartPoint]) -> tuple[float, float]:
    stamps = [moment.timestamp() for moment, _ in points]
    return min(stamps), max(stamps)


def render_panels(panels: Sequence[ChartPanel], *, title: str, subtitle: str = "") -> str:
    """Render stacked panels that share one time axis and each own a y axis."""
    if not panels:
        raise ValueError("at least one panel is required")
    all_points = [point for panel in panels for point in panel.points]
    height = (
        PADDING_TOP
        + len(panels) * PANEL_HEIGHT
        + (len(panels) - 1) * PANEL_GAP
        + PADDING_BOTTOM
    )
    plot_right = WIDTH - PADDING_RIGHT
    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height}" '
        f'width="{WIDTH}" height="{height}" role="img">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{PADDING_LEFT}" y="30" font-family="sans-serif" font-size="18" '
        f'fill="#111111">{escape(title)}</text>',
    ]
    if subtitle:
        parts.append(
            f'<text x="{PADDING_LEFT}" y="50" font-family="sans-serif" font-size="12" '
            f'fill="#555555">{escape(subtitle)}</text>'
        )

    if all_points:
        start, end = _time_bounds(all_points)
    else:
        start, end = 0.0, 1.0
    if start == end:
        start, end = start - 86_400.0, end + 86_400.0

    for index, panel in enumerate(panels):
        top = PADDING_TOP + index * (PANEL_HEIGHT + PANEL_GAP)
        bottom = top + PANEL_HEIGHT
        parts.append(
            f'<text x="{PADDING_LEFT}" y="{top - 10}" font-family="sans-serif" '
            f'font-size="14" fill="#111111">{escape(panel.title)}</text>'
        )
        parts.extend(
            _axis_lines(panel, top=top, bottom=bottom, plot_right=plot_right, start=start, end=end)
        )

    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def _axis_lines(
    panel: ChartPanel,
    *,
    top: int,
    bottom: int,
    plot_right: int,
    start: float,
    end: float,
) -> list[str]:
    elements: list[str] = []
    elements.append(
        f'<line x1="{PADDING_LEFT}" y1="{bottom}" x2="{plot_right}" y2="{bottom}" '
        f'stroke="#cccccc" stroke-width="1"/>'
    )
    if not panel.points:
        elements.append(
            f'<text x="{PADDING_LEFT + 12}" y="{top + PANEL_HEIGHT // 2}" '
            f'font-family="sans-serif" font-size="13" fill="#666666">'
            f"{escape(panel.empty_message)}</text>"
        )
        return elements

    values = [value for _, value in panel.points]
    low, high = min(values), max(values)
    if panel.baseline is not None:
        low, high = min(low, panel.baseline), max(high, panel.baseline)
    if low == high:
        low, high = low - 0.5, high + 0.5
    span = high - low
    low, high = low - span * 0.08, high + span * 0.08
    reference = max(abs(low), abs(high))

    def x_of(moment: float) -> float:
        return PADDING_LEFT + (moment - start) / (end - start) * (plot_right - PADDING_LEFT)

    def y_of(value: float) -> float:
        return bottom - (value - low) / (high - low) * (bottom - top)

    for tick in range(Y_TICKS + 1):
        value = low + (high - low) * tick / Y_TICKS
        y = y_of(value)
        elements.append(
            f'<line x1="{PADDING_LEFT}" y1="{y:.2f}" x2="{plot_right}" y2="{y:.2f}" '
            f'stroke="#eeeeee" stroke-width="1"/>'
        )
        elements.append(
            f'<text x="{PADDING_LEFT - 8}" y="{y + 4:.2f}" text-anchor="end" '
            f'font-family="sans-serif" font-size="11" fill="#444444">'
            f"{escape(_format_value(value, reference))}</text>"
        )
    elements.append(
        f'<text x="{PADDING_LEFT - 8}" y="{top - 2}" text-anchor="end" '
        f'font-family="sans-serif" font-size="11" fill="#777777">'
        f"{escape(panel.y_label)}</text>"
    )

    if panel.baseline is not None:
        y = y_of(panel.baseline)
        elements.append(
            f'<line x1="{PADDING_LEFT}" y1="{y:.2f}" x2="{plot_right}" y2="{y:.2f}" '
            f'stroke="#999999" stroke-dasharray="4 3" stroke-width="1"/>'
        )

    coordinates = " ".join(
        f"{x_of(moment.timestamp()):.2f},{y_of(value):.2f}" for moment, value in panel.points
    )
    elements.append(
        f'<polyline fill="none" stroke="{panel.color}" stroke-width="1.8" '
        f'points="{coordinates}"/>'
    )

    for tick in range(X_TICKS + 1):
        moment = start + (end - start) * tick / X_TICKS
        x = x_of(moment)
        label = datetime.fromtimestamp(moment, tz=UTC).date().isoformat()
        elements.append(
            f'<line x1="{x:.2f}" y1="{bottom}" x2="{x:.2f}" y2="{bottom + 5}" '
            f'stroke="#999999" stroke-width="1"/>'
        )
        elements.append(
            f'<text x="{x:.2f}" y="{bottom + 20}" text-anchor="middle" '
            f'font-family="sans-serif" font-size="10" fill="#555555">{escape(label)}</text>'
        )
    return elements
