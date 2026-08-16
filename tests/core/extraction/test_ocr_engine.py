"""
Unit test cho OCREngine._crop_roi() và OCREngine.recognize_numeric_roi()
(core/extraction/ocr_engine.py), phục vụ OCR_ACCURACY_SPECIFICATION.md.

Bối cảnh:
- _crop_roi() là @staticmethod, thuần túy hình học (không I/O, không phụ
  thuộc Tesseract) - kiểm thử trực tiếp, cùng nguyên tắc với
  Extractor._rotate_bbox() (xem tests/core/extraction/test_extractor.py):
  giá trị "expected" tự suy diễn ĐỘC LẬP theo đúng công thức Mục 4.2.A của
  OCR_ACCURACY_SPECIFICATION.md, KHÔNG copy ngược từ code đang test.

  LƯU Ý QUAN TRỌNG (khác các file test trước): công thức có phép trừ/cộng
  số thập phân (VD 0.30 - 0.02) trước khi nhân với W/H rồi truncate qua
  int() - kết quả CÓ THỂ lệch 1 đơn vị so với số học thập phân "trên giấy"
  do biểu diễn nhị phân dấu phẩy động (IEEE 754). VD: 0.30 - 0.02 trong
  Python double-precision = 0.27999999999999997, không phải 0.28 tuyệt
  đối - nhân 1000 rồi int() cho 279, không phải 280 như nhẩm tay thông
  thường sẽ suy đoán. Toàn bộ giá trị "expected" dưới đây được tính bằng
  1 script Python ĐỘC LẬP áp dụng đúng công thức tài liệu hóa (không đọc
  từ ocr_engine.py) để tránh sai lệch epsilon, không phải nhẩm tay thuần
  túy như các file test trước.
- recognize_numeric_roi() phụ thuộc Tesseract binary thật (qua pytesseract)
  - không thể kiểm thử pure như _crop_roi(). Mock pytesseract.image_to_string
  và OCREngine._ensure_traineddata() (cùng kỹ thuật mock external dependency
  đã dùng ở tests/core/system/test_hardware.py cho os.cpu_count) để kiểm
  thử ĐÚNG luồng orchestration (crop -> upscale -> build config theo
  OCR.LANG -> gọi pytesseract -> strip kết quả), KHÔNG kiểm thử độ chính
  xác nhận diện thật (cần ảnh mẫu thật + Tesseract cài sẵn, ngoài phạm vi
  unit test tự động - xem Mục 5/6 của OCR_ACCURACY_SPECIFICATION.md).
"""

from __future__ import annotations
from unittest.mock import patch
import numpy as np
from core.domain.constants import OCR
from core.domain.models import PageImage
from core.extraction.ocr_engine import OCREngine


class TestCropRoi:
    """4 case, giá trị expected tính độc lập (xem docstring module) theo
    công thức Mục 4.2.A:
        px0 = max(0, int((x0 - pad_x) * W))
        px1 = min(W, int((x1 + pad_x) * W) + 1)
        py0 = max(0, int((y0 - pad_y) * H))
        py1 = min(H, int((y1 + pad_y) * H) + 1)
    pad_x = ROI_PADDING_X = 0.02, pad_y = ROI_PADDING_Y = 0.01, W=1000, H=500.
    """

    _WIDTH = 1000
    _HEIGHT = 500

    def test_typical_bbox_with_padding(self) -> None:
        # bbox=(0.30,0.40,0.50,0.60) -> px0,py0,px1,py1 = 279,195,521,306
        # (px0=279, KHÔNG phải 280 - xem lưu ý floating-point ở docstring
        # module: 0.30-0.02 != 0.28 tuyệt đối trong double-precision).
        image = np.zeros((self._HEIGHT, self._WIDTH, 3), dtype=np.uint8)
        roi = OCREngine._crop_roi(image, (0.30, 0.40, 0.50, 0.60), self._WIDTH, self._HEIGHT)
        assert roi.shape[:2] == (306 - 195, 521 - 279)  # (111, 242)

    def test_bbox_near_left_top_edge_clamped_to_zero(self) -> None:
        # x0/y0 âm sau khi trừ padding -> clamp về 0 (Mục 4.2.A: max(0, ...)).
        # bbox=(0.01,0.005,0.10,0.10) -> px0,py0,px1,py1 = 0,0,121,56
        image = np.zeros((self._HEIGHT, self._WIDTH, 3), dtype=np.uint8)
        roi = OCREngine._crop_roi(image, (0.01, 0.005, 0.10, 0.10), self._WIDTH, self._HEIGHT)
        assert roi.shape[:2] == (56, 121)

    def test_bbox_near_right_bottom_edge_clamped_to_dimension(self) -> None:
        # x1/y1 vượt biên sau khi cộng padding -> clamp về W/H.
        # bbox=(0.90,0.90,0.995,0.998) -> px0,py0,px1,py1 = 880,445,1000,500
        image = np.zeros((self._HEIGHT, self._WIDTH, 3), dtype=np.uint8)
        roi = OCREngine._crop_roi(image, (0.90, 0.90, 0.995, 0.998), self._WIDTH, self._HEIGHT)
        assert roi.shape[:2] == (500 - 445, 1000 - 880)  # (55, 120)
        assert roi.shape[0] <= self._HEIGHT
        assert roi.shape[1] <= self._WIDTH

    def test_full_page_bbox_returns_full_image(self) -> None:
        # bbox=[0,0,1,1] - padding đẩy ra ngoài biên cả 4 phía, clamp về
        # đúng kích thước gốc.
        image = np.zeros((self._HEIGHT, self._WIDTH, 3), dtype=np.uint8)
        roi = OCREngine._crop_roi(image, (0.0, 0.0, 1.0, 1.0), self._WIDTH, self._HEIGHT)
        assert roi.shape[:2] == (self._HEIGHT, self._WIDTH)


