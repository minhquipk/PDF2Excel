# DEVELOPMENT_WORKFLOW.md

# Quy Trình Phát Triển

File này định nghĩa cách dự án này được phát triển.

------------------------------------------------------------------------

# Nguyên Tắc Cốt Lõi

Luôn giữ dự án ở trạng thái chạy được (runnable).

Không bao giờ implement nhiều module cùng lúc.

Mọi thay đổi phải nhỏ, có thể test được, và có thể đảo ngược
(reversible).

------------------------------------------------------------------------

# Chu Trình Phát Triển Chuẩn

1. Thảo luận
   ↓
2. Thống nhất kiến trúc
   ↓
3. Implement
   ↓
4. Compile
   ↓
5. Run
   ↓
6. Verify
   ↓
7. Commit
   ↓
Lặp lại

------------------------------------------------------------------------

# Các Quy Tắc (Rules)

## Rule 1

Không bao giờ thay đổi kiến trúc mà không thảo luận trước.

------------------------------------------------------------------------

## Rule 2

Không bao giờ sinh ra một lượng lớn code cùng lúc.

Implement từng file một.

------------------------------------------------------------------------

## Rule 3

Chỉ implement đúng 1 tính năng tại 1 thời điểm.

Ví dụ:

**ĐÚNG**

```
Progress
  ↓ Test
Table
  ↓ Test
Report
  ↓ Test
```

**SAI**

```
Progress
Table
Report
Worker
Excel
...
  ↓ Test
```

------------------------------------------------------------------------

## Rule 4

Luôn review source code hiện tại của project trước khi đề xuất kiến
trúc hoặc implementation.

Source code là tham chiếu implementation duy nhất.

Không bao giờ dựa vào lịch sử chat.

------------------------------------------------------------------------

## Rule 5

Khi review code, luôn giải thích:

- Sửa ở đâu
- Code mới là gì
- Tại sao

Không bao giờ viết lại toàn bộ 1 file.

------------------------------------------------------------------------

## Rule 6

Business Logic và UI hoàn toàn tách biệt.

UI không bao giờ xử lý PDF.

Worker không bao giờ truy cập UI.

------------------------------------------------------------------------

## Rule 7

`process()` phải luôn là orchestrator.

Business logic thuộc về `_process_pdf()`.

------------------------------------------------------------------------

## Rule 8

Luôn giữ Mock Mode hoạt động được.

Mock Mode được dùng trước mỗi module mới.

------------------------------------------------------------------------

## Rule 9

Không tối ưu sớm.

Đúng đắn (correctness) trước. Hiệu năng (performance) sau.

------------------------------------------------------------------------

## Rule 10

Khi 1 quyết định thiết kế trở nên ổn định, cập nhật `PROJECT_CONTEXT.md`.

Không dựa vào lịch sử chat.

------------------------------------------------------------------------

## Rule 11

Đóng băng thiết kế (freeze design) trước khi implement.

Sau khi implementation bắt đầu:

- Ưu tiên code hơn thảo luận.
- Review sau khi implement.
- Tránh mở lại thảo luận kiến trúc trừ khi thật sự cần thiết.

------------------------------------------------------------------------

## Rule 12

Quy trình implementation:

```
Thảo luận
  ↓
Đóng băng kiến trúc (Architecture Freeze)
  ↓
Review Source
  ↓
Implementation
  ↓
Review
  ↓
Fix
  ↓
Freeze
```

------------------------------------------------------------------------

## Rule 13 — Xác nhận trước khi triển khai

Mọi đề xuất thay đổi (code, kiến trúc, hoặc nội dung 5 file nhật ký dự
án) phải được người dùng xác nhận trước khi triển khai/áp dụng. Đề
xuất chỉ dừng ở mức bản nháp/kế hoạch cho đến khi có xác nhận rõ ràng.

Với các thay đổi khối lượng lớn (VD biên tập nhiều file cùng lúc), ưu
tiên trình bày và xác nhận theo từng phần nhỏ (1 file/1 bước — theo
đúng tinh thần Rule 2/3), thay vì áp dụng toàn bộ 1 lần rồi mới xin
xác nhận.

------------------------------------------------------------------------

## Rule 14 — Trách nhiệm ghi nhật ký dự án

Việc ghi chép 5 file nhật ký dự án
(`ARCHITECTURE_DECISIONS.md`/`CHANGELOG.md`/`SESSION_SUMMARIES.md`/
`PROJECT_CONTEXT.md`/`DEVELOPMENT_WORKFLOW.md`) là trách nhiệm của
Assistant, không phải người dùng.

Assistant chỉ cập nhật nhật ký khi người dùng yêu cầu (không tự động
cập nhật sau mỗi phần việc nhỏ), và khi cập nhật, phải tuân thủ đúng
phân công vai trò giữa các file:

- **ARCHITECTURE_DECISIONS.md** — quyết định kiến trúc đã chốt + lý do
  kỹ thuật đầy đủ.
- **CHANGELOG.md** — diff thuần túy (file nào, thay đổi gì), kèm
  pointer `→ ADR-xxx` cho lý do. Không giải thích "tại sao".
- **SESSION_SUMMARIES.md** — bối cảnh thảo luận, phương án bị bác bỏ,
  vướng mắc thực nghiệm. Không lặp lại lý do kỹ thuật đã có ở ADR.
- **PROJECT_CONTEXT.md** — bức ảnh chụp trạng thái HIỆN TẠI (living
  document), không phải lịch sử.
- **DEVELOPMENT_WORKFLOW.md** — quy tắc/quy trình làm việc.

------------------------------------------------------------------------

## Rule 15 — Đối chiếu định kỳ tài liệu với source thật

Nhật ký dự án (đặc biệt ADR) mô tả hành vi code, nhưng không có cơ chế
nào tự động đảm bảo mô tả đó vẫn đúng theo thời gian — code có thể đổi
mà tài liệu không được cập nhật theo, hoặc tài liệu mô tả sai ngay từ
đầu mà không ai phát hiện (đã từng xảy ra thật: mismatch giữa ADR-027
và `Extractor.extract()` tồn tại xuyên suốt 3 file nhật ký trong nhiều
tuần, chỉ được phát hiện tình cờ qua rà soát không liên quan tại
Session 2026-08-12 — xem ADR-056).

Để giảm rủi ro này:

- Trước khi đóng 1 giai đoạn lớn (VD đóng 1 version, hoặc theo yêu cầu
  của người dùng), Assistant chủ động đối chiếu 1 tập ngẫu nhiên/có
  chủ đích các ADR còn hiệu lực (`Status: Accepted`, chưa bị supersede)
  với source code thật tương ứng, không chỉ dựa vào trí nhớ từ các
  phiên trước.
- Khi rà soát source cho mục đích khác (debug, thêm tính năng, review
  theo Rule 4) mà phát hiện sai lệch với ADR/CHANGELOG/PROJECT_CONTEXT.md,
  Assistant báo ngay cho người dùng, không âm thầm bỏ qua hay tự ý
  sửa 1 bên (code hoặc tài liệu) mà không xác nhận trước — quyết định
  sửa code khớp tài liệu hay sửa tài liệu khớp code phụ thuộc vào lý
  do kiến trúc ban đầu của quyết định đó (xem ví dụ xử lý ADR-027 tại
  ADR-056: sửa code vì ADR có lập luận kiến trúc rõ ràng, không phải
  mô tả tùy tiện).
- Cơ chế này bổ trợ, không thay thế, nguyên tắc "chạy thật để verify"
  và Rule 4 (source code là tham chiếu duy nhất) đã áp dụng xuyên suốt
  dự án.

------------------------------------------------------------------------