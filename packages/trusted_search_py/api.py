"""API-facing service layer scaffold."""

from .engine import SearchEngine


class SearchApiService:
    def __init__(self, engine: SearchEngine | None = None) -> None:
        self.engine = engine or SearchEngine()

