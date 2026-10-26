"""Optional Tavily/Exa context adapters; news is provenance/context, not an implicit model feature."""
from xsentiment.config.settings import get_settings


class NewsSearchConfiguration:
    def __init__(self) -> None:
        self.settings = get_settings()

    def configured_providers(self) -> tuple[str, ...]:
        providers = []
        if self.settings.tavily_api_key:
            providers.append("tavily")
        if self.settings.exa_api_key:
            providers.append("exa")
        return tuple(providers)
