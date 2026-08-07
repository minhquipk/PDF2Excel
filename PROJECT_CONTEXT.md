# PROJECT_CONTEXT.md

# PDF Invoice Extractor

> Project Context & Architecture Handover
>
> This document is the single source of truth for the project.
> Any architectural change must be discussed before implementation.

---

# 1. Project Goal

Build a desktop application using Python to automatically extract information
from a large number of PDF invoices and write the extracted data into an
existing Excel template.

Main requirements:

- Scan an entire folder recursively.
- Support thousands of PDF files.
- Detect Digital PDF / OCR PDF automatically.
- Extract invoice information.
- Store intermediate results in memory.
- Write Excel only once after all files have been processed.
- Generate an error report for manual review.

Target users:

Office users with no programming knowledge.

---

# 2. Overall Architecture

```
MainWindow
    │
    ▼
Worker (QThread)
    │
    ▼
_process_pdf()
    │
    ▼
PDFReader
    │
    ▼
PDFDetector
    │
    ▼
Extractor ──(quyết định gọi khi cần OCR)──> OCREngine
    │
    ▼
Parser (pending)
    │
    ▼
PDFResult
    │
    ▼
Memory (list[PDFResult])
    │
    ▼
ExcelWriter
    │
    ▼
ReportWriter ──▶ logs/app.log (list[PDFResult]) + reports/Report.txt (ExcelWriteResult)
```

UI is completely separated from business logic.

Worker never accesses UI directly.

Communication is only through Qt Signals.

---

# 3. Current Project Structure

```
PDF2Excel/

    config.py
    main.py
    requirements.txt

    ui/
        base_widget.py
        widgets.py
        main_window.py
        theme.py
        worker.py

    models/
        processing_table_model.py

    utils/
        logger.py

    core/
        constants.py
        enums.py
        excel_mapper.py
        excel_writer.py
        extractor.py
        models.py
        ocr_engine.py
        parser.py
        pdf_detector.py
        pdf_reader.py
        processor.py
        report_writer.py
        template_loader.py
        template_matcher.py
        value_converter.py

    resources/
        excel_mapping.json
        templates/
            sample_invoice_v1.json
```

---

# 4. Modules Completed

Completed:

- constants.py
- enums.py
- models.py
- pdf_reader.py — reads PDF via PyMuPDF, builds `PDFDocument`;
  also reads raw word tuples (`words`) and renders a raw grayscale
  `PageImage` (300 DPI) for every page.
- pdf_detector.py — full reasoning engine (Build Context, Heuristic
  Evaluation, Knowledge Lookup, Confidence Composition, Final
  Decision) per `PDF_Detector_Technical_Design.docx`.
- extractor.py — dispatches extraction strategy per
  `DocumentAnalysis.mode` (Digital / OCR / per-page Hybrid);
  normalizes word geometry (incl. rotation reconciliation for the
  Digital path) into `WordToken`s ready for Parser.
- ocr_engine.py — Mock implementation only (ADR-013); contract is
  final, real OCR backend not yet wired in.
- base_widget.py
- widgets.py
- main_window.py
- worker.py — pipeline integration completed end-to-end: Reader →
  Detector → Extractor (conditional on a valid mode) → Parser →
  ExcelWriter → ReportWriter, all wired in `Worker._write_excel()`
  (ADR-037/038/040).
- processing_table_model.py
- value_converter.py — stateless TEXT/DECIMAL/DATE conversion, không
  raise (trả None khi thất bại). Từ Session 2026-08-07: `_to_decimal()`
  strip ký tự `%` cuối chuỗi trước khi parse (ADR-043).
- template_loader.py — đọc/validate JSON Template Definition, fail-soft
  per file. Từ Session 2026-08-07: parse thêm `sections` và field bắt
  buộc `section` trên mỗi field.
- template_matcher.py — Key Matching (Line/Phrase Clustering + fuzzy,
  chuẩn hoá dấu tiếng Việt) → Score/Decision → Windowing → Value
  Matching. Từ Session 2026-08-07: Key Matching nay giới hạn phạm vi
  theo Section (khối tài liệu field thuộc về - `SectionDefinition`,
  giải quyết va chạm key_tokens giữa các khối, VD bên bán/bên mua, xem
  ADR-045); Value Matching field Text nay ghép nhiều `WordToken` liền
  kề cùng dòng thành 1 giá trị thay vì chỉ lấy 1 token (ADR-044).