class TestRecognizeNumericRoi:
    """Mock pytesseract.image_to_string + _ensure_traineddata() (Tesseract
    binary thật không có trong môi trường chạy test) - kiểm thử luồng
    orchestration, không kiểm thử độ chính xác nhận diện thật."""

    @staticmethod
    def _make_page_image(width: int = 200, height: int = 100) -> PageImage:
        samples = bytes(width * height * 3)
        return PageImage(samples=samples, width=width, height=height, dpi=450, channels=3)

    def test_uses_vie_whitelist_by_default(self) -> None:
        # OCR.LANG = "vie" (mặc định v1, hard-code) -> phải dùng đúng
        # OCR.ROI_CHAR_WHITELIST["vie"] (bao gồm đ/Đ/₫), PSM=7, OEM=3.
        engine = OCREngine()
        with patch.object(engine, "_ensure_traineddata"), \
             patch("core.extraction.ocr_engine.pytesseract.image_to_string") as mock_ocr:
            mock_ocr.return_value = "1.234.567,89\n"
            result = engine.recognize_numeric_roi(
                self._make_page_image(), (0.1, 0.1, 0.5, 0.5)
            )

        assert result == "1.234.567,89"
        called_config = mock_ocr.call_args.kwargs["config"]
        assert OCR.ROI_CHAR_WHITELIST["vie"] in called_config
        assert "--psm 7" in called_config
        assert "--oem 3" in called_config

    def test_falls_back_to_vie_whitelist_for_unknown_lang(self) -> None:
        # OCR.LANG bị đổi thành mã KHÔNG có trong ROI_CHAR_WHITELIST ->
        # fallback về "vie" (giữ đúng hành vi mặc định), KHÔNG raise KeyError.
        engine = OCREngine()
        with patch("core.extraction.ocr_engine.OCR.LANG", "fra"), \
             patch.object(engine, "_ensure_traineddata"), \
             patch("core.extraction.ocr_engine.pytesseract.image_to_string") as mock_ocr:
            mock_ocr.return_value = "500000"
            engine.recognize_numeric_roi(self._make_page_image(), (0.1, 0.1, 0.5, 0.5))

        called_config = mock_ocr.call_args.kwargs["config"]
        assert OCR.ROI_CHAR_WHITELIST["vie"] in called_config

    def test_strips_whitespace_from_result(self) -> None:
        engine = OCREngine()
        with patch.object(engine, "_ensure_traineddata"), \
             patch("core.extraction.ocr_engine.pytesseract.image_to_string") as mock_ocr:
            mock_ocr.return_value = "  4,842,303VND  \n"
            result = engine.recognize_numeric_roi(
                self._make_page_image(), (0.1, 0.1, 0.5, 0.5)
            )

        assert result == "4,842,303VND"

    def test_disables_dawg_dictionaries(self) -> None:
        # Whitelist ký tự chỉ hiệu quả nếu DAWG (từ điển tiếng Việt tự
        # nhiên) bị tắt - thiếu cờ này, Tesseract vẫn có thể ưu tiên từ
        # vựng thay vì cấu trúc số (Mục 2.2 spec - nguyên nhân gốc rễ).
        engine = OCREngine()
        with patch.object(engine, "_ensure_traineddata"), \
             patch("core.extraction.ocr_engine.pytesseract.image_to_string") as mock_ocr:
            mock_ocr.return_value = "5%"
            engine.recognize_numeric_roi(self._make_page_image(), (0.1, 0.1, 0.5, 0.5))

        called_config = mock_ocr.call_args.kwargs["config"]
        assert "load_system_dawg=0" in called_config
        assert "load_freq_dawg=0" in called_config
        assert "load_punc_dawg=0" in called_config

    def test_calls_ensure_traineddata_before_recognizing(self) -> None:
        # Đối xứng recognize() hiện có (ADR-061): kiểm tra vie.traineddata
        # lazy, đúng lần đầu được gọi. Xác nhận recognize_numeric_roi()
        # KHÔNG bỏ qua bước này (tránh crash mờ ám nếu thiếu tessdata).
        engine = OCREngine()
        with patch.object(engine, "_ensure_traineddata") as mock_ensure, \
             patch("core.extraction.ocr_engine.pytesseract.image_to_string") as mock_ocr:
            mock_ocr.return_value = "100"
            engine.recognize_numeric_roi(self._make_page_image(), (0.1, 0.1, 0.5, 0.5))

        mock_ensure.assert_called_once()
