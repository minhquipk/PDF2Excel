"""Placeholder OCR engine.

Implements only the contract Extractor depends on (ADR-013 Mock First).
Performs no real optical character recognition yet. When a real backend
(e.g. Tesseract) is wired in, ``recognize()`` must keep its signature so
Extractor requires no change.
"""

from __future__ import annotations
from core.models import PageImage


class OCREngine:
    """Recognize words in a rendered page image.

    Symmetric with PDFReader: returns raw, un-normalized output. All
    coordinate normalization is the sole responsibility of Extractor.
    """

    def recognize(
        self,
        page_image: PageImage,
    ) -> tuple[tuple[float, float, float, float, str, float], ...]:
        """Return raw OCR words as (x0, y0, x1, y1, text, confidence).

        Coordinates are pixel-space of ``page_image`` (top-left origin,
        y-down), matching ``page_image.width`` / ``page_image.height``.

        Mock implementation: always returns an empty tuple. No OCR backend
        is wired in yet.
        """
        return ()
