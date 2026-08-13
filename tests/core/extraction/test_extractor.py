"""
Unit test cho Extractor._rotate_bbox() (core/extractor.py).

Bối cảnh (xem ADR-028, SESSION_SUMMARIES.md Session 2026-07-31):
page.get_text("words") trả tọa độ theo khung KHÔNG XOAY của trang, trong
khi page.rect (nguồn của PageStatistics.width/height) và page.get_pixmap()
đều phản ánh khung ĐÃ XOAY (visual). _rotate_bbox() là nơi duy nhất hòa
giải 2 khung tọa độ này cho luồng Digital.

_rotate_bbox() là @staticmethod, chỉ nhận giá trị số thuần túy - không
phụ thuộc PyMuPDF/OCREngine/I-O nào, nên gọi trực tiếp được, không cần
khởi tạo Extractor() (tránh việc __init__ gọi OCREngine() -> có thể
raise FileNotFoundError nếu máy chạy test chưa có tessdata_best).

Quy ước tọa độ trang gốc dùng xuyên suốt file test này:
    Wu = 800  (width của trang KHÔNG XOAY)
    Hu = 600  (height của trang KHÔNG XOAY)
    bbox mẫu = (100, 50, 200, 120)  (1 "từ" gần góc trên-trái)

Với rotation=90 hoặc 270, trang hiển thị (rotated) có width/height hoán
đổi so với trang gốc: rotated_width = Hu, rotated_height = Wu.
Với rotation=180, kích thước không đổi: rotated_width = Wu,
rotated_height = Hu.

Toàn bộ giá trị "expected" trong file này được suy diễn độc lập bằng
hình học (rotate point quanh 4 góc bbox, lấy lại bounding box), KHÔNG
copy ngược từ code đang test - xem giải trình chi tiết trong nội dung
thảo luận đã chốt trước khi viết file này.
"""

from __future__ import annotations
from core.extraction.extractor import Extractor


# Kích thước trang KHÔNG XOAY dùng chung cho mọi test case.
_UNROTATED_WIDTH = 800.0
_UNROTATED_HEIGHT = 600.0

# 1 bbox mẫu trong khung KHÔNG XOAY - đại diện 1 WordToken gần góc
# trên-trái của trang gốc.
_SAMPLE_BBOX = (100.0, 50.0, 200.0, 120.0)

# bbox phủ toàn bộ trang KHÔNG XOAY - dùng cho edge case Mục 7.
_FULL_PAGE_BBOX = (0.0, 0.0, _UNROTATED_WIDTH, _UNROTATED_HEIGHT)


class TestRotateBboxZeroDegrees:
    """rotation=0: trang không xoay, bbox phải giữ nguyên không đổi."""

    def test_sample_bbox_unchanged(self) -> None:
        result = Extractor._rotate_bbox(
            _SAMPLE_BBOX,
            rotation=0,
            rotated_width=_UNROTATED_WIDTH,
            rotated_height=_UNROTATED_HEIGHT,
        )
        assert result == _SAMPLE_BBOX


class TestRotateBbox90Degrees:
    """
    rotation=90 (xoay 90 độ theo chiều kim đồng hồ khi hiển thị).

    rotated_width = Hu = 600, rotated_height = Wu = 800 (hoán đổi).

    Suy diễn tay (rotate 4 góc bbox quanh gốc, dùng công thức điểm
    new_x = Hu - y, new_y = x cho xoay 90 CW):
        (100,50)  -> (550, 100)
        (200,50)  -> (550, 200)
        (200,120) -> (480, 200)
        (100,120) -> (480, 100)
    Bounding box của 4 điểm trên: x thuộc [480, 550], y thuộc [100, 200].
    """

    _ROTATED_WIDTH = _UNROTATED_HEIGHT  # 600
    _ROTATED_HEIGHT = _UNROTATED_WIDTH  # 800

    def test_sample_bbox_matches_hand_derived_geometry(self) -> None:
        result = Extractor._rotate_bbox(
            _SAMPLE_BBOX,
            rotation=90,
            rotated_width=self._ROTATED_WIDTH,
            rotated_height=self._ROTATED_HEIGHT,
        )
        assert result == (480.0, 100.0, 550.0, 200.0)

    def test_full_page_bbox_maps_to_full_rotated_page(self) -> None:
        result = Extractor._rotate_bbox(
            _FULL_PAGE_BBOX,
            rotation=90,
            rotated_width=self._ROTATED_WIDTH,
            rotated_height=self._ROTATED_HEIGHT,
        )
        assert result == (0.0, 0.0, self._ROTATED_WIDTH, self._ROTATED_HEIGHT)


