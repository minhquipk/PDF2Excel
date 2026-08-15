"""
Unit test cho ValueConverter (core/parsing/template/value_converter.py).

Bối cảnh: ValueConverter là staticmethod-only, stateless, không I/O -
tương tự Extractor._rotate_bbox() (xem tests/core/extraction/test_extractor.py)
nên gọi trực tiếp được, không cần mock/fixture PDF/OCR nào.

Nguyên tắc dùng cho toàn bộ file này (đối xứng test_extractor.py): giá trị
"expected" được TỰ SUY DIỄN bằng cách đọc trực tiếp thuật toán trong
value_converter.py và tính tay theo đúng đặc tả ADR-032/043/051/052 -
KHÔNG chạy code hiện có rồi copy ngược kết quả.

Các nhóm test:
- TestConvertDispatch: convert() dispatch đúng theo ValueType, chặn rỗng/None.
- TestToText: strip whitespace, whitespace-only -> None.
- TestStripCurrencySuffix: 7 biến thề VND (ADR-051), gồm case bảo vệ vị trí
  cho đ/Đ.
- TestToDecimalDefaultFormat / TestToDecimalOverrideFormat: happy path theo
  decimal_format mặc định VN và override (ADR-051 - dữ liệu test dùng
  ngược mặc định).
- TestToDecimalPercentage: strip % + chia 100 (ADR-043).
- TestToDecimalCurrencySuffix: tích hợp strip suffix + convert Decimal.
- TestLooksAmbiguous: 6 dấu hiệu khả nghi (ADR-052), mỗi dấu hiệu 1 test
  cô lập (không để dấu hiệu khác vô tình trigger trước).
- TestNormalizeNumberSeparators: heuristic phục hồi (ADR-052), bao gồm 1
  case xác nhận đúng giới hạn đã biết ("cụm cuối 3 chữ số trùng ngẫu
  nhiên với decimal_separator" - không phải bug, là behavior đã ghi
  nhận trong ADR-052 Known Limitations).
- TestToDate: happy path + sai format + date_format=None -> None.
- TestConvertNeverRaises: ADR-032 - convert() không bao giờ raise, mọi
  input rác trả về None hoặc đúng kiểu dữ liệu đích.
"""

from __future__ import annotations
from datetime import date
from decimal import Decimal
import pytest
from core.domain.enums import SpatialDirection, ValueType
from core.domain.models import FieldDefinition, SpatialRelation
from core.parsing.template.value_converter import ValueConverter


def _make_field(
    field_name: str = "company_name",
    value_type: ValueType = ValueType.TEXT,
    date_format: str | None = None,
    decimal_format: dict[str, str] | None = None,
) -> FieldDefinition:
    """Helper: dựng 1 FieldDefinition tối giản, hợp lệ, chỉ để phục vụ
    dispatch qua ValueConverter.convert() - các field khác (section,
    key_tokens, spatial_relation, value_pattern) không ảnh hưởng logic
    đang test, dùng giá trị placeholder hợp lệ bất kỳ.
    """
    return FieldDefinition(
        field_name=field_name,
        section="header",
        value_type=value_type,
        identification_weight=0.0,
        key_tokens=("dummy",),
        fuzzy_threshold=85,
        spatial_relation=SpatialRelation(
            direction=SpatialDirection.RIGHT,
            max_distance=0.5,
            axis_tolerance=0.01,
        ),
        value_pattern=".+",
        date_format=date_format,
        decimal_format=decimal_format,
    )


class TestConvertDispatch:
    """convert() phải dispatch đúng theo field.value_type, và chặn
    raw_text rỗng/None sớm - trước khi gọi bất kỳ _to_xxx() nào."""

    def test_empty_string_returns_none(self) -> None:
        field = _make_field(value_type=ValueType.TEXT)
        assert ValueConverter.convert("", field) is None

    def test_none_returns_none(self) -> None:
        field = _make_field(value_type=ValueType.TEXT)
        assert ValueConverter.convert(None, field) is None  # type: ignore[arg-type]

    def test_text_dispatch(self) -> None:
        field = _make_field(field_name="company_name", value_type=ValueType.TEXT)
        assert ValueConverter.convert("  Cong ty ABC  ", field) == "Cong ty ABC"

    def test_decimal_dispatch(self) -> None:
        field = _make_field(field_name="subtotal", value_type=ValueType.DECIMAL)
        assert ValueConverter.convert("500000", field) == Decimal("500000")

    def test_date_dispatch(self) -> None:
        field = _make_field(
            field_name="invoice_date", value_type=ValueType.DATE, date_format="%d/%m/%Y"
        )
        assert ValueConverter.convert("15/08/2026", field) == date(2026, 8, 15)


class TestToText:
    def test_strips_surrounding_whitespace(self) -> None:
        assert ValueConverter._to_text("  Cong ty TNHH ABC  ") == "Cong ty TNHH ABC"

    def test_whitespace_only_returns_none(self) -> None:
        assert ValueConverter._to_text("   ") is None


