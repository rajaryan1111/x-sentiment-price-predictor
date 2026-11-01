"""Display units for asset quote values."""
from __future__ import annotations


def quote_currency(asset: str, provenance: dict[str, object] | None = None) -> str:
    """Return explicit snapshot quote currency, otherwise infer a common pair suffix."""
    metadata = (provenance or {}).get("price_snapshot_metadata")
    if isinstance(metadata, dict):
        quote = metadata.get("quote_currency")
        if isinstance(quote, str) and quote.strip():
            return quote.strip().upper()
    normalized = asset.upper().replace("-", "")
    for quote in ("USDT", "USDC", "BUSD", "USD", "EUR", "GBP", "BTC", "ETH"):
        if normalized.endswith(quote):
            return quote
    return "quote units"