- parser.py — orchestrator mỏng, trả `InvoiceInfo | None`.
- excel_mapper.py — `Mapper.load()` đọc/validate `resources/excel_mapping.json`
  thành `ExcelMapping`; lỗi là fatal (khác `template_loader.py`), raise
  `MappingError` (ADR-038).
- excel_writer.py — `ExcelWriter.write()` ghi `list[InvoiceInfo]` vào
  Excel Table có sẵn (openpyxl); trả `ExcelWriteResult` (dữ liệu thuần,
  không tự log/report — ADR-006, ADR-037); cột mapping không khớp
  workbook thực tế → soft-fail vào `ExcelWriteResult.errors` (ADR-039).
- report_writer.py — `ReportWriter.write()` có 2 kênh output tách biệt:
  `list[PDFResult]` → `logs/app.log` (qua `utils/logger.py`, dev/admin,
  tích lũy qua các lần chạy); `ExcelWriteResult` → `reports/Report.txt`
  (end-user, ghi đè mỗi lần chạy) (ADR-040).
- utils/logger.py — logger dùng chung, console handler + `FileHandler`
  (`logs/app.log`, UTF-8, đúng ADR-014) — bổ sung khi triển khai
  report_writer.py.
- requirements.txt — pin version 4 dependency đã xác nhận qua kiểm thử
  thực tế: `PySide6==6.11.1`, `PyMuPDF==1.28.0`, `rapidfuzz==3.14.5`,
  `openpyxl==3.1.5`.
- resources/EXCEL_MAPPING_GUIDE.md — hướng dẫn viết `excel_mapping.json`
  cho người điều hành không biết lập trình (Session 2026-08-07).

Current UI features:

- Input folder
- Output Excel
- Start
- Stop
- Report
- Exit
- Progress bar
- Processing table

Still pending (not yet implemented):

- Real OCR backend (ocr_engine.py currently Mock only) — deliberately
  deferred until after end-to-end verification with real sample PDFs
  (see Section 15, Next Tasks). Mock is sufficient for Digital-mode
  PDFs, which do not invoke OCREngine at all.
- Tài liệu hướng dẫn viết Template JSON (Template Authoring Guide)
- `resources/excel_mapping.json` vẫn còn là mapping mẫu (`tblInvoices`),
  chưa khớp workbook Excel thật của người dùng — bước 2 trong kế hoạch
  5 bước ở Section 15 vẫn chưa thực hiện.
- Chưa có lượt chạy UI thật (Input Folder → Start → Report) trên ứng
  dụng thật với dữ liệu PDF thật — `sample_invoice_v1.json` (v3) mới chỉ
  verify bằng script kiểm thử trực tiếp gọi `PDFReader`/`Extractor`/
  `TemplateMatcher` trong sandbox, KHÔNG phải qua `Worker`/`MainWindow`
  thật.

Resolved this session (previously "Still pending" or "Known Issues" —
now implemented and verified, see Section 14/15 for verification
caveats):

- excel_writer.py — implemented (`core/excel_writer.py`), see ADR-037/
  038/039.
- Report export — implemented (`core/report_writer.py`); UI Report
  button now opens a real generated `reports/Report.txt` (ADR-040/041),
  no longer a "pending" placeholder message.
- Dependency pinning — `requirements.txt` added at project root
  (previously an open item since Session 2026-08-01/02).

Note: `core/processor.py` currently contains only placeholder method
calls (`start/stop/pause/resume`) with no implementation. The actual
orchestrator responsibility (per ADR-004) is currently fulfilled by
`Worker.process()`, not by `processor.py`. This needs clarification
(see Section 14).

Known limitation (deferred to v2.0): pages with both a text layer and
materially relevant image content are extracted from a single source
only (text-layer wins). See CHANGELOG.md / SESSION_SUMMARIES.md,
Session 2026-07-31.

---

# 5. Data Flow

```
Path
  ↓ (PDFReader.read)
PDFDocument
  ↓ (PDFDetector.analyze)
DocumentAnalysis  ──┐
  ↓                 │ (cả 2 cùng làm input cho Extractor)
PDFDocument ─────────┘
  ↓ (Extractor.extract)
ExtractionResult
  ↓ (Parser — pending)
InvoiceInfo
  ↓
PDFResult
  ↓ (accumulate)
list[PDFResult]
  ↓ (ExcelWriter — pending)
.xlsx
```

The application NEVER writes Excel while processing each PDF.

Excel is written only once after all PDFs have been processed.

