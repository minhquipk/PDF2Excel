"""
Đọc Template Definition từ file JSON, validate, build thành TemplateDefinition
(frozen dataclass, sẵn sàng cho TemplateMatcher).

Quy ước:
- Không raise ra ngoài khi một file JSON riêng lẻ bị lỗi: log warning, bỏ qua,
  tiếp tục load các template hợp lệ còn lại (Phương án B đã chốt).
- Thư mục templates không tồn tại: log warning, trả về rỗng — không crash app,
  Worker sẽ chạy với Parser không có template nào (mọi PDF -> không xác định
  được template, đối xứng ADR-027 "absence of decision").
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.enums import SpatialDirection, ValueType
from core.models import FieldDefinition, SpatialRelation, TemplateDefinition
from utils.logger import get_logger

logger = get_logger(__name__)

# Các lỗi được coi là "template JSON không hợp lệ" -> bỏ qua, không dừng batch.
_TEMPLATE_ERROR_TYPES = (
    json.JSONDecodeError,
    KeyError,
    ValueError,
    TypeError,
    UnicodeDecodeError,
    OSError,
)


class TemplateLoader:
    """Đọc toàn bộ Template Definition JSON trong một thư mục."""

    def __init__(self, templates_dir: Path) -> None:
        self._templates_dir = Path(templates_dir)

    def load_all(self) -> tuple[TemplateDefinition, ...]:
        """
        Load mọi file .json hợp lệ trong templates_dir.

        File lỗi (JSON sai cú pháp, thiếu field, sai kiểu, sai enum...) sẽ được
        log warning và bỏ qua, không ảnh hưởng đến việc load các template khác.
        """
        if not self._templates_dir.is_dir():
            logger.warning(
                "Thư mục template không tồn tại: %s. Không có template nào được load.",
                self._templates_dir,
            )
            return ()

        templates: list[TemplateDefinition] = []
        for json_path in sorted(self._templates_dir.glob("*.json")):
            try:
                template = self._load_one(json_path)
            except _TEMPLATE_ERROR_TYPES as error:
                logger.warning(
                    "Bỏ qua template lỗi '%s': %s: %s",
                    json_path.name,
                    type(error).__name__,
                    error,
                )
                continue

            templates.append(template)
            logger.info(
                "Đã load template '%s' (id=%s, version=%s).",
                json_path.name,
                template.template_id,
                template.version,
            )

        return tuple(templates)

    def _load_one(self, json_path: Path) -> TemplateDefinition:
        """Parse một file JSON -> TemplateDefinition. Raise nếu sai schema."""
        with json_path.open("r", encoding="utf-8") as file:
            raw = json.load(file)

        return self._build_template(raw)

    @staticmethod
    def _build_template(raw: dict[str, Any]) -> TemplateDefinition:
        raw_fields = raw["fields"]

        if not isinstance(raw_fields, list) or not raw_fields:
            raise ValueError("Template phải có ít nhất 1 field trong 'fields'.")

        fields = tuple(
            TemplateLoader._build_field(raw_field) for raw_field in raw_fields
        )

        return TemplateDefinition(
            template_id=raw["template_id"],
            version=int(raw["version"]),
            description=raw.get("description", ""),
            fields=fields,
        )

    @staticmethod
    def _build_field(raw_field: dict[str, Any]) -> FieldDefinition:
        key_tokens = raw_field["key_tokens"]
        if not isinstance(key_tokens, list) or not key_tokens:
            raise ValueError(
                f"key_tokens của field '{raw_field.get('field_name')}' "
                "phải là danh sách không rỗng."
            )

        return FieldDefinition(
            field_name=raw_field["field_name"],
            value_type=ValueType(raw_field["value_type"]),
            identification_weight=float(raw_field["identification_weight"]),
            key_tokens=tuple(key_tokens),
            fuzzy_threshold=int(raw_field["fuzzy_threshold"]),
            spatial_relation=TemplateLoader._build_spatial_relation(
                raw_field["spatial_relation"]
            ),
            value_pattern=raw_field["value_pattern"],
            date_format=raw_field.get("date_format"),
            decimal_format=raw_field.get("decimal_format"),
        )

    @staticmethod
    def _build_spatial_relation(raw_spatial: dict[str, Any]) -> SpatialRelation:
        return SpatialRelation(
            direction=SpatialDirection(raw_spatial["direction"]),
            max_distance=float(raw_spatial["max_distance"]),
            axis_tolerance=float(raw_spatial["axis_tolerance"]),
        )
