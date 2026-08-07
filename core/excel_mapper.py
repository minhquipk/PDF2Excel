"""
Đọc Excel Mapping Definition (mapping.json), validate, build thành
ExcelMapping (frozen dataclass), sẵn sàng cho ExcelWriter.

Quy ước:
- KHÁC TemplateLoader (fail-soft per file, ADR-031): ở đây lỗi là FATAL.
  mapping.json là điều kiện tiên quyết duy nhất để ExcelWriter ghi được bất
  kỳ dữ liệu nào - không tồn tại khái niệm "một phần hợp lệ, phần còn lại bỏ
  qua" như với nhiều template JSON. Mọi lỗi đều raise MappingError.
"""

from __future__ import annotations
import json
from dataclasses import fields
from pathlib import Path
from typing import Any
from core.models import ExcelMapping, InvoiceInfo


class MappingError(Exception):
    """mapping.json không tồn tại, sai cú pháp JSON, hoặc sai schema."""


class Mapper:
    """Đọc và validate một file Excel Mapping Definition (mapping.json)."""

    def __init__(self, mapping_path: Path) -> None:
        self._mapping_path = Path(mapping_path)

    def load(self) -> ExcelMapping:
        """
        Đọc mapping_path -> ExcelMapping.
        Raises
        ------
        MappingError
            Nếu file không tồn tại, không đọc được, sai cú pháp JSON, hoặc
            schema không hợp lệ (thiếu key, sai kiểu, field_name không tồn
            tại trong InvoiceInfo).
        """
        try:
            with self._mapping_path.open("r", encoding="utf-8") as file:
                raw = json.load(file)
        except OSError as error:
            raise MappingError(
                f"Không đọc được file mapping '{self._mapping_path}': {error}"
            ) from error
        except json.JSONDecodeError as error:
            raise MappingError(
                f"File mapping '{self._mapping_path}' sai cú pháp JSON: {error}"
            ) from error

        return self._build_mapping(raw)

    @staticmethod
    def _build_mapping(raw: dict[str, Any]) -> ExcelMapping:
        try:
            table = raw["table"]
            columns = raw["columns"]
        except KeyError as error:
            raise MappingError(f"mapping.json thiếu key bắt buộc: {error}") from error

        if not isinstance(table, str) or not table.strip():
            raise MappingError("'table' phải là chuỗi không rỗng.")

        if not isinstance(columns, dict) or not columns:
            raise MappingError("'columns' phải là object không rỗng.")

        valid_field_names = {f.name for f in fields(InvoiceInfo)}
        for column_name, field_name in columns.items():
            if field_name not in valid_field_names:
                raise MappingError(
                    f"Cột '{column_name}' ánh xạ tới field '{field_name}' "
                    f"không tồn tại trong InvoiceInfo. "
                    f"Các field hợp lệ: {sorted(valid_field_names)}."
                )

        return ExcelMapping(table=table, columns=columns)
