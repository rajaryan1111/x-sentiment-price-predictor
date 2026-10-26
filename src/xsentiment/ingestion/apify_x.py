"""Apify X ingestion adapter placeholder; provider contract/actor selection is pending."""
from xsentiment.config.settings import get_settings


class ApifyXAdapter:
    """Reserved for a verified Apify actor and approved input/output contract."""
    def __init__(self) -> None:
        self.settings = get_settings()

    def is_configured(self) -> bool:
        return bool(self.settings.apify_api_token and self.settings.apify_actor_id)
