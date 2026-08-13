"""Deterministic, explainable analysis of a :class:`PDFDocument`."""

from __future__ import annotations
from hashlib import sha256
from json import dumps
from collections.abc import Iterable
from core.domain.enums import ConfidenceLevel, RuleCategory
from core.domain.models import (
    AnalysisContext,
    AnalysisMode,
    Confidence,
    DocumentAnalysis,
    Evidence,
    KnowledgeRecord,
    PDFDocument,
)


class PDFDetector:
    """Build facts, evaluate heuristic evidence, then form one decision.

    The detector never reads a PDF itself, performs OCR, parses invoice data,
    or changes a KnowledgeRecord.  Its only input is the immutable model
    produced by ``PDFReader``.
    """

    _DIGITAL_TEXT_PAGE_RATIO = 0.80
    _DIGITAL_AVERAGE_TEXT_LENGTH = 20
    _HYBRID_CONTENT_PAGE_RATIO = 0.25
    _HIGH_EMPTY_PAGE_RATIO = 0.25
    _DECISION_TIE_MARGIN = 0.10
    _EVIDENCE_SCORE_SCALE = 1.40

    # --- Document Rule / Graphics Rule (bổ sung, TDS §7.2 RC-001/RC-004) ---
    # CHƯA qua thực nghiệm với dữ liệu thật (khác 5 rule Text/Image/
    # Consistency/Quality/Layout đã verify trên PDF thật) - weight cố ý
    # đặt thấp để không làm lệch các quyết định biên đã ổn định. Cần
    # tinh chỉnh khi có dữ liệu thật, cùng nhóm "placeholder" với
    # TemplateMatching.* (core/constants.py).
    _DOCUMENT_RULE_WEIGHT = 0.20
    _GRAPHICS_RULE_WEIGHT = 0.20
    _GRAPHICS_DRAWING_PAGE_RATIO = 0.50

    # Từ khóa gợi ý phần mềm scan trong metadata PDF (Producer/Creator).
    # Danh sách dựa trên tri thức chung, CHƯA verify với PDF Scanned
    # thật của dự án - cần rà lại khi có cơ hội đối chiếu.
    _SCAN_METADATA_KEYWORDS = (
        "scan", "scanner", "scanned",
        "camscanner", "adobe scan", "naps2", "vuescan", "scansnap",
    )

    # Thứ tự ưu tiên hiển thị cảnh báo theo category khi >1 rule cùng
    # sinh warning (ADR-055): category liên quan CHẤT LƯỢNG TÀI LIỆU
    # (QUALITY, LAYOUT) ưu tiên trước category mô tả độ KHÔNG CHẮC CHẮN
    # của riêng 1 rule (TEXT) - tránh hiển thị cảnh báo "bằng chứng yếu"
    # của 1 rule đơn lẻ cạnh 1 kết luận confidence cao được củng cố bởi
    # các rule khác. DOCUMENT/GRAPHICS chưa có rule nào implement (xem
    # PROJECT_CONTEXT.md §14) - thứ tự đặt tạm, cần rà lại khi 2 rule
    # này được thêm.
    _WARNING_CATEGORY_PRIORITY = (
        RuleCategory.QUALITY,
        RuleCategory.LAYOUT,
        RuleCategory.DOCUMENT,
        RuleCategory.GRAPHICS,
        RuleCategory.CONSISTENCY,
        RuleCategory.IMAGE,
        RuleCategory.TEXT,
    )

    def analyze(
        self,
        document: PDFDocument,
        knowledge: KnowledgeRecord | None = None,
    ) -> DocumentAnalysis:
        """Return an immutable, explainable processing recommendation."""
        context = self._build_context(document)
        evidence = self._evaluate_rules(context)
        mode, support_scores = self._decide_mode(evidence)
        fingerprint = self._fingerprint(context)
        confidence, knowledge_fingerprint, knowledge_warnings = (
            self._compose_confidence(
                mode=mode,
                evidence=evidence,
                context=context,
                fingerprint=fingerprint,
                knowledge=knowledge,
            )
        )

        reasons = tuple(item.reason for item in evidence if item.reason)
        warnings = self._evidence_warnings_ordered(evidence)
        warnings = self._unique_strings((*warnings, *knowledge_warnings))

        if mode is AnalysisMode.UNKNOWN:
            warnings = self._unique_strings(
                (*warnings, "The available evidence is insufficient to classify this PDF.")
            )

        return DocumentAnalysis(
            mode=mode,
            confidence=confidence,
            fingerprint=fingerprint,
            reasons=reasons,
            warnings=warnings,
            evidence=evidence,
            knowledge_fingerprint=knowledge_fingerprint,
            properties={
                "support_scores": {
                    mode.name: score for mode, score in support_scores.items()
                },
                "context_version": 1,
            },
        )

    @staticmethod
    def _build_context(document: PDFDocument) -> AnalysisContext:
        """Create the complete observation snapshot before any rule runs."""
        pages = document.pages
        page_count = len(pages)

        pages_with_text = sum(page.has_text for page in pages)
        pages_with_images = sum(page.has_images for page in pages)
        pages_with_drawings = sum(
            page.statistics.drawing_count > 0 for page in pages
        )
        empty_pages = sum(
            not page.has_text
            and not page.has_images
            and page.statistics.drawing_count == 0
            for page in pages
        )
        mixed_pages = sum(page.has_text and page.has_images for page in pages)

        total_text_length = sum(page.statistics.text_length for page in pages)
        total_image_count = sum(page.statistics.image_count for page in pages)
        total_font_count = sum(page.statistics.font_count for page in pages)
        total_text_block_count = sum(
            page.statistics.text_block_count for page in pages
        )
        total_drawing_count = sum(
            page.statistics.drawing_count for page in pages
        )
        rotated_pages = sum(page.statistics.rotation % 360 != 0 for page in pages)
        portrait_pages = sum(
            page.statistics.height >= page.statistics.width for page in pages
        )
        landscape_pages = page_count - portrait_pages

        def ratio(value: int) -> float:
            return value / page_count if page_count else 0.0

        return AnalysisContext(
            total_text_length=total_text_length,
            average_text_per_page=(total_text_length / page_count if page_count else 0.0),
            total_image_count=total_image_count,
            page_count=page_count,
            empty_pages=empty_pages,
            pages_with_text=pages_with_text,
            pages_with_images=pages_with_images,
            total_font_count=total_font_count,
            total_text_block_count=total_text_block_count,
            total_drawing_count=total_drawing_count,
            pages_with_drawings=pages_with_drawings,
            rotated_pages=rotated_pages,
            portrait_pages=portrait_pages,
            landscape_pages=landscape_pages,
            text_page_ratio=ratio(pages_with_text),
            image_page_ratio=ratio(pages_with_images),
            drawing_page_ratio=ratio(pages_with_drawings),
            empty_page_ratio=ratio(empty_pages),
            mixed_page_ratio=ratio(mixed_pages),
            metadata=document.metadata,
        )

    def _evaluate_rules(self, context: AnalysisContext) -> tuple[Evidence, ...]:
        """Evaluate independent, stateless rules against the same context."""
        return (
            self._evaluate_text_rule(context),
            self._evaluate_image_rule(context),
            self._evaluate_mixed_content_rule(context),
            self._evaluate_quality_rule(context),
            self._evaluate_layout_rule(context),
            self._evaluate_document_rule(context),
            self._evaluate_graphics_rule(context),
        )

    def _evaluate_text_rule(self, context: AnalysisContext) -> Evidence:
        metrics = {
            "text_page_ratio": context.text_page_ratio,
            "average_text_per_page": context.average_text_per_page,
        }
        if (
            context.text_page_ratio >= self._DIGITAL_TEXT_PAGE_RATIO
            and context.average_text_per_page >= self._DIGITAL_AVERAGE_TEXT_LENGTH
        ):
            return Evidence(
                rule_name="text_coverage",
                category=RuleCategory.TEXT,
                supports={AnalysisMode.DIGITAL: 0.70},
                reason="Text is present on most pages with usable average length.",
                metrics=metrics,
            )

        if context.pages_with_text > 0:
            return Evidence(
                rule_name="text_coverage",
                category=RuleCategory.TEXT,
                supports={AnalysisMode.DIGITAL: 0.25},
                reason="Some extractable text is present, but coverage is limited.",
                warnings=("Text coverage alone is not strong enough for a high-confidence decision.",),
                metrics=metrics,
            )

        if context.pages_with_images or context.pages_with_drawings:
            return Evidence(
                rule_name="text_coverage",
                category=RuleCategory.TEXT,
                supports={AnalysisMode.SCANNED: 0.15},
                reason="No extractable text was observed.",
                warnings=("Absence of text alone does not prove that OCR is required.",),
                metrics=metrics,
            )

        return Evidence(
            rule_name="text_coverage",
            category=RuleCategory.TEXT,
            reason="No extractable text was observed.",
            warnings=("No observable content is available to infer an OCR strategy.",),
            metrics=metrics,
        )

    def _evaluate_image_rule(self, context: AnalysisContext) -> Evidence:
        metrics = {
            "image_page_ratio": context.image_page_ratio,
            "total_image_count": context.total_image_count,
        }
        if context.image_page_ratio >= self._DIGITAL_TEXT_PAGE_RATIO:
            if context.pages_with_text == 0:
                return Evidence(
                    rule_name="image_coverage",
                    category=RuleCategory.IMAGE,
                    supports={AnalysisMode.SCANNED: 0.80},
                    reason="Images occur on most pages while no text layer is available.",
                    metrics=metrics,
                )

            return Evidence(
                rule_name="image_coverage",
                category=RuleCategory.IMAGE,
                supports={AnalysisMode.HYBRID: 0.35},
                reason="Images occur on most pages together with an extractable text layer.",
                metrics=metrics,
            )

        if context.pages_with_images > 0:
            return Evidence(
                rule_name="image_coverage",
                category=RuleCategory.IMAGE,
                reason="Images are present but not distributed across most pages.",
                metrics=metrics,
            )

        return Evidence(
            rule_name="image_coverage",
            category=RuleCategory.IMAGE,
            reason="No embedded images were observed.",
            metrics=metrics,
        )

    def _evaluate_mixed_content_rule(self, context: AnalysisContext) -> Evidence:
        metrics = {
            "mixed_page_ratio": context.mixed_page_ratio,
            "text_page_ratio": context.text_page_ratio,
            "image_page_ratio": context.image_page_ratio,
        }
        if (
            context.mixed_page_ratio >= self._HYBRID_CONTENT_PAGE_RATIO
            or (
                context.text_page_ratio >= self._HYBRID_CONTENT_PAGE_RATIO
                and context.image_page_ratio >= self._HYBRID_CONTENT_PAGE_RATIO
            )
        ):
            return Evidence(
                rule_name="mixed_content",
                category=RuleCategory.CONSISTENCY,
                supports={AnalysisMode.HYBRID: 0.65},
                reason="Text and image evidence are both materially present in the document.",
                metrics=metrics,
            )

        return Evidence(
            rule_name="mixed_content",
            category=RuleCategory.CONSISTENCY,
            reason="No material text-image mixture was observed.",
            metrics=metrics,
        )

    def _evaluate_quality_rule(self, context: AnalysisContext) -> Evidence:
        warnings: list[str] = []
        if context.page_count == 0:
            warnings.append("The document contains no pages.")
        elif context.empty_page_ratio >= self._HIGH_EMPTY_PAGE_RATIO:
            warnings.append("A substantial share of pages has no observable content.")

        return Evidence(
            rule_name="content_coverage",
            category=RuleCategory.QUALITY,
            reason="Document content coverage was evaluated before confidence composition.",
            warnings=tuple(warnings),
            metrics={
                "page_count": context.page_count,
                "empty_page_ratio": context.empty_page_ratio,
                "drawing_page_ratio": context.drawing_page_ratio,
            },
        )

    @staticmethod
    def _evaluate_layout_rule(context: AnalysisContext) -> Evidence:
        warnings: tuple[str, ...] = ()
        if context.rotated_pages:
            warnings = ("Rotated pages may require layout-aware extraction downstream.",)

        return Evidence(
            rule_name="page_layout",
            category=RuleCategory.LAYOUT,
            reason="Page orientation and rotation were recorded without selecting a strategy.",
            warnings=warnings,
            metrics={
                "rotated_pages": context.rotated_pages,
                "portrait_pages": context.portrait_pages,
                "landscape_pages": context.landscape_pages,
            },
        )

    def _evaluate_document_rule(self, context: AnalysisContext) -> Evidence:
        """RC-001 (TDS §7.2): đánh giá đặc điểm tổng quát cấp tài liệu.

        Tín hiệu duy nhất: metadata Producer/Creator chứa từ khóa gợi ý
        phần mềm scan. Chỉ tạo supports khi CÓ tín hiệu dương tính rõ
        ràng - vắng mặt từ khóa KHÔNG được coi là bằng chứng cho DIGITAL
        (metadata có thể mất/ghi đè qua nhiều lần re-save, DP-003).
        """
        producer = str(context.metadata.get("producer", ""))
        creator = str(context.metadata.get("creator", ""))
        combined = f"{producer} {creator}".lower()
        metrics = {"producer": producer, "creator": creator}

        matched = [kw for kw in self._SCAN_METADATA_KEYWORDS if kw in combined]
        if matched:
            return Evidence(
                rule_name="document_metadata",
                category=RuleCategory.DOCUMENT,
                supports={AnalysisMode.SCANNED: self._DOCUMENT_RULE_WEIGHT},
                reason="Document metadata (Producer/Creator) references scanning software.",
                warnings=(
                    "Metadata-based signal is weak and easily spoofed or "
                    "absent; not yet validated on real data.",
                ),
                metrics=metrics,
            )

        return Evidence(
            rule_name="document_metadata",
            category=RuleCategory.DOCUMENT,
            reason="Document metadata does not reference any known scanning software.",
            metrics=metrics,
        )

    def _evaluate_graphics_rule(self, context: AnalysisContext) -> Evidence:
        """RC-004 (TDS §7.2): đánh giá đối tượng đồ họa/vector.

        Tín hiệu duy nhất: mật độ vector drawing operations
        (page.get_drawings(), không tính pixel ảnh) cao trên phần lớn
        trang - PDF Scanned thuần túy (ảnh raster phủ trang) về bản
        chất không có drawing operations. Chỉ tạo supports khi CÓ tín
        hiệu dương tính; thiếu vector graphics không phải bằng chứng
        cho SCANNED (nhiều hóa đơn Digital cũng không dùng khung/bảng
        vector, DP-003).
        """
        metrics = {
            "drawing_page_ratio": context.drawing_page_ratio,
            "total_drawing_count": context.total_drawing_count,
        }
        if context.drawing_page_ratio >= self._GRAPHICS_DRAWING_PAGE_RATIO:
            return Evidence(
                rule_name="vector_graphics_coverage",
                category=RuleCategory.GRAPHICS,
                supports={AnalysisMode.DIGITAL: self._GRAPHICS_RULE_WEIGHT},
                reason="Vector drawing operations occur on most pages, consistent with software-generated content.",
                warnings=(
                    "Vector graphics can also appear on annotated scans; "
                    "not yet validated on real data.",
                ),
                metrics=metrics,
            )

        return Evidence(
            rule_name="vector_graphics_coverage",
            category=RuleCategory.GRAPHICS,
            reason="Vector drawing operations are not present on most pages.",
            metrics=metrics,
        )

    def _decide_mode(
        self,
        evidence: tuple[Evidence, ...],
    ) -> tuple[AnalysisMode, dict[AnalysisMode, float]]:
        """Resolve all evidence together; no individual rule makes a decision."""
        scores = {
            AnalysisMode.DIGITAL: 0.0,
            AnalysisMode.SCANNED: 0.0,
            AnalysisMode.HYBRID: 0.0,
        }
        for item in evidence:
            for mode, score in item.supports.items():
                if mode in scores:
                    scores[mode] += score

        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        leading_mode, leading_score = ranked[0]
        runner_up_score = ranked[1][1]
        if (
            leading_score == 0
            or leading_score - runner_up_score < self._DECISION_TIE_MARGIN
        ):
            return AnalysisMode.UNKNOWN, scores

        return leading_mode, scores

    def _compose_confidence(
        self,
        *,
        mode: AnalysisMode,
        evidence: tuple[Evidence, ...],
        context: AnalysisContext,
        fingerprint: str,
        knowledge: KnowledgeRecord | None,
    ) -> tuple[Confidence, str | None, tuple[str, ...]]:
        """Compose independent confidence sources without changing evidence."""
        support_scores = self._support_scores(evidence)
        selected_score = support_scores.get(mode, 0.0)
        total_score = sum(support_scores.values())

        evidence_strength = self._clamp(selected_score / self._EVIDENCE_SCORE_SCALE)
        consistency = self._clamp(selected_score / total_score) if total_score else 0.0
        observed_page_ratio = max(
            context.text_page_ratio,
            context.image_page_ratio,
            context.drawing_page_ratio,
        )
        coverage = self._clamp((1.0 - context.empty_page_ratio) * observed_page_ratio)

        sources = {
            "evidence": evidence_strength,
            "consistency": consistency,
            "coverage": coverage,
        }
        explanation = [
            f"Evidence strength is {evidence_strength:.2f} from accumulated support.",
            f"Evidence consistency is {consistency:.2f} across candidate modes.",
            f"Observation coverage is {coverage:.2f} across document pages.",
        ]
        warnings: tuple[str, ...] = ()
        knowledge_fingerprint: str | None = None

        final_score = evidence_strength * consistency * coverage
        if knowledge is not None:
            if knowledge.fingerprint != fingerprint:
                warnings = ("The supplied knowledge record does not match this document fingerprint.",)
            else:
                knowledge_fingerprint = knowledge.fingerprint
                reliability = self._clamp(knowledge.confidence * knowledge.success_rate)
                sources["knowledge"] = reliability
                if knowledge.preferred_mode is mode:
                    final_score *= 1.0 + 0.10 * reliability
                    explanation.append(
                        "Matching knowledge has reliability "
                        f"{reliability:.2f}; it increases confidence but not the decision."
                    )
                else:
                    final_score *= 1.0 - 0.10 * reliability
                    explanation.append(
                        "Conflicting knowledge has reliability "
                        f"{reliability:.2f}; it reduces confidence but not the decision."
                    )

        final_score = self._clamp(final_score)
        return (
            Confidence(
                score=final_score,
                level=self._confidence_level(final_score),
                sources=sources,
                explanation=tuple(explanation),
            ),
            knowledge_fingerprint,
            warnings,
        )

    @staticmethod
    def _support_scores(evidence: tuple[Evidence, ...]) -> dict[AnalysisMode, float]:
        scores = {
            AnalysisMode.DIGITAL: 0.0,
            AnalysisMode.SCANNED: 0.0,
            AnalysisMode.HYBRID: 0.0,
        }
        for item in evidence:
            for mode, score in item.supports.items():
                if mode in scores:
                    scores[mode] += score
        return scores

    @staticmethod
    def _fingerprint(context: AnalysisContext) -> str:
        """Create a deterministic structural fingerprint from observed metrics."""
        values = {
            "average_text_per_page": round(context.average_text_per_page, 6),
            "drawing_page_ratio": round(context.drawing_page_ratio, 6),
            "empty_page_ratio": round(context.empty_page_ratio, 6),
            "image_page_ratio": round(context.image_page_ratio, 6),
            "page_count": context.page_count,
            "text_page_ratio": round(context.text_page_ratio, 6),
            "total_drawing_count": context.total_drawing_count,
            "total_image_count": context.total_image_count,
            "total_text_length": context.total_text_length,
        }
        encoded = dumps(values, sort_keys=True, separators=(",", ":"))
        return sha256(encoded.encode("utf-8")).hexdigest()

    @staticmethod
    def _confidence_level(score: float) -> ConfidenceLevel:
        if score >= 0.80:
            return ConfidenceLevel.VERY_HIGH
        if score >= 0.60:
            return ConfidenceLevel.HIGH
        if score >= 0.40:
            return ConfidenceLevel.MEDIUM
        if score >= 0.20:
            return ConfidenceLevel.LOW
        return ConfidenceLevel.VERY_LOW

    @staticmethod
    def _clamp(value: float) -> float:
        return max(0.0, min(1.0, value))

    def _evidence_warnings_ordered(
            self,
            evidence: tuple[Evidence, ...],
    ) -> tuple[str, ...]:
        """
        Gom warnings từ mọi Evidence, sắp theo _WARNING_CATEGORY_PRIORITY
        thay vì theo thứ tự rule chạy trong _evaluate_rules() (ADR-055).
        Category không nằm trong danh sách ưu tiên rơi xuống cuối.
        sorted() ổn định (stable) - Evidence cùng category giữ nguyên
        thứ tự tương đối ban đầu (không đổi hành vi khi >1 warning cùng
        category).
        """

        def priority(item: Evidence) -> int:
            try:
                return self._WARNING_CATEGORY_PRIORITY.index(item.category)
            except ValueError:
                return len(self._WARNING_CATEGORY_PRIORITY)

        ordered_evidence = sorted(evidence, key=priority)
        return self._unique_strings(
            warning
            for item in ordered_evidence
            for warning in item.warnings
        )

    @staticmethod
    def _unique_strings(values: Iterable[str]) -> tuple[str, ...]:
        return tuple(dict.fromkeys(values))
