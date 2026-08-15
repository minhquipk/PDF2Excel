"""
Phát hiện phần cứng CPU và tính số luồng khuyến nghị cho xử lý đa luồng.

Quy ước:
- Chỉ dùng thư viện chuẩn Python (os.cpu_count()) - không phụ thuộc Qt,
  không phụ thuộc bất kỳ thư viện ngoài nào (MULTI_THREAD_SPECIFICATION.md
  §2.1 - GPU bị loại trừ có chủ đích ở giai đoạn này).
- Hàm thuần túy (pure function), không side-effect, dễ unit test độc lập
  với UI/Worker/QThreadPool.
- Không chứa Business Logic khác ngoài tính toán số luồng.
"""

from __future__ import annotations
import os

# Trần tối đa gợi ý (MULTI_THREAD_SPECIFICATION.md §2.2) - tránh nghẽn I/O
# và tràn bộ nhớ RAM do render ảnh 450 DPI song song (Image.DPI, xem
# core/domain/constants.py::Image).
_MAX_RECOMMENDED_THREADS = 8

# Ngưỡng phân nhóm cpu_count theo công thức đã chốt trong đặc tả.
_LOW_CORE_THRESHOLD = 2
_MID_CORE_THRESHOLD = 4

# Hệ số dùng cho nhóm cpu_count > 4.
_HIGH_CORE_RATIO = 0.75


def get_cpu_info() -> tuple[int, int]:
    """
    Phát hiện số CPU core và tính số luồng khuyến nghị.

    Returns
    -------
    tuple[int, int]
        (total_cores, recommended_threads).
        - total_cores: số CPU core phát hiện được qua os.cpu_count();
          fallback về 1 nếu hệ thống không xác định được (cpu_count()
          trả None - trường hợp hiếm, một số môi trường container/sandbox
          hạn chế).
        - recommended_threads: số luồng gợi ý, theo công thức:
            <= 2 core   -> 1 luồng
            3-4 core    -> 2 luồng
            > 4 core    -> min(8, max(2, floor(cpu_count * 0.75)))
          Khi cpu_count() trả None, recommended_threads luôn là 1 (an
          toàn nhất, không giả định phần cứng).
    """
    cpu_count = os.cpu_count()

    if cpu_count is None:
        return 1, 1

    total_cores = cpu_count

    if cpu_count <= _LOW_CORE_THRESHOLD:
        recommended_threads = 1
    elif cpu_count <= _MID_CORE_THRESHOLD:
        recommended_threads = 2
    else:
        recommended_threads = min(
            _MAX_RECOMMENDED_THREADS,
            max(2, int(cpu_count * _HIGH_CORE_RATIO)),
        )

    return total_cores, recommended_threads
