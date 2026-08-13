"""
Chọn Template Definition khớp nhất với một ExtractionResult, sau đó trích
Value cho từng Field.

Thuật toán (theo thiết kế Parser đã thống nhất):
1. Key Matching: gom WordToken thành dòng/cụm từ (Line/Phrase Clustering),
   fuzzy-match với key_tokens của mỗi FieldDefinition (rapidfuzz).
2. Score + Decision: chấm điểm mỗi TemplateDefinition theo tổng
   identification_weight của các field có Key khớp; chọn template thắng
   rõ ràng, có tie margin - đối xứng cách PDFDetector._decide_mode() quyết
   định AnalysisMode (Evidence -> Score -> Decision).
3. Windowing: dựng cửa sổ tìm kiếm từ bbox Key theo SpatialRelation
   (direction + max_distance + axis_tolerance).
4. Value Matching: lọc WordToken trong cửa sổ khớp value_pattern (regex),
   tie-break bằng khoảng cách Euclidean tới Key gần nhất.

Quy ước:
- Không tự quyết định AnalysisMode hay đọc PDF; chỉ nhận ExtractionResult.
- re.compile() được cache tại đây (tầng logic), KHÔNG đặt trong models.py
  (models.py giữ quy ước "Không chứa Regex" - xem ghi chú ADR liên quan).
"""

from __future__ import annotations
import re
import unicodedata
from dataclasses import dataclass
from rapidfuzz import fuzz
from core.domain.constants import TemplateMatching
from core.domain.enums import SpatialDirection, ValueType
from core.domain.models import (
    ExtractionResult,
    FieldDefinition,
    SectionDefinition,
    SpatialRelation,
    TemplateDefinition,
    TemplateSelection,
    WordToken,
)


def _strip_diacritics(text: str) -> str:
    """
    Chuẩn hoá tiếng Việt trước khi fuzzy match: loại bỏ dấu thanh/dấu phụ.

    Cần thiết vì rapidfuzz.fuzz.ratio() so sánh theo ký tự (character-level),
    rất nhạy với dấu tiếng Việt - "Mã số thuế" vs "Ma so thue" cho ratio chỉ
    ~70, dưới mọi ngưỡng fuzzy_threshold hợp lý (85-90). Áp dụng cho cả
    key_tokens (JSON) và text thực tế (WordToken) để khớp nhau bất kể bên
    nào có dấu hay không - đặc biệt quan trọng khi OCR làm rớt dấu.

    "Đ"/"đ" phải xử lý riêng vì đây là ký tự Unicode độc lập (Latin Capital/
    Small Letter D with Stroke), không decompose qua NFKD như các dấu khác.
    """
    text = text.replace("Đ", "D").replace("đ", "d")
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(c for c in normalized if not unicodedata.combining(c))


@dataclass(slots=True, frozen=True)
class _Phrase:
    """Cụm từ liền kề trên cùng 1 dòng - cấu trúc nội bộ, chỉ dùng cho Key Matching."""
    text: str
    bbox: tuple[float, float, float, float]
    page_index: int


