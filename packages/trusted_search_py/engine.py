"""Core search engine scaffolding."""

from .settings import Settings


class SearchEngine:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()

