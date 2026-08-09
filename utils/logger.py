"""
Logger dùng chung cho toàn bộ ứng dụng.

Quy ước:
- Chỉ cấu hình logging, không chứa Business Logic.
- Mọi module gọi get_logger(__name__) để lấy logger đã cấu hình sẵn.
- Không tự tạo handler riêng lẻ ở module khác, tránh log trùng lặp.
"""

from __future__ import annotations
import logging
from config import LOG_DIR
from core.constants import Logging as LoggingConfig

_CONFIGURED = False


def _configure_root() -> None:
    """Cấu hình root logger một lần duy nhất (console + file handler)."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    formatter = logging.Formatter(
        fmt=LoggingConfig.FORMAT,
        datefmt=LoggingConfig.DATE_FORMAT,
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(
        LOG_DIR / LoggingConfig.FILE_NAME,
        mode="w",
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(LoggingConfig.LEVEL)
    root.addHandler(console_handler)
    root.addHandler(file_handler)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """
    Trả về logger đã cấu hình sẵn cho module gọi.

    Parameters
    ----------
    name:
        Thường truyền __name__ của module gọi.

    Returns
    -------
    logging.Logger
    """
    _configure_root()
    return logging.getLogger(name)