---

# 6. Important Design Decisions

## Memory First

PDFs are processed one by one.

Each PDF is immediately released from memory after processing.

Only PDFResult objects remain in memory.

This greatly reduces memory usage.

---

## Single Excel Write

Excel writing is expensive.

Never write after each PDF.

Write only once at the end.

---

## process() Responsibility

process() is an orchestrator.

It must NEVER contain PDF parsing logic.

Correct structure:

```
for pdf in pdf_files:

    result = _process_pdf(pdf)

    results.append(result)

_write_excel()
```
This orchestrator responsibility is currently implemented as
`Worker.process()` in `ui/worker.py`.

---

## _process_pdf()

All business logic belongs here.

Current implementation (`Worker._process_pdf()`):

PDF

↓

PDF Reader

↓

PDF Detector

↓

PDFResult (pdf_type / status / note derived from DocumentAnalysis)

The detector is a deterministic reasoning engine. It receives only an
immutable PDFDocument, builds an immutable AnalysisContext, preserves all
heuristic Evidence, optionally consults a read-only KnowledgeRecord, and
returns an immutable DocumentAnalysis with explainable Confidence.

This integration is now real (not Mock) — `Worker._process_pdf()` calls
`PDFReader.read()` and `PDFDetector.analyze()` directly. Extraction,
regex parsing, and Excel writing are still pending and not yet wired
into this method.

---

## Reader Responsibility

PDFReader is responsible only for reading PDF content and converting
PyMuPDF objects into immutable domain models.

PDFReader MUST NOT perform:

- OCR
- Regex parsing
- Invoice extraction
- PDF classification
- Data analysis
- Business validation

PDFReader is the boundary between PyMuPDF and the project domain.

## PDFDocument Strategy

PDFDocument keeps the complete document text.

Reason:

Parser benefits from preserving page relationships and document context.

Memory usage remains acceptable because only one PDF is processed at a time.

## Analyzer Strategy

Analyzer is responsible for collecting document statistics and building
a reusable knowledge cache.

Analyzer does not perform OCR or machine learning.

Knowledge grows incrementally from previous processing sessions.

Note: in the current source, this "Analyzer" role is fulfilled by
`PDFDetector` (Rule System + Confidence Model) as designed in
`PDF_Detector_Technical_Design.docx`. `KnowledgeRecord` accumulation /
lifecycle management (Knowledge System, TDS Chapter 9) is defined at
the design level but not yet implemented in source.

## Source of Truth

Implementation must always be based on the current project source code.

Chat history must never be treated as the implementation reference.

# 7. UI Design

Layout:

```
Input Folder

Output Excel

---------------------------

        Start   Stop

---------------------------

Progress

---------------------------

Processing Table

---------------------------

             Report Exit
```

Processing Table columns:

| Column | Description         |
|--------|---------------------|
| PDF    | File name           |
| TYPE   | Digital / OCR       |
| STATUS | OK / ERROR / OCR... |
| NOTE   | Detailed message    |

---

# 8. Worker Design

Worker runs in its own QThread.

MainWindow never performs heavy work.

Signals:

- started
- progress
- file_processed
- finished
- cancelled
- error

---

# 9. Progress Strategy

Progress is based on

processed PDFs / total PDFs

Elapsed time and ETA are updated separately.

---

# 10. Coding Conventions

- Python 3.12+
- Type hints everywhere.
- Dataclass for data models.
- Enum for fixed values.
- One responsibility per class.
- No business logic inside UI.
- Avoid global variables.
- Prefer composition over inheritance.

---

# 11. Libraries

GUI

- PySide6

PDF

- PyMuPDF (fitz) — in use by pdf_reader.py (text, words, and page
  image rendering)

OCR

- Backend not yet chosen; `ocr_engine.py` currently a Mock (ADR-013).
  `pytesseract` remains the leading candidate (planned).

Image

- No separate library needed for rendering — PyMuPDF's
  `Page.get_pixmap()` covers this (see ADR-026). `pdf2image` is not
  currently required.

Excel

- openpyxl — dùng bởi `excel_writer.py` để ghi vào Excel Table có sẵn
  (đọc/mở rộng `table.ref`, ghi cell theo `ExcelMapping`).

Regex

- re

Data

- dataclasses

Fuzzy Matching

- rapidfuzz — dùng bởi template_matcher.py cho Key Matching.

