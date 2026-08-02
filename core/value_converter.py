"""
Convert raw text (đã regex-match) sang kiểu dữ liệu đích của một FieldDefinition.

Quy ước:
- Stateless: không giữ trạng thái, không phụ thuộc I/O.
- Không raise Exception: convert thất bại trả về None.
  Parser tự quyết định field đó là None trong InvoiceInfo (theo quyết định đã
  chốt: convert fail -> field = None -> không ghi Excel -> xử lý ở Report).
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from core.enums import ValueType
from core.models import FieldDefinition

# Giá trị mặc định khi FieldDefinition.decimal_format không khai báo.
# Khớp quy ước phân cách số của hóa đơn Việt Nam (ADR-014: Vietnamese Data).
_DEFAULT_THOUSAND_SEPARATOR = "."
_DEFAULT_DECIMAL_SEPARATOR = ","


class ValueConverter:
    """Convert raw text thành kiểu dữ liệu đích theo FieldDefinition.value_type."""

    @staticmethod
    def convert(raw_text: str, field: FieldDefinition) -> Any | None:
        if not raw_text:
            return None

        if field.value_type is ValueType.TEXT:
            return ValueConverter._to_text(raw_text)

        if field.value_type is ValueType.DECIMAL:
            return ValueConverter._to_decimal(raw_text, field.decimal_format)

        if field.value_type is ValueType.DATE:
            return ValueConverter._to_date(raw_text, field.date_format)

        return None

    @staticmethod
    def _to_text(raw_text: str) -> str | None:
        text = raw_text.strip()
        return text or None

    @staticmethod
    def _to_decimal(
        raw_text: str,
        decimal_format: dict[str, str] | None,
    ) -> Decimal | None:
        thousand_sep = _DEFAULT_THOUSAND_SEPARATOR
        decimal_sep = _DEFAULT_DECIMAL_SEPARATOR

        if decimal_format:
            thousand_sep = decimal_format.get("thousand_separator", thousand_sep)
            decimal_sep = decimal_format.get("decimal_separator", decimal_sep)

        normalized = raw_text.strip()

        if thousand_sep:
            normalized = normalized.replace(thousand_sep, "")

        if decimal_sep and decimal_sep != ".":
            normalized = normalized.replace(decimal_sep, ".")

        try:
            return Decimal(normalized)
        except InvalidOperation:
            return None

    @staticmethod
    def _to_date(raw_text: str, date_format: str | None) -> date | None:
        if not date_format:
            return None

        try:
            return datetime.strptime(raw_text.strip(), date_format).date()
        except ValueError:
            return None
