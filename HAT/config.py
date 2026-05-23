"""
Global configuration store — thread-safe singleton shared across all tests.

Stores:
  - Browser settings (_browser)
  - Page element locators (_locators, _elements)
  - Database configs (_database)
  - DDT / extracted variables
  - POM page object registry (_pages)
  - AI model config
"""

from typing import Any


class Config:
    """Singleton config. All instances share the same class-level dict."""

    _store: dict = {}

    def set(self, key: str, value: Any) -> None:
        self._store[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._store.get(key, default)

    def update(self, mapping: dict) -> None:
        if mapping:
            self._store.update(mapping)

    def all(self) -> dict:
        return self._store

    def clear(self) -> None:
        self._store.clear()


# Module-level singleton — import and use directly
cfg = Config()