Dependency file: `requirements.txt` (project root) — pin version 4
package trên (`PySide6`, `PyMuPDF`, `rapidfuzz`, `openpyxl`), version
đã được xác nhận qua kiểm thử thực tế trong phiên triển khai
excel_writer/report_writer. Trước đó dự án không có dependency file
nào (Known Issue từ Session 2026-08-01/02) — đã giải quyết.

---

# 12. Development Workflow

Always develop incrementally.

Each step must compile.

Each step must run.

Never implement multiple modules simultaneously.

Typical workflow:

1.

Implement

↓

Compile

↓

Run

↓

Verify

↓

Commit

2.

Continue.

---

# 13. Mock Mode

Mock mode was used before implementing real PDF processing.

Worker generated fake PDFResult objects during early UI/Worker/Thread
validation.

Purpose (historical):

- Test UI
- Test Thread
- Test Signals
- Test TableModel

Current status: Mock processing has been replaced by the real
pipeline end-to-end: PDFReader → PDFDetector → Extractor → Parser →
ExcelWriter → ReportWriter, all wired in `ui/worker.py`. `OCREngine`
remains a Mock (ADR-013) — this only affects Scanned/Hybrid-mode
pages; Digital-mode PDFs (the majority case) do not invoke it at all.
The pipeline has been verified with unit-level and mocked-input tests
(see SESSION_SUMMARIES.md, Session 2026-08-03) but **not yet** with a
real user-driven run against real sample PDF data through the actual
UI — that is the planned next step (see Section 15).

---

# 14. Known Issues

Current:

- Elapsed Time not implemented.
- ETA not implemented.
- Real OCR backend not implemented (`ocr_engine.py` is Mock only) —
  intentionally deferred, see Section 15.
- `core/processor.py` is a placeholder (4 undefined method calls, not
  inside any class/function — calling it directly would raise
  `NameError`, not just "unimplemented"); its relationship to
  `Worker.process()` (which currently acts as the real orchestrator)
  needs clarification.
- `main.py` is currently empty. The actual application entry point
  (`if __name__ == "__main__":` block constructing `QApplication` and
  `MainWindow`) lives in `ui/main_window.py` instead. This discrepancy
  was noticed during source review but not yet discussed/resolved —
  needs clarification on whether `main.py` should become the real
  entry point or be removed.
- `core/excel_writer.py::WorkbookSaveError` has not been verified
  against a real OS-level permission failure (e.g. target `.xlsx` open
  in Excel, or read-only file). Testing was attempted but could not be
  reproduced in the development/test container, which runs with root
  privileges and bypasses normal file permission checks. The exception
  handling path (`_save_workbook()` catching `OSError`) is logically
  correct and covered by other automated tests, but this specific
  failure mode is unverified end-to-end. Needs manual verification on
  a real user machine before being considered fully validated (see
  Section 15).
- `core/constants.py::UIText.REPORT_PENDING` is now dead code — no
  longer referenced anywhere in `ui/main_window.py` after `_report()`
  was reimplemented to open a real `report.txt` (ADR-041). Not yet
  removed; flagged for cleanup.
- PDFDetector Rule System currently implements 5 of 7 Rule
  Categories defined in the TDS (§7.2): Text, Image, Consistency,
  Quality, Layout are implemented; Document and Graphics rule
  categories are not yet implemented.
- Knowledge System (TDS Chapter 9: lifecycle, governance, sources)
  is defined at the design level only; no persistence/lifecycle
  management exists in source yet.
- Extractor routes mixed-content pages (text + image) to a single
  source only; dual-source extraction deferred to v2.0 (see
  Section 4).
- No automated test suite exists; `Extractor._rotate_bbox()` in
  particular is a good candidate for dedicated unit tests before
  further logic is built on top of it.
- Value Matching (template_matcher.py) chỉ lấy 1 WordToken đơn lẻ; field
  nhiều từ (company_name, address) bị cắt cụt. Cần thiết kế ghép cụm
  Value trước khi Value Matching — deferred, chưa có giải pháp.
- Chưa có tài liệu "Template Authoring Guide" (quy tắc viết key_tokens/
  value_pattern an toàn) — cần thiết trước khi ai đó ngoài phiên thảo
  luận này viết Template JSON thật.
- TemplateMatching.* (core/constants.py) là giá trị ước lượng ban đầu,
  cần tinh chỉnh khi có PDF hóa đơn thật.
- resources/templates/sample_invoice_v1.json cố ý giữ 2 lỗi đã biết
  (key_tokens ngắn, value_pattern lỏng) — chưa sửa, chờ dữ liệu thật.
