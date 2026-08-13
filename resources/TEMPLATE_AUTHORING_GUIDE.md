# TEMPLATE_AUTHORING_GUIDE.md

# Hướng dẫn viết Template Definition (`resources/templates/*.json`)

> File này mô tả cách viết/chỉnh sửa một Template Definition JSON —
> dùng để `TemplateMatcher` (`core/template_matcher.py`) nhận diện mẫu
> hóa đơn và trích xuất field, phục vụ `Parser` (`core/parser.py`).
>
> Đối tượng đọc: người điều hành (office user) muốn thêm/sửa mẫu hóa
> đơn mới, không yêu cầu biết lập trình — chỉ cần hiểu đúng cấu trúc và
> các quy tắc an toàn bên dưới.
>
> Toàn bộ ví dụ trong tài liệu này trích trực tiếp từ
> `resources/templates/sample_invoice_v1.json` (v4) — template duy nhất
> hiện đã verify 12/12 field đúng trên PDF hóa đơn thật
> (`HD2026-0003_digital.pdf`).

---

## 1. Mục đích & phạm vi

Một Template Definition trả lời 2 câu hỏi cho `TemplateMatcher`:

1. **Đây có phải mẫu hóa đơn mà template này mô tả không?** (Bước
   Score + Decision — xem Mục 5).
2. **Nếu đúng, mỗi field của `InvoiceInfo` nằm ở đâu trên trang, và
   giá trị trông như thế nào?** (Bước Windowing + Value Matching —
   xem Mục 6, 7).

Mỗi file `.json` trong `resources/templates/` là 1 Template Definition
độc lập. `TemplateLoader` (`core/template_loader.py`) đọc **toàn bộ**
file `.json` trong thư mục này ở mỗi lần khởi động `Worker`.

**Fail-soft per file (ADR-031):** nếu 1 file JSON sai cú pháp hoặc sai
schema, `TemplateLoader` chỉ bỏ qua đúng file đó (log warning), các
template khác vẫn hoạt động bình thường — không dừng cả ứng dụng.

---

## 2. Cấu trúc tổng quan

```json
{
  "template_id": "sample_invoice_v1",
  "version": 4,
  "description": "...",
  "sections": [ ... ],
  "fields": [ ... ]
}
```

| Khóa | Kiểu | Bắt buộc | Ghi chú |
|------|------|----------|---------|
| `template_id` | string | Có | Định danh duy nhất, dùng khi log. |
| `version` | int | Có | Tăng thủ công mỗi khi sửa template — không có ý nghĩa nghiệp vụ nào khác ngoài truy vết lịch sử qua log. |
| `description` | string | Không | Ghi chú tự do. Khuyến nghị mạnh: ghi rõ **đã verify trên PDF nào**, **những gì đã sửa/tại sao** — xem cách `sample_invoice_v1.json` đang làm, giúp phiên làm việc sau không lặp lại thử nghiệm đã biết kết quả. |
| `sections` | array | Có (tối thiểu 1) | Xem Mục 4. |
| `fields` | array | Có (tối thiểu 1) | Xem Mục 5. `TemplateLoader` sẽ raise lỗi và bỏ qua file nếu `fields` rỗng. |

---

## 3. Danh sách field hợp lệ của `InvoiceInfo`

Giá trị `field_name` trong mỗi field **chỉ được phép** là một trong
các tên sau (khớp chính xác `core/models.py::InvoiceInfo`):

| `field_name` | Kiểu dữ liệu (`value_type`) |
|---------------|------------------------------|
| `company_name` | Text |
| `tax_code` | Text |
| `address` | Text |
| `buyer_name` | Text |
| `buyer_tax_code` | Text |
| `payment_method` | Text |
| `invoice_number` | Text |
| `invoice_date` | Date |
| `subtotal` | Decimal |
| `vat_rate` | Decimal |
| `vat_amount` | Decimal |
| `total_amount` | Decimal |

`source_file` **không** khai trong template — Parser tự gán từ đường
dẫn PDF gốc.

Nếu gõ sai `field_name`, `FieldDefinition.__post_init__`
(`core/models.py`) raise `ValueError` ngay khi load — `TemplateLoader`
bắt lỗi này và bỏ qua toàn bộ file (fail-soft per file, Mục 2).

---

## 4. `sections` — khối tài liệu

