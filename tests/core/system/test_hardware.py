"""
Unit test cho core/system/hardware.py::get_cpu_info().

Bối cảnh: get_cpu_info() là pure function, chỉ phụ thuộc os.cpu_count() -
tương tự nguyên tắc test đã áp dụng cho Extractor._rotate_bbox() và
ValueConverter (xem tests/core/extraction/test_extractor.py,
tests/core/parsing/template/test_value_converter.py): giá trị "expected"
tự suy diễn tay theo đúng công thức MULTI_THREAD_SPECIFICATION.md §2.2,
KHÔNG copy ngược từ code đang test.

Dùng unittest.mock.patch("os.cpu_count") để kiểm soát giá trị trả về,
tránh phụ thuộc vào số core thật của máy đang chạy test (đề đạt yêu cầu
"Đạt 100% test case cho các ngưỡng CPU: 1, 2, 4, 8, 16, 32, 64 cores và
case None" - MULTI_THREAD_SPECIFICATION.md §6 Bước 1).
"""

from __future__ import annotations
from unittest.mock import patch
import pytest
from core.system.hardware import get_cpu_info


class TestGetCpuInfoNoneCase:
    """cpu_count() trả None - môi trường không xác định được số core."""

    def test_none_returns_safe_fallback(self) -> None:
        with patch("os.cpu_count", return_value=None):
            assert get_cpu_info() == (1, 1)


class TestGetCpuInfoLowCoreGroup:
    """<= 2 core -> luôn 1 luồng khuyến nghị."""

    @pytest.mark.parametrize("cpu_count", [1, 2])
    def test_recommends_one_thread(self, cpu_count: int) -> None:
        with patch("os.cpu_count", return_value=cpu_count):
            assert get_cpu_info() == (cpu_count, 1)


class TestGetCpuInfoMidCoreGroup:
    """3-4 core -> luôn 2 luồng khuyến nghị."""

    @pytest.mark.parametrize("cpu_count", [3, 4])
    def test_recommends_two_threads(self, cpu_count: int) -> None:
        with patch("os.cpu_count", return_value=cpu_count):
            assert get_cpu_info() == (cpu_count, 2)


class TestGetCpuInfoHighCoreGroup:
    """
    > 4 core -> min(8, max(2, floor(cpu_count * 0.75))).

    Suy diễn tay từng case (không chạy code rồi copy ngược):
        cpu_count=8  -> floor(8*0.75)=6   -> min(8, max(2,6))=6
        cpu_count=16 -> floor(16*0.75)=12 -> min(8, max(2,12))=8 (chạm trần)
        cpu_count=32 -> floor(32*0.75)=24 -> min(8, max(2,24))=8 (chạm trần)
        cpu_count=64 -> floor(64*0.75)=48 -> min(8, max(2,48))=8 (chạm trần)
    """

    @pytest.mark.parametrize(
        "cpu_count, expected_recommended",
        [
            (8, 6),
            (16, 8),
            (32, 8),
            (64, 8),
        ],
    )
    def test_matches_hand_derived_formula(
        self, cpu_count: int, expected_recommended: int
    ) -> None:
        with patch("os.cpu_count", return_value=cpu_count):
            assert get_cpu_info() == (cpu_count, expected_recommended)


class TestGetCpuInfoBoundaryConsistency:
    """
    Xác nhận trần MAX_RECOMMENDED_THREADS=8 không bao giờ bị vượt qua,
    bất kể cpu_count lớn tới đâu - bất biến độc lập với việc suy diễn
    "công thức đúng" ở trên có đúng hay không (bắt regression nếu hằng
    số trần bị đổi sai trong tương lai).
    """

    def test_recommended_never_exceeds_cap_for_very_high_core_count(self) -> None:
        with patch("os.cpu_count", return_value=256):
            _, recommended = get_cpu_info()
            assert recommended <= 8

    def test_recommended_at_least_two_when_above_mid_threshold(self) -> None:
        # cpu_count=5 là biên ngay trên _MID_CORE_THRESHOLD=4 -
        # floor(5*0.75)=3, vẫn > max(2,...) nên recommended=3.
        with patch("os.cpu_count", return_value=5):
            assert get_cpu_info() == (5, 3)
