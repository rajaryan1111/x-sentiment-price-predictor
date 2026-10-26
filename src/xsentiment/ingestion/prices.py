"""Price data adapter boundary; provider choice and licensing need confirmation."""
from xsentiment.config.settings import get_settings


class PriceDataAdapter:
    def __init__(self) -> None:
        self.settings = get_settings()

    def is_configured(self) -> bool:
        return bool(self.settings.price_provider and self.settings.asset_symbol)
