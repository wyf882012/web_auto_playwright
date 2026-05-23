"""AI vision provider protocol + default Qwen-VL implementation."""
from typing import Protocol


class AIVisionProvider(Protocol):
    """Vision model provider protocol — implement to support different AI vendors."""

    def resize(self, width: int, height: int) -> tuple[int, int]:
        """Return (resize_width, resize_height) for the provider's preferred input."""
        ...

    def get_min_max_pixels(self) -> tuple[int, int]:
        """Return (min_pixels, max_pixels) for the provider."""
        ...


class QwenVLProvider:
    """Default provider for Qwen-VL compatible APIs (uses smart_resize)."""

    def resize(self, width: int, height: int) -> tuple[int, int]:
        from qwen_vl_utils import smart_resize
        min_px, max_px = self.get_min_max_pixels()
        ih, iw = smart_resize(height, width, factor=1.0,
                              min_pixels=min_px, max_pixels=max_px)
        return iw, ih

    def get_min_max_pixels(self) -> tuple[int, int]:
        return 512 * 28 * 28, 2048 * 28 * 28