- - Value Matching nhiều từ (ADR-044, Session 2026-08-07) dùng cơ chế
  gap-based, dừng mở rộng khi gặp token kết thúc bằng dấu `:`. Rủi ro
  còn lại: nếu 1 dòng có 2 field liền kề mà nhãn field thứ 2 KHÔNG kết
  thúc bằng `:`, giá trị vẫn có thể bị ghép tràn sang field kế bên. Mới
  verify trên 1 PDF test duy nhất — chưa đủ dữ liệu để đánh giá tần
  suất rủi ro này trên layout đa dạng hơn.
- Section (ADR-045, Session 2026-08-07) giảm mạnh nhưng KHÔNG loại bỏ
  hoàn toàn rủi ro va chạm: bản thân section header vẫn dùng chung cơ
  chế fuzzy match, về lý thuyết vẫn có thể va chạm nếu 2 section dùng
  `key_tokens` gần giống nhau trên 1 tài liệu khác.
- `TemplateMatching.SECTION_TIE_MARGIN` (giá trị 10, thang 0-100 của
  `rapidfuzz.fuzz.ratio()`) là placeholder ban đầu, cùng loại với các
  hằng số khác trong `TemplateMatching` — cần tinh chỉnh khi có nhiều
  mẫu hóa đơn thật hơn.
- `FieldDefinition.section` nay là field BẮT BUỘC (không có default).
  Mọi template JSON khác ngoài `sample_invoice_v1.json`, nếu phát sinh
  sau này mà thiếu `section` trên 1 field, sẽ bị `TemplateLoader` skip
  toàn bộ file đó (fail-soft per file, ADR-031) — cần lưu ý khi viết
  Template Authoring Guide (mục dưới).
- Section header 5+ từ có thể không bao giờ đạt fuzzy ratio tuyệt đối
  do `TemplateMatching.MAX_KEY_WORDS = 4` giới hạn độ dài phrase sinh
  ra khi Key Matching (VD "THÔNG TIN NGƯỜI MUA HÀNG:" — 5 từ — phải rút
  gọn `key_tokens` xuống 4 từ để qua được `SECTION_TIE_MARGIN`, xem
  ADR-045). Ràng buộc này áp dụng cho CẢ field lẫn section.

Resolved (previously listed here, now implemented — see Section 4):

- PDF Reader — implemented (`core/pdf_reader.py`).
- PDF Detector reasoning engine — implemented (`core/pdf_detector.py`).
- Extractor — implemented (`core/extractor.py`).
- Regex Parser — implemented (`core/parser.py`, `core/template_matcher.py`).
- Excel Writer — implemented (`core/excel_writer.py`), see ADR-037/038/039.
- Report export — implemented (`core/report_writer.py`), see ADR-040/041.
- Import path issue — re-verified against current source (this
  session): `core/models.py` now imports via `from core.enums import
  ...` and `ui/widgets.py` via `from ui.base_widget import
  BaseWidget`, both with correct package prefixes. The issue described
  in earlier sessions (Session 2026-07-29) no longer reproduces in the
  current source; closing as resolved. (Note: it is unclear from
  available history whether this was fixed deliberately in an
  undocumented change or was miscategorized originally — flagging for
  awareness, not re-opening.)
- Dependency file missing — resolved via `requirements.txt` added at
  project root, pinning `PySide6`, `PyMuPDF`, `rapidfuzz`, `openpyxl`.

---

# 15. Next Tasks

Decision made at the end of Session 2026-08-03: two candidate
directions were discussed for the next session —

1.  Wire up the UI end-to-end with real config files and run against
    real sample PDF data.
2.  Implement a real OCR backend first, then test.

**Direction 1 was chosen**, per ADR-013 (Mock First: validate UI/
Worker/Signals before replacing a Mock) and because Mock `OCREngine`
is already sufficient for Digital-mode PDFs — implementing OCR now
would conflate two untested things at once (new OCR code + first-ever
real end-to-end run), which conflicts with Rule 2/3 of
DEVELOPMENT_WORKFLOW.md (one feature at a time, small reversible
changes).

Priority order for the next session:

1.

Place real sample PDF files (Digital-type first, to stay independent
of the still-Mock OCREngine) in a local folder outside the repo.

↓

2.

Adjust `resources/excel_mapping.json` to match the real target output
Excel workbook's actual Table name and column headers.

↓

