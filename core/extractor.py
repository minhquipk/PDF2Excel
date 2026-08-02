"""Convert PDFDocument + DocumentAnalysis into word-level, normalized
extraction results, ready for Parser.
"""

from __future__ import annotations

from core.models import (
    AnalysisMode,
    DocumentAnalysis,
    ExtractionResult,
    PDFDocument,
    PDFPage,
    WordToken,
)
from core.ocr_engine import OCREngine


class Extractor:
    """Dispatch extraction strategy per DocumentAnalysis.mode.

    The Extractor never re-evaluates document type; ``analysis.mode`` is
    treated as an already-finalized decision (a decision is made once and
    reused downstream). It normalizes geometry for both the Digital
    (text-layer) and OCR (image) sources into a shared, comparable
    coordinate space, but never performs OCR itself — that is delegated
    to OCREngine.
    """

    def __init__(self) -> None:
        self._ocr_engine = OCREngine()

    def extract(
        self,
        document: PDFDocument,
        analysis: DocumentAnalysis,
    ) -> ExtractionResult:
        """Return word-level extraction results for the given decision."""
        if analysis.mode is AnalysisMode.UNKNOWN:
            return ExtractionResult(
                source_mode=analysis.mode,
                words_by_page={},
                warnings=(
                    "Extraction was skipped because the document type is unknown.",
                ),
            )

        words_by_page: dict[int, tuple[WordToken, ...]] = {}
        page_images = {}

        for page in document.pages:
            words_by_page[page.page_index] = self._extract_page(page, analysis.mode)

            if page.page_image is not None:
                page_images[page.page_index] = page.page_image

        return ExtractionResult(
            source_mode=analysis.mode,
            words_by_page=words_by_page,
            page_images=page_images,
        )

    def _extract_page(
        self,
        page: PDFPage,
        mode: AnalysisMode,
    ) -> tuple[WordToken, ...]:
        """Route a single page to the Digital or OCR extraction path."""
        if mode is AnalysisMode.DIGITAL:
            return self._extract_digital_page(page)

        if mode is AnalysisMode.SCANNED:
            return self._extract_ocr_page(page)

        # HYBRID: decide per page, since text and image coverage may
        # differ across pages of the same document.
        if page.has_text:
            return self._extract_digital_page(page)

        return self._extract_ocr_page(page)

    def _extract_digital_page(self, page: PDFPage) -> tuple[WordToken, ...]:
        """Build WordTokens from raw PyMuPDF words, correcting for rotation.

        ``page.get_text("words")`` returns coordinates relative to the
        unrotated page, while ``page.statistics.width/height`` (sourced
        from ``page.rect``) reflect the rotated, visual page. The two
        frames must be reconciled before normalization.
        """
        rotation = page.statistics.rotation % 360
        rotated_width = page.statistics.width
        rotated_height = page.statistics.height

        tokens: list[WordToken] = []
        for raw_word in page.words:
            x0, y0, x1, y1, text, *_ = raw_word

            normalized_text = self._normalize_text(text)
            if not normalized_text:
                continue

            bbox = self._rotate_bbox(
                (x0, y0, x1, y1),
                rotation=rotation,
                rotated_width=rotated_width,
                rotated_height=rotated_height,
            )
            normalized_bbox = self._normalize_bbox(bbox, rotated_width, rotated_height)

            tokens.append(
                WordToken(
                    text=normalized_text,
                    normalized_bbox=normalized_bbox,
                    confidence=None,
                    source="digital",
                )
            )

        return tuple(tokens)

    def _extract_ocr_page(self, page: PDFPage) -> tuple[WordToken, ...]:
        """Build WordTokens from OCR output.

        No rotation transform is applied here: PyMuPDF bakes page
        rotation into the rendered pixmap by design, so page_image and
        any OCR bbox derived from it already share the same, rotated
        reference frame.
        """
        if page.page_image is None:
            return ()

        raw_words = self._ocr_engine.recognize(page.page_image)

        tokens: list[WordToken] = []
        for x0, y0, x1, y1, text, confidence in raw_words:
            normalized_text = self._normalize_text(text)
            if not normalized_text:
                continue

            normalized_bbox = self._normalize_bbox(
                (x0, y0, x1, y1),
                page.page_image.width,
                page.page_image.height,
            )
            tokens.append(
                WordToken(
                    text=normalized_text,
                    normalized_bbox=normalized_bbox,
                    confidence=confidence,
                    source="ocr",
                )
            )

        return tuple(tokens)

    @staticmethod
    def _normalize_text(text: str) -> str:
        """
        Chuẩn hoá whitespace của một text token.

        Loại bỏ khoảng trắng thừa đầu/cuối và thu gọn khoảng trắng liên tiếp
        bên trong thành 1 khoảng trắng. Áp dụng cho cả hai nguồn (Digital/
        OCR) vì đây là quy tắc định dạng chung, không phụ thuộc domain model
        nào - phù hợp đặt tại Extractor thay vì lặp lại ở Parser (xem ADR-029).

        Token trở thành rỗng sau khi chuẩn hoá (VD toàn khoảng trắng) sẽ bị
        loại bỏ hoàn toàn, không tạo WordToken tương ứng.
        """
        return " ".join(text.split())

    @staticmethod
    def _rotate_bbox(
        bbox: tuple[float, float, float, float],
        *,
        rotation: int,
        rotated_width: float,
        rotated_height: float,
    ) -> tuple[float, float, float, float]:
        """Map an unrotated word bbox into the rotated (visual) page frame.

        rotated_width/height are the visual dimensions (page.rect). The
        unrotated dimensions are derived from them: for 90/270, width and
        height are swapped relative to the unrotated page; for 0/180,
        they are unchanged. PyMuPDF guarantees rotation is one of
        0, 90, 180, 270.
        """
        x0, y0, x1, y1 = bbox

        if rotation == 90:
            unrotated_height = rotated_width
            return (
                unrotated_height - y1,
                x0,
                unrotated_height - y0,
                x1,
            )

        if rotation == 180:
            return (
                rotated_width - x1,
                rotated_height - y1,
                rotated_width - x0,
                rotated_height - y0,
            )

        if rotation == 270:
            unrotated_width = rotated_height
            return (
                y0,
                unrotated_width - x1,
                y1,
                unrotated_width - x0,
            )

        return x0, y0, x1, y1

    @staticmethod
    def _normalize_bbox(
        bbox: tuple[float, float, float, float],
        reference_width: float,
        reference_height: float,
    ) -> tuple[float, float, float, float]:
        """Normalize a bbox to [0.0, 1.0] against an explicit reference size."""
        if reference_width <= 0 or reference_height <= 0:
            return 0.0, 0.0, 0.0, 0.0

        x0, y0, x1, y1 = bbox
        return (
            Extractor._clamp(x0 / reference_width),
            Extractor._clamp(y0 / reference_height),
            Extractor._clamp(x1 / reference_width),
            Extractor._clamp(y1 / reference_height),
        )

    @staticmethod
    def _clamp(value: float) -> float:
        return max(0.0, min(1.0, value))