class TestStripCurrencySuffix:
    """7 biến thể VND (ADR-051), chia 2 nhóm rủi ro."""

    def test_strips_vnd_case_insensitive(self) -> None:
        assert ValueConverter._strip_currency_suffix("4,842,303VND") == "4,842,303"

    def test_strips_dong_symbol(self) -> None:
        assert ValueConverter._strip_currency_suffix("100₫") == "100"

    def test_strips_dong_symbol_with_space(self) -> None:
        # .strip() sau khi cắt suffix phải dọn khoảng trắng còn sót.
        assert ValueConverter._strip_currency_suffix("100 ₫") == "100"

    def test_strips_single_char_d_after_digit(self) -> None:
        assert ValueConverter._strip_currency_suffix("50000đ") == "50000"

    def test_strips_single_char_D_uppercase_after_digit(self) -> None:
        assert ValueConverter._strip_currency_suffix("50000Đ") == "50000"

    def test_protects_single_char_d_not_after_digit(self) -> None:
        # 'Đ' đứng sau ký tự chữ (không phải chữ số) - KHÔNG được strip,
        # đúng ràng buộc vị trí của ADR-051.
        assert ValueConverter._strip_currency_suffix("ABCĐ") == "ABCĐ"

    def test_protects_lone_single_char_suffix(self) -> None:
        # len(normalized) == 1 -> điều kiện len(normalized) > 1 fail,
        # không strip.
        assert ValueConverter._strip_currency_suffix("đ") == "đ"

    def test_no_suffix_unchanged(self) -> None:
        assert ValueConverter._strip_currency_suffix("12345") == "12345"


class TestToDecimalDefaultFormat:
    """Happy path với decimal_format mặc định VN (thousand='.', decimal=',')."""

    def test_full_thousand_and_decimal(self) -> None:
        assert ValueConverter._to_decimal("1.234.567,89", None) == Decimal("1234567.89")

    def test_integer_no_separator(self) -> None:
        assert ValueConverter._to_decimal("500000", None) == Decimal("500000")

    def test_decimal_only_no_thousand(self) -> None:
        assert ValueConverter._to_decimal("0,05", None) == Decimal("0.05")


class TestToDecimalOverrideFormat:
    """Override decimal_format (ADR-051 - dữ liệu test dùng ngược mặc định
    VN: thousand=',', decimal='.') - khớp cấu hình thật của 3 field tiền
    tệ trong sample_invoice_v1.json."""

    _FORMAT = {"thousand_separator": ",", "decimal_separator": "."}

    def test_thousand_only(self) -> None:
        assert ValueConverter._to_decimal("19,188,159", self._FORMAT) == Decimal("19188159")

    def test_thousand_and_decimal(self) -> None:
        assert ValueConverter._to_decimal("4842303.50", self._FORMAT) == Decimal("4842303.50")


class TestToDecimalPercentage:
    """Strip '%' cuối chuỗi + chia 100 (ADR-043)."""

    def test_integer_percentage(self) -> None:
        assert ValueConverter._to_decimal("5%", None) == Decimal("0.05")

    def test_decimal_percentage_default_format(self) -> None:
        # "12,5%" theo mặc định VN (',' là decimal) = 12.5% = 0.125.
        assert ValueConverter._to_decimal("12,5%", None) == Decimal("0.125")


class TestToDecimalCurrencySuffix:
    """Tích hợp strip suffix (ADR-051) + convert Decimal, dùng
    decimal_format override khớp cấu hình thật của field tiền tệ."""

    _FORMAT = {"thousand_separator": ",", "decimal_separator": "."}

    def test_vnd_suffix_with_thousand_separators(self) -> None:
        assert ValueConverter._to_decimal("4,842,303VND", self._FORMAT) == Decimal("4842303")

    def test_dong_symbol_no_separator(self) -> None:
        assert ValueConverter._to_decimal("100₫", self._FORMAT) == Decimal("100")

    def test_single_char_dong_after_digit(self) -> None:
        assert ValueConverter._to_decimal("50,000đ", self._FORMAT) == Decimal("50000")