### 4.1. Vì sao cần Section

Một hóa đơn thường có nhiều khối lặp lại cùng loại nhãn (VD "Mã số
thuế:" xuất hiện cả ở khối Bên bán lẫn Bên mua). Nếu tìm `key_tokens`
trên toàn văn bản không giới hạn phạm vi, `tax_code` có thể bị lấy
nhầm giá trị của `buyer_tax_code` (đã xảy ra thật, xem ADR-045).
`sections` giải quyết vấn đề này bằng cách giới hạn phạm vi tìm kiếm
`key_tokens` của mỗi field vào đúng 1 khối tài liệu.

### 4.2. Cấu trúc 1 section

```json
{
  "section_id": "seller",
  "key_tokens": ["don vi ban hang"],
  "fuzzy_threshold": 85
}
```

| Khóa | Kiểu | Ghi chú |
|------|------|---------|
| `section_id` | string | Định danh, field tham chiếu qua field `section` (Mục 5). |
| `key_tokens` | array of string, hoặc `null` | Cụm từ đánh dấu **điểm bắt đầu** khối này trên trang. `null` = khối "ảo" bắt đầu từ đỉnh trang đầu tiên, không cần marker thật — dùng cho phần đầu tài liệu chưa có tiêu đề khối rõ ràng (VD số/ngày hóa đơn, trước khối "ĐƠN VỊ BÁN HÀNG"). |
| `fuzzy_threshold` | int (0-100) | Ngưỡng tối thiểu để coi là khớp (thang `rapidfuzz.fuzz.ratio()`). Mặc định 85 nếu bỏ qua. |

Ví dụ đầy đủ 4 section trong `sample_invoice_v1.json`:

```json
"sections": [
  { "section_id": "header", "key_tokens": null },
  { "section_id": "seller", "key_tokens": ["don vi ban hang"], "fuzzy_threshold": 85 },
  { "section_id": "buyer", "key_tokens": ["thong tin nguoi mua"], "fuzzy_threshold": 85 },
  { "section_id": "detail", "key_tokens": ["chi tiet thanh toan"], "fuzzy_threshold": 85 }
]
```

**Lưu ý viết `key_tokens` cho Section: không dấu tiếng Việt cũng
được** — `TemplateMatcher._strip_diacritics()` tự chuẩn hóa cả 2 phía
(template và PDF thật) trước khi so khớp (ADR-035), nên viết có dấu
hay không dấu đều cho kết quả như nhau. Các ví dụ trong tài liệu này
và trong `sample_invoice_v1.json` dùng dạng không dấu theo thói quen
đã có, nhưng đây không phải yêu cầu bắt buộc.

### 4.3. Cách tài liệu được chia khối

`TemplateMatcher._resolve_sections()` tìm vị trí khớp tốt nhất của mỗi
section header trên toàn tài liệu, sắp theo thứ tự xuất hiện
(page → trên xuống dưới), rồi dựng khoảng `[bắt đầu section này, bắt
đầu section kế tiếp)`. Field thuộc section nào chỉ được tìm
`key_tokens` trong đúng khoảng đó.

**Section không tìm được** (không khớp, hoặc khớp mơ hồ — xem Mục
4.4) sẽ **vắng mặt** trong kết quả chia khối. Mọi field thuộc section
đó coi như "không tìm được" cho template này — không raise lỗi, không
crash (đối xứng nguyên tắc "UNKNOWN là absence of decision", ADR-027).

### 4.4. ⚠️ Quy tắc bắt buộc: giới hạn 4 từ cho `key_tokens` của Section

`TemplateMatching.MAX_KEY_WORDS = 4` (`core/constants.py`) giới hạn độ
dài cụm từ (candidate phrase) mà Key Matching có thể sinh ra bằng
sliding window. **Section header dài hơn 4 từ sẽ KHÔNG BAO GIỜ đạt độ
khớp tuyệt đối**, vì candidate dài nhất mà thuật toán tạo ra chỉ gồm 4
từ liên tiếp.

Ví dụ thật đã gặp (Session 2026-08-07): tiêu đề PDF ghi đầy đủ "THÔNG
TIN NGƯỜI MUA HÀNG:" (5 từ). Nếu khai `key_tokens: ["thong tin nguoi
mua hang"]` (5 từ), ratio tối đa có thể đạt được sẽ luôn thấp hơn 100
— rủi ro fail `SECTION_TIE_MARGIN` (Mục 4.5). Giải pháp đã dùng: rút
gọn còn 4 từ đầu, khớp một phần cụm dài hơn trên PDF:

```json
{ "section_id": "buyer", "key_tokens": ["thong tin nguoi mua"] }
```

**Quy tắc:** khi viết `key_tokens` cho Section, đếm số từ trong PDF
thật — nếu tiêu đề khối dài hơn 4 từ, chỉ lấy tối đa 4 từ đầu (hoặc
cụm 4 từ đặc trưng nhất, không nhất thiết phải là 4 từ đầu, miễn là
cụm đó xuất hiện liên tục trên PDF).

### 4.5. Rủi ro va chạm giữa các Section

Section dùng ngưỡng phân biệt riêng, chặt hơn field thường:
`TemplateMatching.SECTION_TIE_MARGIN = 10` (thang 0-100 của
`rapidfuzz.fuzz.ratio()`) — nếu 2 vị trí trên tài liệu khớp
`key_tokens` của section với độ chênh lệch ratio nhỏ hơn 10, section
đó bị coi là "không xác định được" (ambiguous), không phải lỗi crash
nhưng field bên trong sẽ ra `None`.

**Quy tắc:** chọn `key_tokens` cho mỗi Section đủ **đặc trưng**, tránh
trùng lặp gần giống với section khác trong cùng template. Header
càng dài/riêng biệt thì càng an toàn (nhưng không vượt quá 4 từ, xem
Mục 4.4) — đây là 2 ràng buộc cần cân bằng khi chọn `key_tokens`.

Rủi ro này **giảm mạnh nhưng không triệt tiêu hoàn toàn** ngay cả khi
tuân thủ đúng quy tắc — đây là giới hạn cố hữu đã ghi nhận (ADR-045).

---

## 5. `fields` — khai báo từng trường dữ liệu

### 5.1. Cấu trúc 1 field

Ví dụ field `tax_code` từ `sample_invoice_v1.json`:

```json
{
  "field_name": "tax_code",
  "section": "seller",
  "value_type": "Text",
  "identification_weight": 1.0,
  "key_tokens": ["ma so thue"],
  "fuzzy_threshold": 90,
  "spatial_relation": {
    "direction": "Right",
    "max_distance": 0.15,
    "axis_tolerance": 0.006
  },
  "value_pattern": "^[0-9]{10,14}(-[0-9]{3})?$"
}
```

| Khóa | Kiểu | Ghi chú |
|------|------|---------|
| `field_name` | string | Phải khớp đúng 1 tên trong Mục 3. |
| `section` | string | **Bắt buộc**, không có giá trị mặc định — phải khớp đúng 1 `section_id` đã khai ở Mục 4. Thiếu field này khiến `TemplateLoader` bỏ qua toàn bộ file (ADR-045). |
| `value_type` | `"Text"` \| `"Decimal"` \| `"Date"` | Quyết định cách `ValueConverter` convert raw text. |
| `identification_weight` | float (0.0 - 1.0) | Xem Mục 5.2. |
| `key_tokens` | array of string | Cụm từ nhãn để tìm vị trí field (VD "Mã số thuế:"). Xem Mục 5.3. |
| `fuzzy_threshold` | int (0-100) | Ngưỡng khớp tối thiểu cho field này (khác thang `SECTION_TIE_MARGIN`, field không dùng tie-margin riêng — best-match tuyệt đối). |
| `spatial_relation` | object | Vị trí giá trị so với nhãn đã khớp. Xem Mục 6. |
| `value_pattern` | string (regex) | Mẫu để lọc giá trị hợp lệ trong cửa sổ tìm kiếm. Xem Mục 7. |
| `date_format` | string, tùy chọn | Bắt buộc nếu `value_type = "Date"` (VD `"%d/%m/%Y"`). |
| `decimal_format` | object, tùy chọn | Override `thousand_separator`/`decimal_separator` mặc định. Xem Mục 7.3. |

### 5.2. `identification_weight` — trọng số nhận diện template

`TemplateMatcher._score_template()` chấm điểm mỗi template bằng:

```
score = Σ(identification_weight của field có key khớp) / Σ(identification_weight của mọi field)
```

Template đạt điểm cao nhất, vượt `TEMPLATE_MIN_SCORE = 0.5` và chênh
lệch với hạng nhì ≥ `TEMPLATE_TIE_MARGIN = 0.10` mới được chọn
(ADR-030).

**Quy tắc:** chỉ gán `identification_weight` cao (VD `1.0`) cho field
mang tính **định danh nhà cung cấp** — field mà nếu khớp đúng, gần như
chắc chắn xác nhận đây đúng loại hóa đơn (VD `tax_code`). Field mang
tính generic, xuất hiện giống nhau ở mọi loại hóa đơn (VD
`invoice_date`) nên để weight thấp hoặc `0.0` — nếu không, việc chọn
sai template có thể xảy ra chỉ vì field generic tình cờ khớp.

Trong `sample_invoice_v1.json`: chỉ `company_name` (0.5) và `tax_code`
(1.0) có weight dương; toàn bộ field còn lại là `0.0` — tức là chỉ 2
field này quyết định việc chọn template, các field khác chỉ phục vụ
trích xuất giá trị sau khi đã chọn xong.

### 5.3. `key_tokens` của field — tránh từ khóa 1 từ

**Quy tắc:** **không dùng `key_tokens` chỉ gồm 1 từ**, trừ khi từ đó
chắc chắn không xuất hiện ở ngữ cảnh nào khác trong tài liệu.

Đã xảy ra thật (Session 2026-08-01/02): `key_tokens: ["so"]` cho field
`invoice_number` từng khớp nhầm với từ "số" đứng độc lập trong cụm
"Mã số thuế" ở dòng khác — không phải lỗi thuật toán (rapidfuzz trả
kết quả đúng bản chất theo dữ liệu đưa vào), mà là lỗi thiết kế
`key_tokens` quá ngắn/chung chung.

Section (Mục 4) đã giảm đáng kể rủi ro này bằng cách giới hạn phạm vi
tìm kiếm vào đúng khối — nhưng nếu 1 section có nhiều field cùng dùng
key ngắn, va chạm vẫn có thể xảy ra trong nội bộ section đó. Luôn ưu
tiên cụm từ 2+ từ, càng gần với nhãn thật trên PDF càng tốt.

---

## 6. `spatial_relation` — vị trí giá trị so với nhãn

```json
"spatial_relation": {
  "direction": "Right",
  "max_distance": 0.15,
  "axis_tolerance": 0.006
}
```

| Khóa | Kiểu | Ghi chú |
|------|------|---------|
| `direction` | `"Right"` \| `"Left"` \| `"Below"` \| `"Above"` | Hướng tìm giá trị tính từ vị trí nhãn đã khớp. |
| `max_distance` | float [0.0, 1.0] | Khoảng cách tối đa theo trục chính (tỉ lệ so với kích thước trang). |
| `axis_tolerance` | float [0.0, 1.0] | Dung sai theo trục vuông góc. |

Tất cả tọa độ dùng thang chuẩn hóa `[0.0, 1.0]`
(`WordToken.normalized_bbox`), không phụ thuộc kích thước/DPI PDF thật
— viết template không cần biết PDF gốc bao nhiêu pixel.

### 6.1. `axis_tolerance` — 2 quy tắc thực nghiệm quan trọng

**Quy tắc:** dùng `axis_tolerance` nhỏ, khoảng **0.006** — KHÔNG dùng
giá trị lớn (0.02-0.05).

Phát hiện qua thực nghiệm thật (Session 2026-08-07): khoảng cách dòng
thật đo được trên PDF mẫu chỉ khoảng 0.0168-0.0202 (tỉ lệ trang).
`axis_tolerance` lớn hơn mức này khiến cửa sổ tìm kiếm hướng
`Right`/`Below` **tràn sang dòng liền kề** — từng khiến field
`buyer_name` lấy nhầm giá trị `'mua:'` (một phần nhãn của dòng khác)
thay vì tên người mua thật.

Toàn bộ 12 field trong `sample_invoice_v1.json` hiện dùng
`axis_tolerance: 0.006` — dùng làm mức khởi điểm khi viết field mới,
chỉ tăng nếu có bằng chứng thực nghiệm cho thấy giá trị bị cắt do dung
sai quá chặt.

### 6.2. `max_distance` — đủ lớn cho field căn phải

**Quy tắc:** với field mà nhãn nằm sát lề trái nhưng giá trị căn phải
xa (điển hình: các field tiền tệ trong bảng chi tiết thanh toán),
`max_distance` cần đặt đủ lớn — tham khảo **0.85** (giá trị đã verify
trong `sample_invoice_v1.json` cho `subtotal`/`vat_rate`/
`vat_amount`/`total_amount`).

Phát hiện qua thực nghiệm: nếu đặt `max_distance` nhỏ (0.1-0.2) cho
nhóm field này, cửa sổ tìm kiếm không đủ rộng để chạm tới vị trí giá
trị thật → field luôn ra `None`, dù key đã khớp đúng.

Ngược lại, field mà giá trị nằm ngay sát nhãn (VD `tax_code`,
`invoice_number`) nên dùng `max_distance` nhỏ (0.15) — tránh cửa sổ
tìm kiếm quá rộng vô tình chạm token của field khác.

**Tóm lại: `max_distance` không có 1 giá trị "đúng" chung cho mọi
field — phải ước lượng dựa trên khoảng cách thật giữa nhãn và giá trị
trên PDF mẫu, verify bằng cách chạy thử, không đoán.**

---

## 7. `value_pattern` — lọc giá trị hợp lệ

`value_pattern` là 1 regex (cú pháp Python `re`) mà token trong cửa sổ
tìm kiếm phải khớp (`pattern.match()`) để được coi là giá trị ứng
viên.

### 7.1. Không dùng pattern quá lỏng

**Quy tắc:** tránh `value_pattern: ".+"` — pattern này chấp nhận cả
token chỉ có dấu câu (VD `":"`), và vì Value Matching tie-break theo
khoảng cách gần nhất, dấu `:` đứng ngay sau nhãn có thể bị chọn nhầm
làm giá trị (gần nhãn hơn giá trị thật).

Khuyến nghị: pattern yêu cầu ít nhất 1 ký tự alphanumeric, VD dạng
`.*[^\s:.,\-].*`, hoặc — tốt hơn — viết pattern **chặt theo đúng định
dạng dữ liệu mong đợi** (xem ví dụ `tax_code` ở Mục 5.1: chỉ chấp nhận
10-14 chữ số, có thể kèm hậu tố `-3 chữ số`).

### 7.2. Field tiền tệ — chấp nhận hậu tố đơn vị dính liền

Với PDF quét (OCR), Tesseract có thể gộp ký hiệu đơn vị tiền tệ dính
liền số thành 1 token (VD `"4,842,303VND"`, không có khoảng trắng).
Nếu `value_pattern` chỉ cho phép `[0-9.,]+`, token này sẽ bị loại,
field ra `None` dù vị trí đã đúng (phát hiện thật, ADR-051 — ~15% data
PDF Scanned từng bị ảnh hưởng).

**Pattern mẫu đã verify** (dùng cho `subtotal`/`vat_amount`/
`total_amount` trong `sample_invoice_v1.json`):

```
^[0-9.,]+\s*(?:(?i:vn[dđ])|₫|[đĐ])?$
```

`ValueConverter._strip_currency_suffix()` sẽ tự strip hậu tố này trước
khi convert sang `Decimal` — template chỉ cần đảm bảo pattern **không
loại bỏ** token có hậu tố, phần strip đã có sẵn ở tầng convert.

### 7.3. Field phần trăm — chấp nhận `%` dính liền

Tương tự, PyMuPDF/OCR có thể không tách khoảng trắng giữa số và `%`
(VD `"5%"` là 1 token). Pattern mẫu cho `vat_rate`:

```
^[0-9]{1,2}%?$
```

`ValueConverter._to_decimal()` tự strip `%` và chia 100 (ADR-043).

### 7.4. `decimal_format` — khi định dạng số khác chuẩn VN

Mặc định hệ thống dùng `.` làm thousand separator, `,` làm decimal
separator (chuẩn VN). Nếu nguồn PDF dùng ngược lại (VD PDF test dùng
`,` ngăn hàng nghìn — xác nhận là đặc thù của riêng bộ dữ liệu test,
không đại diện hóa đơn VN thật), override riêng cho field đó — **không
đổi mặc định toàn cục**:

```json
"decimal_format": {
  "thousand_separator": ",",
  "decimal_separator": "."
}
```

---

## 8. Value nhiều từ (field Text) — quy tắc dấu `:` kết thúc nhãn

Với field `value_type: "Text"`, `TemplateMatcher._merge_same_line()`
tự động ghép nhiều `WordToken` liền kề cùng dòng thành 1 giá trị (VD
tên công ty, địa chỉ — thường dài hơn 1 từ). Cơ chế dừng mở rộng khi
gặp token **kết thúc bằng dấu `:`** — vì trong dữ liệu thực nghiệm,
token dạng này luôn là phần còn lại của 1 nhãn khác, không bao giờ là
giá trị thật (ADR-044).

**Quy tắc khi thiết kế/kiểm tra PDF nguồn:** nếu 1 dòng có 2 field
liền kề nhau (VD nhãn field A và ngay sau đó là nhãn field B trên cùng
dòng), đảm bảo nhãn field B **kết thúc bằng dấu `:`**. Nếu không, giá
trị của field A có nguy cơ bị ghép tràn sang lấn cả nhãn/giá trị của
field B.

Đây là giới hạn cố hữu của cơ chế gap-based (đánh đổi độ đầy đủ lấy
rủi ro tràn) — không phải lỗi implementation, và **chưa loại bỏ hoàn
toàn** dù đã có điều kiện dừng ở dấu `:` (ADR-044).

---

## 9. Checklist trước khi đưa template vào dùng thật

- [ ] Mọi `field_name` đã đối chiếu đúng bảng ở Mục 3.
- [ ] Mọi field đã khai `section` khớp đúng 1 `section_id` đã định
      nghĩa.
- [ ] Section `key_tokens` không dài quá 4 từ (Mục 4.4).
- [ ] Section `key_tokens` đủ đặc trưng, không trùng lặp gần giống
      section khác (Mục 4.5).
- [ ] `key_tokens` của field không chỉ gồm 1 từ chung chung (Mục 5.3).
- [ ] `identification_weight` chỉ gán cao cho field định danh nhà
      cung cấp (Mục 5.2).
- [ ] `axis_tolerance` ở mức nhỏ (~0.006), trừ khi có lý do thực
      nghiệm cụ thể để tăng (Mục 6.1).
- [ ] `max_distance` đủ lớn cho field có giá trị nằm xa nhãn (Mục
      6.2) — đã đo thử trên PDF mẫu, không đoán.
- [ ] `value_pattern` không quá lỏng (`.+`), có xét khả năng OCR gộp
      hậu tố đơn vị (VND/`%`) nếu là field số (Mục 7).
- [ ] Nếu dòng có 2 field liền kề, nhãn field thứ 2 kết thúc bằng `:`
      (Mục 8).
- [ ] **Đã chạy thử thật** trên tối thiểu 1 PDF mẫu thuộc đúng loại
      hóa đơn này, đối chiếu từng field với nội dung PDF gốc — không
      chỉ dựa vào review JSON tĩnh. Toàn bộ quy tắc trong tài liệu này
      đều đúc kết từ việc **chạy thật phát hiện lỗi**, không phải suy
      đoán trước (xem SESSION_SUMMARIES.md các phiên liên quan).

---

## 10. Giới hạn đã biết, chưa có giải pháp (đọc để hiểu rủi ro còn lại)

Tuân thủ đúng mọi quy tắc ở trên **giảm mạnh nhưng không loại bỏ hoàn
toàn** các rủi ro sau (ghi nhận minh bạch, xem thêm
`PROJECT_CONTEXT.md` §14 và các ADR liên quan):

- Gap-based Value merge (Mục 8) vẫn có thể tràn nếu nhãn liền kề không
  kết thúc bằng `:` — chưa có giải pháp thay thế.
- Section header vẫn có thể va chạm lý thuyết nếu 2 khối dùng
  `key_tokens` gần giống nhau, dù đã chọn header đặc trưng.
- `SECTION_TIE_MARGIN`, `TEMPLATE_TIE_MARGIN`, `TEMPLATE_MIN_SCORE` và
  các hằng số khác trong `TemplateMatching`
  (`core/constants.py`) hiện là giá trị ước lượng ban đầu, cần tinh
  chỉnh thêm khi có nhiều mẫu hóa đơn thật đa dạng hơn — không coi là
  hằng số cố định vĩnh viễn.
