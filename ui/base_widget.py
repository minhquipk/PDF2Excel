"""
Lớp cơ sở cho toàn bộ Widget trong ứng dụng.
Quy ước vòng đời:

    __init__()
        │
        ├── _create_widgets()
        ├── _create_layout()
        └── _connect_signals()

Mọi Widget trong dự án đều kế thừa BaseWidget.
Không viết Business Logic trong lớp này.
"""

from __future__ import annotations
from typing import Optional
from PySide6.QtWidgets import QWidget


class BaseWidget(QWidget):
    """Base class cho tất cả Widget của ứng dụng."""
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self._create_widgets()
        self._create_layout()
        self._connect_signals()

    # ==========================================================
    # Protected Life Cycle
    # ==========================================================

    def _create_widgets(self) -> None:
        """Khởi tạo các widget con."""
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement _create_widgets()."
        )

    def _create_layout(self) -> None:
        """Thiết lập layout."""
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement _create_layout()."
        )

    def _connect_signals(self) -> None:
        """Kết nối toàn bộ signal/slot."""
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement _connect_signals()."
        )

    # ==========================================================
    # Public API
    # ==========================================================

    def clear(self) -> None:
        """
        Xóa dữ liệu hiển thị.
        Widget con có thể override nếu cần.
        """
        pass

    def reset(self) -> None:
        """
        Đưa Widget về trạng thái ban đầu.
        Widget con có thể override nếu cần.
        """
        pass