class TestLooksAmbiguous:
    """6 dấu hiệu khả nghi (ADR-052) - mỗi test cô lập đúng 1 dấu hiệu,
    xác nhận các dấu hiệu khác không vô tình trigger trước."""

    def test_not_ambiguous_valid_vn_format(self) -> None:
        assert ValueConverter._looks_ambiguous("1.234.567,89", ",") is False

    def test_not_ambiguous_no_separators(self) -> None:
        assert ValueConverter._looks_ambiguous("500000", ",") is False

    def test_signal_leading_separator(self) -> None:
        assert ValueConverter._looks_ambiguous(",123", ",") is True

    def test_signal_trailing_separator(self) -> None:
        assert ValueConverter._looks_ambiguous("123,", ",") is True

    def test_signal_double_punctuation(self) -> None:
        assert ValueConverter._looks_ambiguous("1,,23", ",") is True

    def test_signal_decimal_separator_repeated(self) -> None:
        # Đây chính là case thật của ADR-051 ("4,842,303") nếu KHÔNG có
        # decimal_format override - decimal_sep mặc định "," xuất hiện
        # 2 lần -> bị flag khả nghi (đúng thiết kế, xem TestNormalizeNumberSeparators
        # bên dưới để thấy hệ quả của _normalize_number_separators() trên
        # đúng chuỗi này).
        assert ValueConverter._looks_ambiguous("4,842,303", ",") is True

    def test_signal_mixed_separators_last_not_decimal(self) -> None:
        assert ValueConverter._looks_ambiguous("1.234,56.78", ",") is True

    def test_signal_decimal_tail_too_long(self) -> None:
        # NumberRepair.DECIMAL_TAIL_MAX_LENGTH = 3; cụm cuối "5678" dài 4.
        assert ValueConverter._looks_ambiguous("1.234,5678", ",") is True

    def test_signal_thousand_group_not_three_digits(self) -> None:
        assert ValueConverter._looks_ambiguous("1.23.456", ",") is True


class TestNormalizeNumberSeparators:
    """Heuristic phục hồi (ADR-052) - chỉ chạy sau khi _looks_ambiguous()
    đã xác nhận khả nghi."""

    def test_last_group_short_becomes_decimal(self) -> None:
        # Cụm cuối "567" dài 3, nằm trong DECIMAL_TAIL_MAX_LENGTH -> coi
        # là phần thập phân. ĐÂY LÀ RANH GIỚI ĐÃ GHI NHẬN Ở ADR-052 KNOWN
        # LIMITATIONS: nếu "567" thực ra là 1 nhóm nghìn hợp lệ (không
        # phải phần thập phân), kết quả này SAI - nhưng không có đủ tín
        # hiệu cấu trúc để phân biệt 2 khả năng. Test này xác nhận hành
        # vi HIỆN TẠI đã biết, không phải bug mới phát hiện.
        assert ValueConverter._normalize_number_separators("1,234.567") == "1234.567"

    def test_last_group_too_long_strips_all(self) -> None:
        assert ValueConverter._normalize_number_separators("1,234,5678") == "12345678"

    def test_boundary_separator_strips_all(self) -> None:
        assert ValueConverter._normalize_number_separators(",123,456") == "123456"

    def test_no_separators_returns_unchanged(self) -> None:
        assert ValueConverter._normalize_number_separators("123456") == "123456"


class TestToDate:
    def test_valid_date(self) -> None:
        assert ValueConverter._to_date("15/08/2026", "%d/%m/%Y") == date(2026, 8, 15)

    def test_valid_date_different_format(self) -> None:
        assert ValueConverter._to_date("2026-08-15", "%Y-%m-%d") == date(2026, 8, 15)

    def test_strips_whitespace_before_parsing(self) -> None:
        assert ValueConverter._to_date("  15/08/2026  ", "%d/%m/%Y") == date(2026, 8, 15)

    def test_mismatched_format_returns_none(self) -> None:
        assert ValueConverter._to_date("15/08/2026", "%Y-%m-%d") is None

    def test_no_date_format_returns_none(self) -> None:
        assert ValueConverter._to_date("15/08/2026", None) is None


class TestConvertNeverRaises:
    """ADR-032: ValueConverter không bao giờ raise Exception - convert
    thất bại phải trả None, không phải để Exception thoát ra ngoài."""

    @pytest.mark.parametrize(
        "raw_text",
        [
            "abc%%%",
            "12..,,34",
            "---",
            ":::",
            "VNDVNDVND",
            "%",
            "1.2.3.4.5,6,7",
            "\t\n  ",
        ],
    )
    def test_decimal_never_raises(self, raw_text: str) -> None:
        field = _make_field(field_name="subtotal", value_type=ValueType.DECIMAL)
        result = ValueConverter.convert(raw_text, field)
        assert result is None or isinstance(result, Decimal)

    @pytest.mark.parametrize("raw_text", ["abc", "12/13/9999", "not-a-date", "!!!"])
    def test_date_never_raises(self, raw_text: str) -> None:
        field = _make_field(
            field_name="invoice_date", value_type=ValueType.DATE, date_format="%d/%m/%Y"
        )
        result = ValueConverter.convert(raw_text, field)
        assert result is None or isinstance(result, date)

    @pytest.mark.parametrize("raw_text", ["   ", "\t\t", "\n"])
    def test_text_never_raises(self, raw_text: str) -> None:
        field = _make_field(field_name="company_name", value_type=ValueType.TEXT)
        result = ValueConverter.convert(raw_text, field)
        assert result is None or isinstance(result, str)
