"""
Parser: orchestrator mỏng, điều phối TemplateMatcher + ValueConverter để
build InvoiceInfo từ ExtractionResult.

Quy ước:
- Không chứa logic Key Matching/Windowing/Value Matching (nằm trong
  TemplateMatcher).
- Không chứa logic convert kiểu dữ liệu (nằm trong ValueConverter).
- parse() trả None khi không xác định được template - đối xứng ADR-027
  ("UNKNOWN là absence of decision, không phải case cần xử lý"). Worker
  chịu trách nhiệm quyết định ProcessStatus tương ứng, giữ nguyên tắc
  "quyết định một lần, không re-evaluate downstream" (TDS §3.1).
"""

from __future__ import annotations
from typing import Any
from core.models import ExtractionResult, InvoiceInfo
from core.template_matcher import TemplateMatcher
from core.value_converter import ValueConverter


class Parser:
    """Orchestrator: chọn template, trích field, build InvoiceInfo."""

    def __init__(self, matcher: TemplateMatcher) -> None:
        self._matcher = matcher

    def parse(
        self,
        extraction: ExtractionResult,
        source_file: str,
    ) -> InvoiceInfo | None:
        """
        Parse một ExtractionResult thành InvoiceInfo.

        Parameters
        ----------
        extraction:
            Kết quả trích xuất WordToken từ Extractor.
        source_file:
            Đường dẫn file PDF gốc, gán trực tiếp vào InvoiceInfo.source_file
            (không qua template/regex - Parser tự gán).

        Returns
        -------
        InvoiceInfo nếu xác định được template phù hợp, ngược lại None
        (không xác định được mẫu hóa đơn nào khớp).
        """
        selection = self._matcher.select_template(extraction)
        if selection is None:
            return None

        raw_values = self._matcher.extract_fields(selection, extraction)

        values: dict[str, Any] = {"source_file": source_file}
        for field_def in selection.template.fields:
            raw_text = raw_values.get(field_def.field_name)
            values[field_def.field_name] = (
                ValueConverter.convert(raw_text, field_def)
                if raw_text
                else None
            )

        return InvoiceInfo(**values)