class TemplateMatcher:
    """Chọn template khớp nhất, sau đó trích Value cho từng Field."""

    def __init__(self, templates: tuple[TemplateDefinition, ...]) -> None:
        self._templates = templates
        self._pattern_cache: dict[str, re.Pattern] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def select_template(self, extraction: ExtractionResult) -> TemplateSelection | None:
        """
        Bước 1 (Key Matching) + Score toàn bộ template trên toàn văn bản.
        Trả None nếu không có template nào đạt ngưỡng hoặc bị tie (ambiguous).
        """
        phrases = self._build_phrases(extraction)

        best_selection: TemplateSelection | None = None
        best_score = -1.0
        second_best_score = -1.0

        for template in self._templates:
            matched_keys, score = self._score_template(template, phrases)

            if score > best_score:
                second_best_score = best_score
                best_score = score
                best_selection = TemplateSelection(
                    template=template,
                    score=score,
                    matched_keys=matched_keys,
                )
            elif score > second_best_score:
                second_best_score = score

        if best_selection is None:
            return None
        if best_score < TemplateMatching.TEMPLATE_MIN_SCORE:
            return None
        if best_score - second_best_score < TemplateMatching.TEMPLATE_TIE_MARGIN:
            return None

        return best_selection

    def extract_fields(
        self,
        selection: TemplateSelection,
        extraction: ExtractionResult,
    ) -> dict[str, str | None]:
        """
        Bước 2 (Windowing) + Bước 3 (Value Matching), dùng lại
        selection.matched_keys - không quét lại Key Matching lần 2.
        """
        results: dict[str, str | None] = {}

        for field_def in selection.template.fields:
            key_position = selection.matched_keys.get(field_def.field_name)
            if key_position is None:
                results[field_def.field_name] = None
                continue

            page_index, key_token = key_position
            page_words = extraction.words_by_page.get(page_index, ())

            window = self._build_window(key_token, field_def.spatial_relation)
            candidates = self._tokens_in_window(page_words, window)
            value = self._select_best_value(candidates, field_def, key_token)
            results[field_def.field_name] = value

        return results

    # ------------------------------------------------------------------
    # Bước 1: Key Matching (Line/Phrase Clustering + Fuzzy Match)
    # ------------------------------------------------------------------

    @staticmethod
    def _build_phrases(extraction: ExtractionResult) -> tuple[_Phrase, ...]:
        """Gom toàn bộ WordToken (mọi trang) thành các cụm từ liền kề."""
        phrases: list[_Phrase] = []
        for page_index, tokens in extraction.words_by_page.items():
            phrases.extend(
                TemplateMatcher._build_phrases_for_page(page_index, tokens)
            )
        return tuple(phrases)

    @staticmethod
    def _build_phrases_for_page(
        page_index: int,
        tokens: tuple[WordToken, ...],
    ) -> list[_Phrase]:
        lines = TemplateMatcher._cluster_lines(tokens)
        phrases: list[_Phrase] = []
        for line in lines:
            phrases.extend(TemplateMatcher._cluster_phrases(line, page_index))
        return phrases

    @staticmethod
    def _cluster_lines(tokens: tuple[WordToken, ...]) -> list[list[WordToken]]:
        """Gom token theo dòng: y_center gần nhau -> cùng dòng, sort theo x."""
        if not tokens:
            return []

        def y_center(t: WordToken) -> float:
            return (t.normalized_bbox[1] + t.normalized_bbox[3]) / 2

        sorted_tokens = sorted(tokens, key=y_center)

        lines: list[list[WordToken]] = []
        current_line: list[WordToken] = [sorted_tokens[0]]
        current_y = y_center(sorted_tokens[0])

        for token in sorted_tokens[1:]:
            ty = y_center(token)
            if abs(ty - current_y) <= TemplateMatching.LINE_Y_TOLERANCE:
                current_line.append(token)
            else:
                lines.append(sorted(current_line, key=lambda t: t.normalized_bbox[0]))
                current_line = [token]
                current_y = ty

        lines.append(sorted(current_line, key=lambda t: t.normalized_bbox[0]))
        return lines

    @staticmethod
    def _cluster_phrases(line: list[WordToken], page_index: int) -> list[_Phrase]:
        """
        Sinh candidate phrase bằng sliding window (1..MAX_KEY_WORDS từ liên
        tiếp), chỉ ghép các token đủ gần nhau (WORD_GAP_TOLERANCE).
        """
        phrases: list[_Phrase] = []
        n = len(line)

        for start in range(n):
            texts = [line[start].text]
            x0, y0, x1, y1 = line[start].normalized_bbox

            phrases.append(
                _Phrase(text=texts[0], bbox=(x0, y0, x1, y1), page_index=page_index)
            )

            limit = min(start + TemplateMatching.MAX_KEY_WORDS, n)
            for end in range(start + 1, limit):
                prev_token = line[end - 1]
                curr_token = line[end]
                gap = curr_token.normalized_bbox[0] - prev_token.normalized_bbox[2]
                if gap > TemplateMatching.WORD_GAP_TOLERANCE:
                    break

                texts.append(curr_token.text)
                cx0, cy0, cx1, cy1 = curr_token.normalized_bbox
                x0 = min(x0, cx0)
                y0 = min(y0, cy0)
                x1 = max(x1, cx1)
                y1 = max(y1, cy1)

                phrases.append(
                    _Phrase(
                        text=" ".join(texts),
                        bbox=(x0, y0, x1, y1),
                        page_index=page_index,
                    )
                )

        return phrases

    @staticmethod
    def _find_key_match(
            key_tokens: tuple[str, ...],
            fuzzy_threshold: int,
            phrases: tuple[_Phrase, ...],
            tie_margin: float | None = None,
    ) -> tuple[int, WordToken] | None:
        """
        Tìm phrase khớp tốt nhất (fuzzy) với key_tokens trong phrases đã cho.
        Dùng chung cho cả Field (tie_margin=None - best-match tuyệt đối,
        hành vi không đổi so với trước) và Section (tie_margin bắt buộc -
        chống va chạm giữa các section header). Trả (page_index, WordToken
        đại diện mang bbox hợp nhất của cụm khớp).
        """
        best_phrase: _Phrase | None = None
        best_ratio = -1.0
        second_best_ratio = -1.0

        for phrase in phrases:
            phrase_normalized = _strip_diacritics(phrase.text.lower())
            for key_text in key_tokens:
                key_normalized = _strip_diacritics(key_text.lower())
                ratio = fuzz.ratio(phrase_normalized, key_normalized)
                if ratio < fuzzy_threshold:
                    continue
                if ratio > best_ratio:
                    second_best_ratio = best_ratio
                    best_ratio = ratio
                    best_phrase = phrase
                elif ratio > second_best_ratio:
                    second_best_ratio = ratio

        if best_phrase is None:
            return None
        if tie_margin is not None and best_ratio - second_best_ratio < tie_margin:
            return None

        representative = WordToken(
            text=best_phrase.text,
            normalized_bbox=best_phrase.bbox,
            confidence=None,
            source="phrase",
        )
        return best_phrase.page_index, representative

    @staticmethod
    def _phrase_position(phrase: _Phrase) -> tuple[int, float]:
        y_center = (phrase.bbox[1] + phrase.bbox[3]) / 2
        return phrase.page_index, y_center

    @staticmethod
    def _resolve_sections(
            sections: tuple[SectionDefinition, ...],
            phrases: tuple[_Phrase, ...],
    ) -> dict[str, tuple]:
        """
        Xác định vị trí bắt đầu của từng section, sau đó dựng khoảng
        [bắt đầu, bắt đầu section kế tiếp) theo thứ tự (page, y) tăng dần.
        Section không resolve được (ambiguous do tie_margin, hoặc không
        tìm thấy) sẽ VẮNG MẶT trong dict trả về - field thuộc section đó
        coi như "không tìm được" cho template này (đối xứng ADR-027).
        """
        starts: dict[str, tuple[int, float]] = {}
        for section in sections:
            if section.key_tokens is None:
                starts[section.section_id] = (0, 0.0)
                continue
            match = TemplateMatcher._find_key_match(
                section.key_tokens, section.fuzzy_threshold, phrases,
                tie_margin=TemplateMatching.SECTION_TIE_MARGIN,
            )
            if match is None:
                continue
            page_index, token = match
            y_center = (token.normalized_bbox[1] + token.normalized_bbox[3]) / 2
            starts[section.section_id] = (page_index, y_center)

        ordered = sorted(starts.items(), key=lambda kv: kv[1])
        ranges: dict[str, tuple] = {}
        for i, (section_id, start) in enumerate(ordered):
            end = ordered[i + 1][1] if i + 1 < len(ordered) else (float("inf"), float("inf"))
            ranges[section_id] = (start, end)
        return ranges

    @staticmethod
    def _filter_phrases_by_range(phrases: tuple[_Phrase, ...], position_range: tuple) -> tuple:
        start, end = position_range
        return tuple(
            p for p in phrases
            if start <= TemplateMatcher._phrase_position(p) < end
        )
    # ------------------------------------------------------------------
    # Score + Decision (đối xứng PDFDetector._decide_mode)
    # ------------------------------------------------------------------

    def _score_template(
        self,
        template: TemplateDefinition,
        phrases: tuple[_Phrase, ...],
    ) -> tuple[dict[str, tuple[int, WordToken]], float]:
        section_ranges = self._resolve_sections(template.sections, phrases)

        matched_keys: dict[str, tuple[int, WordToken]] = {}
        matched_weight = 0.0
        total_weight = sum(f.identification_weight for f in template.fields)

        for field_def in template.fields:
            position_range = section_ranges.get(field_def.section)
            if position_range is None:
                # Section của field này không resolve được cho template
                # này -> field coi như không tìm được (ADR-027 style).
                continue

            scoped_phrases = self._filter_phrases_by_range(phrases, position_range)
            match = self._find_key_match(
                field_def.key_tokens, field_def.fuzzy_threshold, scoped_phrases,
            )
            if match is not None:
                matched_keys[field_def.field_name] = match
                matched_weight += field_def.identification_weight

        score = matched_weight / total_weight if total_weight else 0.0
        return matched_keys, score

    # ------------------------------------------------------------------
    # Bước 2: Windowing
    # ------------------------------------------------------------------

    @staticmethod
    def _build_window(
        key_token: WordToken,
        relation: SpatialRelation,
    ) -> tuple[float, float, float, float]:
        """Dựng cửa sổ tìm kiếm hình chữ nhật từ bbox Key theo hướng đã khai báo."""
        x0, y0, x1, y1 = key_token.normalized_bbox
        d = relation.max_distance
        tol = relation.axis_tolerance

        if relation.direction is SpatialDirection.RIGHT:
            return x1, y0 - tol, x1 + d, y1 + tol
        if relation.direction is SpatialDirection.LEFT:
            return x0 - d, y0 - tol, x0, y1 + tol
        if relation.direction is SpatialDirection.BELOW:
            return x0 - tol, y1, x1 + tol, y1 + d
        # ABOVE
        return x0 - tol, y0 - d, x1 + tol, y0

    @staticmethod
    def _tokens_in_window(
        tokens: tuple[WordToken, ...],
        window: tuple[float, float, float, float],
    ) -> list[WordToken]:
        """Lọc token có tâm bbox nằm trong cửa sổ tìm kiếm."""
        wx0, wy0, wx1, wy1 = window
        result: list[WordToken] = []
        for token in tokens:
            tx0, ty0, tx1, ty1 = token.normalized_bbox
            center_x = (tx0 + tx1) / 2
            center_y = (ty0 + ty1) / 2
            if wx0 <= center_x <= wx1 and wy0 <= center_y <= wy1:
                result.append(token)
        return result

    # ------------------------------------------------------------------
    # Bước 3: Value Matching
    # ------------------------------------------------------------------

    def _get_compiled_pattern(self, pattern: str) -> re.Pattern:
        """Cache regex compile theo value_pattern string (tránh compile lại)."""
        compiled = self._pattern_cache.get(pattern)
        if compiled is None:
            compiled = re.compile(pattern)
            self._pattern_cache[pattern] = compiled
        return compiled

    def _select_best_value(
        self,
        candidates: list[WordToken],
        field_def: FieldDefinition,
        key_token: WordToken,
    ) -> str | None:
        """Lọc candidate khớp value_pattern, tie-break bằng khoảng cách gần Key nhất."""
        pattern = self._get_compiled_pattern(field_def.value_pattern)
        matches = [token for token in candidates if pattern.match(token.text)]
        if not matches:
            return None

        anchor = min(matches, key=lambda t: TemplateMatcher._distance(t, key_token))

        if field_def.value_type is not ValueType.TEXT:
            return anchor.text

        return self._merge_same_line(anchor, candidates)

    @staticmethod
    def _merge_same_line(anchor: WordToken, candidates: list[WordToken]) -> str:
        """
        Ghép anchor với các token liền kề cùng dòng (Value Matching nhiều
        từ - Known Limitation 3.3). Chỉ dùng cho field Text; tái dùng
        LINE_Y_TOLERANCE ("cùng dòng") và WORD_GAP_TOLERANCE ("liền kề"),
        đối xứng cơ chế đã có ở Key Matching (_cluster_lines/_cluster_phrases).
        Dừng mở rộng khi gặp token kết thúc bằng ':' - dấu hiệu đó là nhãn
        của field khác trên cùng dòng, không phải giá trị thật.
        """
        def y_center(t: WordToken) -> float:
            return (t.normalized_bbox[1] + t.normalized_bbox[3]) / 2

        anchor_y = y_center(anchor)
        same_line = [
            t for t in candidates
            if abs(y_center(t) - anchor_y) <= TemplateMatching.LINE_Y_TOLERANCE
        ]
        same_line.sort(key=lambda t: t.normalized_bbox[0])

        anchor_idx = next(
            i for i, t in enumerate(same_line)
            if t.normalized_bbox == anchor.normalized_bbox and t.text == anchor.text
        )

        selected = [anchor]

        i = anchor_idx
        while i + 1 < len(same_line):
            gap = same_line[i + 1].normalized_bbox[0] - same_line[i].normalized_bbox[2]
            if gap > TemplateMatching.WORD_GAP_TOLERANCE:
                break
            if same_line[i + 1].text.endswith(":"):
                break
            selected.append(same_line[i + 1])
            i += 1

        i = anchor_idx
        while i - 1 >= 0:
            gap = same_line[i].normalized_bbox[0] - same_line[i - 1].normalized_bbox[2]
            if gap > TemplateMatching.WORD_GAP_TOLERANCE:
                break
            if same_line[i - 1].text.endswith(":"):
                break
            selected.insert(0, same_line[i - 1])
            i -= 1

        selected.sort(key=lambda t: t.normalized_bbox[0])
        return " ".join(t.text for t in selected)

    @staticmethod
    def _distance(a: WordToken, b: WordToken) -> float:
        """Khoảng cách Euclidean giữa tâm bbox của 2 WordToken."""
        ax = (a.normalized_bbox[0] + a.normalized_bbox[2]) / 2
        ay = (a.normalized_bbox[1] + a.normalized_bbox[3]) / 2
        bx = (b.normalized_bbox[0] + b.normalized_bbox[2]) / 2
        by = (b.normalized_bbox[1] + b.normalized_bbox[3]) / 2
        return ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5