class TestRotateBbox180Degrees:
    """
    rotation=180.

    rotated_width = Wu = 800, rotated_height = Hu = 600 (không hoán đổi).

    Suy diễn tay (phép đối xứng tâm quanh tâm trang):
        new_bbox = (Wu - x1, Hu - y1, Wu - x0, Hu - y0)
                 = (800-200, 600-120, 800-100, 600-50)
                 = (600, 480, 700, 550)
    """

    _ROTATED_WIDTH = _UNROTATED_WIDTH  # 800
    _ROTATED_HEIGHT = _UNROTATED_HEIGHT  # 600

    def test_sample_bbox_matches_hand_derived_geometry(self) -> None:
        result = Extractor._rotate_bbox(
            _SAMPLE_BBOX,
            rotation=180,
            rotated_width=self._ROTATED_WIDTH,
            rotated_height=self._ROTATED_HEIGHT,
        )
        assert result == (600.0, 480.0, 700.0, 550.0)

    def test_full_page_bbox_maps_to_full_rotated_page(self) -> None:
        result = Extractor._rotate_bbox(
            _FULL_PAGE_BBOX,
            rotation=180,
            rotated_width=self._ROTATED_WIDTH,
            rotated_height=self._ROTATED_HEIGHT,
        )
        assert result == (0.0, 0.0, self._ROTATED_WIDTH, self._ROTATED_HEIGHT)


class TestRotateBbox270Degrees:
    """
    rotation=270 (tương đương xoay 90 độ ngược chiều kim đồng hồ).

    rotated_width = Hu = 600, rotated_height = Wu = 800 (hoán đổi, giống
    trường hợp 90 độ - kích thước hiển thị hoán đổi ở cả 2 hướng).

    Suy diễn tay (công thức điểm new_x = y, new_y = Wu - x cho xoay 90
    CCW, với Wu = unrotated_width = 800):
        (100,50)  -> (50, 700)
        (200,50)  -> (50, 600)
        (200,120) -> (120, 600)
        (100,120) -> (120, 700)
    Bounding box: x thuộc [50, 120], y thuộc [600, 700].
    """

    _ROTATED_WIDTH = _UNROTATED_HEIGHT  # 600
    _ROTATED_HEIGHT = _UNROTATED_WIDTH  # 800

    def test_sample_bbox_matches_hand_derived_geometry(self) -> None:
        result = Extractor._rotate_bbox(
            _SAMPLE_BBOX,
            rotation=270,
            rotated_width=self._ROTATED_WIDTH,
            rotated_height=self._ROTATED_HEIGHT,
        )
        assert result == (50.0, 600.0, 120.0, 700.0)

    def test_full_page_bbox_maps_to_full_rotated_page(self) -> None:
        result = Extractor._rotate_bbox(
            _FULL_PAGE_BBOX,
            rotation=270,
            rotated_width=self._ROTATED_WIDTH,
            rotated_height=self._ROTATED_HEIGHT,
        )
        assert result == (0.0, 0.0, self._ROTATED_WIDTH, self._ROTATED_HEIGHT)


class TestRotateBboxRoundTrip:
    """
    Bất biến toán học độc lập với việc suy diễn "đúng chiều xoay" ở trên
    có đúng hay không: xoay đi rồi xoay ngược lại phải trả về đúng bbox
    gốc. Bắt được lỗi dấu (sign error) nếu công thức bị đổi sai trong
    tương lai (regression), không chỉ xác nhận trạng thái hiện tại.
    """

    def test_90_then_270_returns_original_bbox(self) -> None:
        # Bước 1: xoay 90 độ, trang gốc (800x600) -> trang hiển thị (600x800).
        rotated_once = Extractor._rotate_bbox(
            _SAMPLE_BBOX,
            rotation=90,
            rotated_width=_UNROTATED_HEIGHT,  # 600
            rotated_height=_UNROTATED_WIDTH,  # 800
        )

        # Bước 2: xoay tiếp 270 độ (90 + 270 = 360 = identity), coi khung
        # trung gian (600x800) là khung "chưa xoay", trả về khung gốc
        # (800x600).
        rotated_back = Extractor._rotate_bbox(
            rotated_once,
            rotation=270,
            rotated_width=_UNROTATED_WIDTH,   # 800
            rotated_height=_UNROTATED_HEIGHT,  # 600
        )

        assert rotated_back == _SAMPLE_BBOX

    def test_180_then_180_returns_original_bbox(self) -> None:
        # 180 + 180 = 360 = identity; kích thước không hoán đổi ở bước nào.
        rotated_once = Extractor._rotate_bbox(
            _SAMPLE_BBOX,
            rotation=180,
            rotated_width=_UNROTATED_WIDTH,
            rotated_height=_UNROTATED_HEIGHT,
        )
        rotated_back = Extractor._rotate_bbox(
            rotated_once,
            rotation=180,
            rotated_width=_UNROTATED_WIDTH,
            rotated_height=_UNROTATED_HEIGHT,
        )

        assert rotated_back == _SAMPLE_BBOX
