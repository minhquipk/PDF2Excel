"""OCR engine thật, dùng Tesseract 5.x + tessdata_best (qua pytesseract).

Thay thế Mock (ADR-013: Mock First -> Replace Mock). Giữ nguyên contract
đã có với Extractor (ADR-024/025): nhận PageImage, trả về raw, chưa
normalize - Extractor vẫn là nơi duy nhất chuẩn hoá hình học.

Lưu ý triển khai: Tesseract là binary hệ thống, KHÔNG cài qua pip - phải
tự cài riêng trên máy (VD `brew install tesseract` trên macOS). File
vie.traineddata (tessdata_best, độ chính xác cao hơn hẳn tessdata mặc
định của hệ điều hành) cũng phải tự tải và đặt vào TESSDATA_DIR
(xem config.py) - không đi kèm sẵn khi cài Tesseract qua trình quản lý
gói hệ thống.
"""

from __future__ import annotations
import cv2
import numpy as np
import pytesseract
from PIL import Image
from config import TESSDATA_DIR
from core.domain.constants import OCR
from core.domain.models import PageImage


class OCREngine:
    """Nhận dạng chữ trên page_image đã render (Tesseract 5.x, LSTM/tessdata_best).

    Symmetric với PDFReader: trả về raw, un-normalized output. Toàn bộ
    chuẩn hoá toạ độ vẫn là trách nhiệm duy nhất của Extractor.

    Deskew (làm thẳng trang trước khi detect) được thực hiện NỘI BỘ tại
    đây, không lộ ra ngoài contract recognize() - Extractor không cần
    biết trang có bị nghiêng hay không, chỉ nhận bbox đã đúng vị trí
    trên page_image gốc (canvas giữ nguyên kích thước sau deskew).

    Kiểm tra sự tồn tại của tessdata_best (vie.traineddata) được trì
    hoãn đến lần đầu tiên recognize() thực sự được gọi (xem
    _ensure_traineddata()), KHÔNG thực hiện trong __init__() - khác
    thiết kế ban đầu của ADR-047. Lý do: Worker.__init__() khởi tạo
    Extractor()/OCREngine() vô điều kiện ngay khi mở ứng dụng (trước
    khi biết batch có PDF Scanned/Hybrid nào không), nên fail-fast
    trong __init__() khiến TOÀN BỘ ứng dụng crash ngay lúc khởi động
    nếu thiếu tessdata_best - kể cả với người dùng chỉ xử lý PDF
    Digital, không bao giờ chạm tới OCR. Xem amend ADR-047.
    """

    def __init__(self) -> None:
        # Cấu hình Tesseract dựng 1 lần, tái sử dụng cho mọi lần gọi
        # recognize() - không đổi giữa các trang/PDF trong cùng batch.
        self._config = f'--tessdata-dir "{TESSDATA_DIR}" --psm {OCR.PSM} --oem {OCR.OEM}'
        self._traineddata_checked = False

    def _ensure_traineddata(self) -> None:
        """Kiểm tra vie.traineddata tồn tại - chỉ chạy thật sự lần đầu.

        Cache qua self._traineddata_checked để không lặp lại I/O này ở
        mỗi trang/mỗi PDF trong cùng batch (recognize() có thể được gọi
        hàng trăm/nghìn lần trong 1 lượt xử lý).
        """
        if self._traineddata_checked:
            return

        traineddata = TESSDATA_DIR / f"{OCR.LANG}.traineddata"
        if not traineddata.exists():
            raise FileNotFoundError(
                f"Không tìm thấy '{traineddata}'. Tải file tại "
                f"https://github.com/tesseract-ocr/tessdata_best/raw/main/{OCR.LANG}.traineddata "
                f"và đặt vào '{TESSDATA_DIR}'."
            )

        self._traineddata_checked = True

    def recognize(
        self,
        page_image: PageImage,
    ) -> tuple[tuple[float, float, float, float, str, float], ...]:
        """Return raw OCR words as (x0, y0, x1, y1, text, confidence).

        Coordinates are pixel-space of ``page_image`` (top-left origin,
        y-down), matching ``page_image.width`` / ``page_image.height`` -
        không đổi kể cả sau khi deskew nội bộ (canvas cố định).

        Raises
        ------
        FileNotFoundError
            Nếu thiếu vie.traineddata (kiểm tra lazy, xem
            _ensure_traineddata()) - chỉ raise khi hàm này thực sự được
            gọi lần đầu, không phải lúc __init__().
        """
        self._ensure_traineddata()

        image = self._to_numpy_array(page_image)
        image = self._deskew(image)
        image = self._preprocess(image)

        pil_image = Image.fromarray(image)
        data = pytesseract.image_to_data(
            pil_image,
            lang=OCR.LANG,
            config=self._config,
            output_type=pytesseract.Output.DICT,
        )

        words: list[tuple[float, float, float, float, str, float]] = []
        for i in range(len(data["text"])):
            text = data["text"][i].strip()
            if not text:
                continue

            confidence = float(data["conf"][i])
            if confidence < 0:
                continue

            left, top = float(data["left"][i]), float(data["top"][i])
            width, height = float(data["width"][i]), float(data["height"][i])
            words.append((left, top, left + width, top + height, text, confidence / 100.0))

        return tuple(words)

    def recognize_numeric_roi(
            self,
            page_image: PageImage,
            normalized_bbox: tuple[float, float, float, float],
    ) -> str:
        """Re-OCR 1 vùng số (ROI) với cấu hình chuyên biệt (Pass 2, ADR mới).

        Nhận bbox chuẩn hóa [0.0, 1.0] (cùng hệ tọa độ WordToken.normalized_bbox),
        trả về text thô (chưa qua ValueConverter). Không dùng chung self._config
        (Pass 1) - Pass 2 cần whitelist + PSM riêng biệt cho dòng đơn.
        """
        self._ensure_traineddata()

        image = self._to_numpy_array(page_image)
        # MỚI - đồng bộ hệ tọa độ với recognize() (Pass 1),
        # nếu không, bbox tính trên ảnh đã xoay sẽ cắt sai
        # vị trí trên ảnh gốc chưa xoay khi trang bị nghiêng
        image = self._deskew(image)
        roi = self._crop_roi(image, normalized_bbox, page_image.width, page_image.height)
        roi = cv2.resize(
            roi, (0, 0),
            fx=OCR.ROI_UPSCALE_FACTOR, fy=OCR.ROI_UPSCALE_FACTOR,
            interpolation=cv2.INTER_CUBIC,
        )

        whitelist = OCR.ROI_CHAR_WHITELIST.get(OCR.LANG, OCR.ROI_CHAR_WHITELIST["vie"])
        config = (
            f'--tessdata-dir "{TESSDATA_DIR}" --psm 7 --oem 3 '
            f'-c tessedit_char_whitelist={whitelist} '
            '-c load_system_dawg=0 -c load_freq_dawg=0 -c load_punc_dawg=0'
        )

        text = pytesseract.image_to_string(Image.fromarray(roi), lang=OCR.LANG, config=config)
        return text.strip()

    @staticmethod
    @staticmethod
    def _crop_roi(
            image: np.ndarray,
            normalized_bbox: tuple[float, float, float, float],
            width: int,
            height: int,
    ) -> np.ndarray:
        """Cắt vùng ROI từ ảnh trang, padding tỉ lệ theo CHIỀU CAO bbox (đại
        diện cỡ chữ/font size) - không theo kích thước trang. Tránh 2 rủi ro
        đối lập: tràn sang token/cột liền kề khi token ngắn (VD "10%"), và
        cắt mất mép ký tự khi padding quá chật - cả 2 đều gây OCR sai dấu
        phân cách (xem thực nghiệm thật trên PDF high_noise)."""
        x0, y0, x1, y1 = normalized_bbox
        bbox_height_px = (y1 - y0) * height
        pad_px = max(1, int(bbox_height_px * OCR.ROI_PADDING_RATIO))

        px0 = max(0, int(x0 * width) - pad_px)
        px1 = min(width, int(x1 * width) + pad_px)
        py0 = max(0, int(y0 * height) - pad_px)
        py1 = min(height, int(y1 * height) + pad_px)
        return image[py0:py1, px0:px1]

    @staticmethod
    def _to_numpy_array(page_image: PageImage) -> np.ndarray:
        """Dựng mảng NumPy (H, W, channels) từ raw pixmap bytes (RGB).

        page_image.channels tự mô tả số kênh (xem PageImage, core/models.py)
        - không giả định ngầm 1 hay 3 kênh (DP-008, Explicit Over Implicit).
        """
        array = np.frombuffer(page_image.samples, dtype=np.uint8)
        return array.reshape(page_image.height, page_image.width, page_image.channels)

    @staticmethod
    def _deskew(image: np.ndarray) -> np.ndarray:
        """Làm thẳng trang bị nghiêng nhẹ, giữ nguyên kích thước canvas gốc.

        Chỉ xử lý nghiêng vài độ (skew do đặt giấy lệch khi scan) - KHÔNG
        xử lý lật ngược 0/180 độ (việc đó do dữ liệu osd.traineddata của
        Tesseract đảm nhiệm ngầm trong PSM=3, độc lập với bước này).
        """
        angle = OCREngine._estimate_skew_angle(image)
        if abs(angle) < OCR.DESKEW_MIN_ANGLE:
            return image

        height, width = image.shape[:2]
        center = (width / 2, height / 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)

        channels = image.shape[2] if image.ndim == 3 else 1
        border_value = (
            (OCR.DESKEW_FILL_VALUE,) * channels if channels > 1 else OCR.DESKEW_FILL_VALUE
        )

        return cv2.warpAffine(
            image,
            rotation_matrix,
            (width, height),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=border_value,
        )

    @staticmethod
    def _preprocess(image: np.ndarray) -> np.ndarray:
        """Tăng contrast + sharpen trước OCR để cải thiện nhận dạng ký tự nhỏ."""
        # Chuyển sang grayscale nếu chưa phải
        gray = (
            cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            if image.ndim == 3
            else image
        )
        # Tăng contrast cục bộ (CLAHE — tốt hơn equalizeHist toàn cục
        # vì hoá đơn thường có vùng sáng/tối không đều)
        clahe = cv2.createCLAHE(clipLimit=OCR.PREPROCESS_CLAHE_CLIP_LIMIT,
                                tileGridSize=OCR.PREPROCESS_CLAHE_TILE_GRID_SIZE)
        enhanced = clahe.apply(gray)
        # Unsharp masking nhẹ để làm sắc nét cạnh ký tự
        blur = cv2.GaussianBlur(enhanced, (0, 0), sigmaX=OCR.PREPROCESS_SHARPEN_SIGMA)
        weight_original = 1.0 + OCR.PREPROCESS_SHARPEN_AMOUNT
        weight_blur = -OCR.PREPROCESS_SHARPEN_AMOUNT
        sharpened = cv2.addWeighted(enhanced, weight_original, blur, weight_blur, 0)
        # Trả về 3 kênh nếu input là RGB (để đồng nhất với downstream)
        if image.ndim == 3:
            return cv2.cvtColor(sharpened, cv2.COLOR_GRAY2RGB)
        return sharpened

    @staticmethod
    def _estimate_skew_angle(image: np.ndarray) -> float:
        """Ước lượng góc nghiêng (độ) của nội dung trên trang.

        Nhị phân hoá (Otsu) -> minAreaRect bao toàn bộ điểm nội dung ->
        góc nghiêng của hình chữ nhật nhỏ nhất đó. Trang trắng/không có
        nội dung -> trả 0.0 (không xoay).
        """
        gray = (
            cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if image.ndim == 3 else image
        )
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        coords = np.column_stack(np.where(binary > 0))
        if coords.size == 0:
            return 0.0

        angle = cv2.minAreaRect(coords)[-1]

        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        # CHỈ deskew nếu nghiêng nhẹ (dưới 10 độ).
        # Bỏ qua góc lớn do minAreaRect nhầm khung A4 đứng, tránh xoay ngang trang 90 độ!
        if abs(angle) > OCR.DESKEW_MAX_ANGLE:
            return 0.0
        return angle
