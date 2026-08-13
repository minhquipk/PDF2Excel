# EXCEL_MAPPING_GUIDE.md

# Hướng dẫn tạo `excel_mapping.json`

> File này mô tả cách viết/chỉnh sửa `resources/excel_mapping.json` —
> dùng để ánh xạ cột trong Excel Table đích sang các field của
> `InvoiceInfo`, phục vụ `ExcelWriter` (`core/excel_writer.py`).
>
> Đối tượng đọc: người điều hành (office user), không yêu cầu biết lập
> trình. Chỉ cần làm theo đúng cấu trúc bên dưới.

---

## 1. Mục đích & phạm vi

`excel_mapping.json` trả lời 2 câu hỏi cho chương trình:

1. Dữ liệu hóa đơn sẽ được ghi vào **Excel Table nào** trong file
   Excel đầu ra (Output Excel chọn ở UI)?
2. Mỗi **cột** trong Table đó tương ứng với **field dữ liệu nào**
   của hóa đơn đã trích xuất được?

File này chỉ chỉnh 1 lần khi thiết lập, hoặc mỗi khi mẫu Excel đầu ra
thay đổi cấu trúc cột.

---

## 2. Yêu cầu bắt buộc trên file Excel đích

Chương trình ghi dữ liệu vào một **Excel Table** (ListObject) — **không
phải** một vùng ô (range) thông thường, dù trông giống nhau trên màn
hình.

Cách tạo Excel Table trong Excel:

1. Chọn vùng dữ liệu có sẵn dòng tiêu đề (header).
2. Insert → Table (hoặc Ctrl+T).
3. Đặt tên Table: chọn Table → tab **Table Design** → ô **Table Name**
   (góc trái) → gõ tên (ví dụ `tblInvoices`).

Nếu Table đích không tồn tại (chưa Insert → Table, hoặc bị xoá), chương
trình sẽ **dừng ghi Excel** với lỗi rõ ràng — đây là lỗi cấp toàn cục,
không thể ghi một phần.

---

## 3. Cấu trúc file JSON

```json
{
  "table": "tblInvoices",
  "columns": {
    "Invoice No": "invoice_number",
    "Date": "invoice_date",
    "Supplier": "company_name",
    "Tax Code": "tax_code",
    "Amount": "subtotal",
    "VAT Rate": "vat_rate",
    "VAT Amount": "vat_amount",
    "Total": "total_amount"
  }
}
```

- `table`: đúng tên Table đã đặt ở Bước 2 (phân biệt hoa/thường).
- `columns`: mỗi cặp `"Tên cột Excel": "field_name"`.
  - **Key** (bên trái) = tên cột **đúng như header thật** trong Excel.
  - **Value** (bên phải) = tên field dữ liệu hóa đơn (xem Mục 4).

Không bắt buộc phải khai báo đủ mọi cột có trong Table — cột nào không
khai báo trong `columns` sẽ không bị chương trình đụng tới.
---

## 4. Danh sách field hợp lệ của `InvoiceInfo`

Giá trị bên phải mỗi dòng trong `columns` **chỉ được phép** là một
trong các field sau (đúng chính tả, chữ thường, dấu gạch dưới):

| field_name       | Kiểu dữ liệu | Ghi chú                              |
|------------------|--------------|--------------------------------------|
| `source_file`    | Text         | Đường dẫn file PDF gốc (luôn có sẵn) |
| `company_name`   | Text         | Tên đơn vị bán                       |
| `tax_code`       | Text         | Mã số thuế                           |
| `address`        | Text         | Địa chỉ                              |
| `buyer_name`     | Text         | Tên người mua                        |
| `buyer_tax_code` | Text         | Mã số thuế người mua                 |
| `payment_method` | Text         | Hình thức thanh toán                 |
| `invoice_number` | Text         | Số hóa đơn                           |
| `invoice_date`   | Date         | Ngày lập hóa đơn                     |
| `subtotal`       | Decimal      | Cộng tiền hàng (chưa thuế)           |
| `vat_rate`       | Decimal      | Thuế suất GTGT (%)                   |
| `vat_amount`     | Decimal      | Tiền thuế GTGT                       |
| `total_amount`   | Decimal      | Tổng cộng tiền thanh toán            |

Nếu gõ sai tên field (kể cả lệch 1 ký tự, ví dụ `invoice_no` thay vì
`invoice_number`), chương trình sẽ **từ chối chạy ngay từ đầu**, kèm
thông báo liệt kê đầy đủ các field hợp lệ — đây là lỗi cấp toàn cục,
không đợi đến lúc ghi Excel mới phát hiện.

---

## 5. Quy tắc đặt tên cột (key bên trái)

- Phải khớp **chính xác từng ký tự** với dòng tiêu đề thật trong Excel
  Table — kể cả khoảng trắng thừa, chữ hoa/thường.
- Ví dụ: nếu header thật trong Excel là `"Invoice No."` (có dấu chấm)
  nhưng mapping ghi `"Invoice No"` (không dấu chấm) → 2 chuỗi này được
  coi là **khác nhau**, cột đó sẽ bị bỏ qua (xem Mục 6).
- Khuyến nghị: copy trực tiếp text từ ô tiêu đề trong Excel, dán vào
  JSON, tránh gõ tay để không lệch khoảng trắng/ký tự.

---

## 6. Các loại lỗi và nơi xem kết quả

| Tình huống                                                                                     | Mức độ                   | Hậu quả                                                | Xem ở đâu                              |
|------------------------------------------------------------------------------------------------|--------------------------|--------------------------------------------------------|----------------------------------------|
| `excel_mapping.json` sai cú pháp JSON, thiếu `table`/`columns`, hoặc `field_name` sai chính tả | **Toàn cục (fatal)**     | Dừng ghi Excel hoàn toàn, không ghi được dòng nào      | Popup lỗi trên UI khi bấm Start        |
| `table` không tồn tại trong Output Excel đã chọn                                               | **Toàn cục (fatal)**     | Dừng ghi Excel hoàn toàn                               | Popup lỗi trên UI                      |
| Tên cột trong `columns` không khớp header thật của Table                                       | **Từng cột (soft-fail)** | Cột đó bị bỏ qua, các cột khác vẫn ghi bình thường     | `reports/Report.txt`, mục **Errors**   |
| Một field bị `None` (không trích được từ PDF)                                                  | **Từng ô (warning)**     | Ô đó để trống, các field khác của cùng hóa đơn vẫn ghi | `reports/Report.txt`, mục **Warnings** |

Quy tắc chung: **lỗi cấu hình** (mapping sai, Table không tồn tại) luôn
chặn toàn bộ; **lỗi dữ liệu từng phần** (cột lệch tên, field rỗng)
không bao giờ làm mất dữ liệu của các hóa đơn/cột/field còn lại.

---

## 7. Checklist trước khi chạy thật

- [ ] File Excel đầu ra đã có sẵn Excel Table (Insert → Table), có tên
      trùng khớp với `table` trong JSON.
- [ ] Mỗi tên cột trong `columns` đã copy đúng từ header thật trong
      Excel (không gõ tay).
- [ ] Mỗi `field_name` bên phải đã đối chiếu đúng bảng ở Mục 4.
- [ ] File JSON hợp lệ (không thiếu dấu phẩy/ngoặc — có thể dán thử
      vào một công cụ kiểm tra JSON online nếu không chắc).
- [ ] Sau lần chạy thử đầu tiên: mở `reports/Report.txt`, kiểm tra mục
      **Errors** — nếu có, đối chiếu lại tên cột ở Mục 5.