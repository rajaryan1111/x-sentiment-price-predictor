"""Optional Tavily/Exa context adapters; news is not an implicit model feature."""
from xsentiment.config.settings import get_settings


class NewsSearchConfiguration:
    def __init__(self) -> None:
        self.settings = get_settings()

    def configured_providers(self) -> tuple[str, ...]:
        providers: list[str] = []
        tavily_key = self.settings.tavily_api_key
        exa_key = self.settings.exa_api_key
        if tavily_key and tavily_key.get_secret_value().strip():
            providers.append("tavily")
        if exa_key and exa_key.get_secret_value().strip():
            providers.append("exa")
        return tuple(providers)