3.

Run the real application end-to-end (`python ui/main_window.py` —
see Section 14, `main.py` entry-point discrepancy still open) against
the sample folder: Input Folder → Output Excel → Start → wait →
Report.

↓

4.

Inspect results: does the output `.xlsx` contain correct data? Does
`reports/Report.txt` content make sense? Does the sample template
(`sample_invoice_v1.json`) actually match fields in the real PDFs?

↓

5.

Fix `sample_invoice_v1.json`'s two known issues~~ — Done, Session
2026-08-07 (phạm vi thực tế rộng hơn nhiều: xem SESSION_SUMMARIES.md,
Session 2026-08-07, và ADR-043/044/045). `sample_invoice_v1.json` hiện
ở version 3, đã verify 12/12 field đúng trên `HD2026-0003_digital.pdf`
BẰNG SCRIPT KIỂM THỬ TRỰC TIẾP trong sandbox — bước "chạy app thật qua
UI" (mục 3 ở trên) vẫn CHƯA thực hiện, vẫn là việc cần làm tiếp theo.

Sau khi có lượt chạy UI thật, quay lại Hướng 2 (OCR thật) cho các PDF
Scanned/Hybrid nếu có trong bộ data mẫu.

Also pending, not yet scheduled:

-   Viết "Template Authoring Guide" — cần bổ sung quy tắc về
    `sections`/`key_tokens` cho Section (VD giới hạn `MAX_KEY_WORDS=4`
    khi chọn section header dài — phát hiện từ Session 2026-08-07),
    ngoài các quy tắc đã ghi từ Session 2026-08-01/02 (tránh key 1 từ,
    tránh `value_pattern` quá lỏng).
-   Điều chỉnh `resources/excel_mapping.json` khớp workbook Excel thật
    (đã có `resources/EXCEL_MAPPING_GUIDE.md` hướng dẫn cách viết, từ
    Session 2026-08-07, nhưng bản thân file mapping mẫu vẫn chưa cập
    nhật khớp workbook thật của người dùng).
-   Đánh giá rủi ro tràn của gap-based Value merge (ADR-044) và va
    chạm section header (ADR-045) trên nhiều mẫu hóa đơn thật đa dạng
    hơn — hiện chỉ có 1 file test.
-   Tinh chỉnh `TemplateMatching.SECTION_TIE_MARGIN` cùng các hằng số
    `TemplateMatching.*` khác khi có thêm dữ liệu thật.
-   Manual verification of `WorkbookSaveError` against a real OS
    permission failure (see Section 14) — could not be reproduced in
    the root-privileged test container.
-   Unit tests for `Extractor._rotate_bbox()` (four rotation cases) —
    still open since Session 2026-07-31.
-   Resolve `processor.py` role vs `Worker.process()` — still open
    since Session 2026-07-29.
-   Resolve `main.py` vs `ui/main_window.py` entry-point discrepancy
    (see Section 14).
-   Remove dead code: `core/constants.py::UIText.REPORT_PENDING` (see
    Section 14).

---

# 16. Previous Problems & Solutions

Problem:

Writing Excel after each PDF.

Solution:

Store PDFResult in memory.

Write once.

---

Problem:

UI freezes.

Solution:

Worker + QThread.

---

Problem:

Huge memory usage.

Solution:

Release each PDF immediately.

Keep only PDFResult.

---

Problem:

Thread updating UI directly.

Solution:

Qt Signals only.

---

# 17. DO NOT CHANGE

These architectural rules are frozen.

DO NOT change unless absolutely necessary.

- process() is only an orchestrator.
- Business logic belongs to _process_pdf().
- UI never accesses business logic directly.
- Worker never accesses UI directly.
- Excel is written only once.
- PDF is processed one at a time.
- Results remain in memory.
- Communication uses Qt Signals only.
- ProcessingTable uses ProcessingTableModel.
- Incremental development workflow.

---

# 18. Future Improvements

- Logging system
- Config file
- Drag & Drop
- Multi-language UI
- Dark Mode
- Unit tests
- Plugin parser
- OCR optimization
- Batch report
- Tái cấu trúc thư mục source theo module chức năng khi hoàn thiện v1
  (VD core/parsing/template/, core/parsing/layoutlm/) — đã thảo luận sơ
  bộ, CHƯA quyết định, cần 1 phiên thảo luận riêng trước khi thực hiện
  (tránh đổi kiến trúc giữa chừng, theo Rule 1/11).
