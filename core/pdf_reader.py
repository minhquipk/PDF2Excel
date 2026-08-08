from __future__ import annotations
from pathlib import Path
from typing import Any
import pymupdf as fitz
from core.constants import Image
from core.models import (
    PageImage,
    PDFDocument,
    PDFPage,
    PageStatistics,
)


class PDFReader:
    """
    Read PDF files and convert them into domain models.

    This class is responsible for collecting raw information from a PDF.
    It never performs OCR, parsing, validation or business analysis.
    """

    def read(self, pdf_path: Path) -> PDFDocument:
        """
        Read a PDF file.

        Parameters
        ----------
        pdf_path:
            PDF file path.

        Returns
        -------
        PDFDocument
            Fully populated PDF domain model.
        """

        with fitz.open(pdf_path) as document:
            metadata = self._read_metadata(document)
            pages = self._read_pages(document)

        return PDFDocument(
            path=pdf_path,
            pages=pages,
            metadata=metadata,
        )

    @staticmethod
    def _read_metadata(document: fitz.Document,) -> dict[str, Any]:
        """
        Read document metadata.
        """
        return dict(document.metadata)

    def _read_pages(
        self,
        document: fitz.Document,
    ) -> tuple[PDFPage, ...]:
        """
        Read every page in document.
        """

        pages: list[PDFPage] = []

        for page_index in range(document.page_count):
            page = self._read_page(
                document=document,
                page_index=page_index,
            )

            pages.append(page)

        return tuple(pages)

    def _read_page(
        self,
        document: fitz.Document,
        page_index: int,
    ) -> PDFPage:
        """
        Read one page.
        """

        page = document.load_page(page_index)

        text = page.get_text("text")
        words = page.get_text("words")

        statistics = self._read_statistics(
            page=page,
            text=text,
        )

        page_image = self._render_page_image(page)

        return PDFPage(
            page_index=page_index,
            text=text,
            statistics=statistics,
            words=words,
            page_image=page_image,
        )

    def _read_statistics(
        self,
        page: fitz.Page,
        text: str,
    ) -> PageStatistics:
        """
        Read page statistics.
        """

        page_dict = page.get_text("dict")

        return PageStatistics(
            text_length=len(text),
            image_count=len(page.get_images()),
            font_count=self._count_fonts(page_dict),
            text_block_count=self._count_text_blocks(page_dict),
            drawing_count=len(page.get_drawings()),
            annotation_count=self._count_annotations(page),
            width=page.rect.width,
            height=page.rect.height,
            rotation=page.rotation,
        )

    @staticmethod
    def _render_page_image(page: fitz.Page) -> PageImage:
        """
        Render page thành ảnh RGB, raw pixmap samples.
        """

        pixmap = page.get_pixmap(dpi=Image.DPI, colorspace=fitz.csRGB)

        return PageImage(
            samples=pixmap.samples,
            width=int(getattr(pixmap, "width")),
            height=int(getattr(pixmap, "height")),
            dpi=Image.DPI,
            channels=3,
        )

    @staticmethod
    def _count_fonts(page_dict: dict[str, Any],) -> int:
        """
        Count unique fonts used on the page.
        """
        font_names: set[str] = set()

        for block in page_dict.get("blocks", []):
            if block.get("type") != 0:
                continue

            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    font = span.get("font")

                    if font:
                        font_names.add(font)

        return len(font_names)

    @staticmethod
    def _count_text_blocks(page_dict: dict[str, Any],) -> int:
        """
        Count text blocks on the page.
        """
        count = 0

        for block in page_dict.get("blocks", []):
            if block.get("type") == 0:
                count += 1

        return count

    @staticmethod
    def _count_annotations(page: fitz.Page,) -> int:
        """
        Count page annotations.
        """
        annotations_iter = page.annots()

        if annotations_iter is None:
            return 0

        return sum(1 for _ in annotations_iter)
