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
from core.constants import NumberRepair

# Giá trị mặc định khi FieldDefinition.decimal_format không khai báo.
# Khớp quy ước phân cách số của hóa đơn Việt Nam (ADR-014: Vietnamese Data).
_DEFAULT_THOUSAND_SEPARATOR = "."
_DEFAULT_DECIMAL_SEPARATOR = ","

# Hậu tố đơn vị tiền tệ VND — strip vô điều kiện trước khi parse Decimal
# (ADR-051, đối xứng ADR-043 cho ký hiệu '%'). Các biến thể ≥2 ký tự
# hoặc ký tự Unicode riêng biệt (₫) không thể là 1 phần hợp lệ khác
# của số Decimal -> an toàn để strip không điều kiện.
_CURRENCY_SUFFIXES = ("vnd", "vnđ", "₫")

# Biến thể 1 ký tự ('đ'/'Đ') CẦN ràng buộc vị trí riêng (xem
# _strip_currency_suffix()) - khác _CURRENCY_SUFFIXES vì 1 ký tự chữ
# đơn lẻ có rủi ro trùng nội dung khác cao hơn nhiều so với chuỗi
# 2+ ký tự (ADR-051).
_SINGLE_CHAR_CURRENCY_SUFFIXES = ("đ", "Đ")


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

        # Khi chuỗi có ký hiệu phần trăm cuối chuỗi (VD field vat_rate: "5%"),
        # chuyển đổi giá trị về dạng đại số thực sự bằng cách chia cho 100
        # ("5%" -> Decimal("0.05")), giúp dữ liệu trong InvoiceInfo chuẩn xác
        # và tương thích tự nhiên với định dạng Percentage của Excel.
        is_percentage = False
        if normalized.endswith("%"):
            normalized = normalized[:-1].strip()
            is_percentage = True

        # Strip hậu tố đơn vị tiền tệ VND (VD OCR quét dính liền:
        # "4,842,303VND") trước khi parse Decimal (ADR-051).
        normalized = ValueConverter._strip_currency_suffix(normalized)

        # Kiểm tra khả nghi TRƯỚC khi thousand/decimal_sep bị replace -
        # bước replace phía dưới xóa mất dấu vết cấu trúc cần để phát
        # hiện OCR nhầm lẫn ',' <-> '.' (ADR-052).
        value: Decimal | None = None
        if ValueConverter._looks_ambiguous(normalized, decimal_sep):
            repaired = ValueConverter._normalize_number_separators(normalized)
            value = ValueConverter._parse_plain_decimal(repaired)

        if value is None:
            conventional = (
                normalized.replace(thousand_sep, "") if thousand_sep else normalized
            )
            if decimal_sep and decimal_sep != ".":
                conventional = conventional.replace(decimal_sep, ".")
            value = ValueConverter._parse_plain_decimal(conventional)

        if value is None:
            return None

        return value / Decimal("100") if is_percentage else value

    @staticmethod
    def _strip_currency_suffix(normalized: str) -> str:
        """
        Strip hậu tố đơn vị tiền tệ VND khỏi cuối chuỗi số (ADR-051).

        - Biến thể vnd/VND/vnđ/VNĐ/₫: strip vô điều kiện (case-insensitive
          qua .lower(), không thể là 1 phần hợp lệ khác của số Decimal).
        - Biến thể đ/Đ (1 ký tự): CHỈ strip khi ký tự liền trước là chữ số
          (0-9) - ràng buộc vị trí, giảm rủi ro strip nhầm 1 ký tự chữ cái
          Việt không liên quan (khác hẳn rủi ro thấp của các biến thể dài
          hơn ở trên).
        """
        lowered = normalized.lower()
        for suffix in _CURRENCY_SUFFIXES:
            if lowered.endswith(suffix):
                return normalized[: -len(suffix)].strip()

        if (
                normalized
                and normalized[-1] in _SINGLE_CHAR_CURRENCY_SUFFIXES
                and len(normalized) > 1
                and normalized[-2].isdigit()
        ):
            return normalized[:-1]

        return normalized

    @staticmethod
    def _split_number_groups(raw: str) -> tuple[list[str], list[str]]:
        """
        Tách chuỗi số thành các cụm chữ số theo VỊ TRÍ dấu ',' và '.'
        (không phân biệt loại dấu - vì bản thân loại ký tự là điểm OCR
        hay đọc nhầm, xem ADR-052). len(groups) == len(seps) + 1.
        """
        groups: list[str] = []
        seps: list[str] = []
        current: list[str] = []
        for ch in raw:
            if ch in (",", "."):
                groups.append("".join(current))
                seps.append(ch)
                current = []
            else:
                current.append(ch)
        groups.append("".join(current))
        return groups, seps

    @staticmethod
    def _looks_ambiguous(raw: str, decimal_sep: str) -> bool:
        """
        Phát hiện chuỗi số có dấu hiệu bị OCR đọc nhầm lẫn ',' <-> '.',
        dựa trên CẤU TRÚC chuỗi gốc - độc lập với việc Decimal() có
        raise exception hay không. Decimal() có thể "parse thành công"
        nhưng sai trị số (silent corruption) - xem ADR-052.
        """
        groups, seps = ValueConverter._split_number_groups(raw)
        if not seps:
            return False

        # Vị trí phi lý: dấu phân cách đứng ở đầu/cuối chuỗi.
        if groups[0] == "" or groups[-1] == "":
            return True

        # Double punctuation: 2 dấu phân cách liền nhau.
        if any(group == "" for group in groups[1:-1]):
            return True

        # decimal_separator đã cấu hình xuất hiện nhiều hơn 1 lần.
        if seps.count(decimal_sep) > 1:
            return True

        # Có cả 2 loại dấu, và dấu CUỐI CÙNG không phải decimal_separator
        # đã cấu hình - trái quy tắc "dấu cuối luôn là decimal nếu có
        # phần lẻ".
        if len(set(seps)) > 1 and seps[-1] != decimal_sep:
            return True

        decimal_at_end = seps[-1] == decimal_sep

        # Decimal Tail Length: phần sau dấu cuối (nếu là decimal_sep)
        # dài hơn ngưỡng hợp lý -> nhiều khả năng thực ra là 1 nhóm
        # nghìn (3 chữ số) bị đọc nhầm thành decimal.
        if decimal_at_end and len(groups[-1]) > NumberRepair.DECIMAL_TAIL_MAX_LENGTH:
            return True

        # Quy tắc 3 chữ số: mọi cụm không phải cụm đầu (và không phải
        # cụm cuối nếu cụm cuối là decimal) phải có đúng 3 chữ số.
        thousand_groups = groups[1:-1] if decimal_at_end else groups[1:]
        if any(len(group) != 3 for group in thousand_groups):
            return True

        return False

    @staticmethod
    def _normalize_number_separators(raw: str) -> str:
        """
        Fallback heuristic khi _looks_ambiguous() == True (ADR-052).
        Suy luận dựa trên VỊ TRÍ dấu phân cách, không dựa vào bản thân
        ký tự. Nếu cụm cuối có độ dài hợp lý cho phần thập phân -> coi
        dấu cuối là decimal, còn lại strip. Ngược lại -> coi TOÀN BỘ là
        thousand separator, strip hết (ưu tiên giữ đúng ĐỘ LỚN số hơn
        đoán sai vị trí thập phân).
        """
        groups, seps = ValueConverter._split_number_groups(raw)
        if not seps:
            return raw

        has_boundary_or_double = (
                groups[0] == "" or groups[-1] == "" or any(g == "" for g in groups[1:-1])
        )

        if (
                not has_boundary_or_double
                and 1 <= len(groups[-1]) <= NumberRepair.DECIMAL_TAIL_MAX_LENGTH
        ):
            return f"{''.join(groups[:-1])}.{groups[-1]}"

        return "".join(groups)

    @staticmethod
    def _parse_plain_decimal(text: str) -> Decimal | None:
        try:
            return Decimal(text)
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
