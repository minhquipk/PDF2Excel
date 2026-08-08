"""OCR engine thật, dùng RapidOCR (ONNX Runtime backend, không phụ thuộc
paddlepaddle).

Thay thế Mock (ADR-013: Mock First -> Replace Mock). Giữ nguyên contract
đã có với Extractor (ADR-024/025): nhận PageImage, trả về raw, chưa
normalize - Extractor vẫn là nơi duy nhất chuẩn hoá hình học.
"""

from __future__ import annotations
import cv2
import numpy as np
from rapidocr import RapidOCR as _RapidOCR
from core.constants import OCR
from core.models import PageImage


class OCREngine:
    """Nhận dạng chữ trên page_image đã render (RapidOCR PP-OCRv6 pipeline).

    Symmetric với PDFReader: trả về raw, un-normalized output. Toàn bộ
    chuẩn hoá toạ độ vẫn là trách nhiệm duy nhất của Extractor.

    Deskew (làm thẳng trang trước khi detect) được thực hiện NỘI BỘ tại
    đây, không lộ ra ngoài contract recognize() - Extractor không cần
    biết trang có bị nghiêng hay không, chỉ nhận bbox đã đúng vị trí
    trên page_image gốc (canvas giữ nguyên kích thước sau deskew).
    """

    def __init__(self) -> None:
        # Khởi tạo model 1 lần duy nhất - tái sử dụng cho toàn bộ batch
        # (đối xứng cách Extractor.__init__ tạo OCREngine() một lần).
        self._ocr = _RapidOCR(
            params={
                "Det.model_type": OCR.MODEL_TYPE,
                "Rec.lang_type": OCR.REC_LANG,
                "Rec.model_type": OCR.MODEL_TYPE,
            }
        )

    def recognize(
        self,
        page_image: PageImage,
    ) -> tuple[tuple[float, float, float, float, str, float], ...]:
        """Return raw OCR words as (x0, y0, x1, y1, text, confidence).

        Coordinates are pixel-space of ``page_image`` (top-left origin,
        y-down), matching ``page_image.width`` / ``page_image.height`` -
        không đổi kể cả sau khi deskew nội bộ (canvas cố định).
        """
        image = self._to_numpy_array(page_image)
        image = self._to_bgr(image)
        image = self._deskew(image)

        result = self._ocr(image, use_cls=OCR.USE_CLS)
        if result is None or result.boxes is None or len(result.boxes) == 0:
            return ()

        words: list[tuple[float, float, float, float, str, float]] = []
        for quad, text, score in zip(result.boxes, result.txts, result.scores):
            xs = quad[:, 0]
            ys = quad[:, 1]
            x0, y0, x1, y1 = float(xs.min()), float(ys.min()), float(xs.max()), float(ys.max())
            words.append((x0, y0, x1, y1, text, float(score)))

        return tuple(words)

    @staticmethod
    def _to_numpy_array(page_image: PageImage) -> np.ndarray:
        """Dựng mảng NumPy (H, W, channels) từ raw pixmap bytes (RGB).

        page_image.channels tự mô tả số kênh (xem PageImage, core/models.py)
        - không giả định ngầm 1 hay 3 kênh (DP-008, Explicit Over Implicit).
        """
        array = np.frombuffer(page_image.samples, dtype=np.uint8)
        return array.reshape(page_image.height, page_image.width, page_image.channels)

    @staticmethod
    def _to_bgr(image: np.ndarray) -> np.ndarray:
        """Đổi RGB (nguồn PageImage) sang BGR.

        RapidOCR chỉ tự convert RGB->BGR khi nhận str/Path/bytes/PIL.Image
        (đọc qua Pillow); với numpy.ndarray truyền thẳng, nó GIẢ ĐỊNH mảng
        đã là BGR và không convert gì (xem rapidocr/utils/load_image.py::
        LoadImage.convert_img()). Không tự bù bước này sẽ khiến kênh Đỏ/
        Xanh dương bị hoán đổi ngầm bên trong RapidOCR - đi ngược lý do
        PageImage giữ RGB (bảo toàn màu thật: con dấu đỏ, chữ ký mực màu).
        """
        if image.ndim != 3 or image.shape[2] != 3:
            return image
        return cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    @staticmethod
    def _deskew(image: np.ndarray) -> np.ndarray:
        """Làm thẳng trang bị nghiêng nhẹ, giữ nguyên kích thước canvas gốc.

        Chỉ xử lý nghiêng vài độ (skew do đặt giấy lệch khi scan) - KHÔNG
        xử lý lật ngược 0/180 độ (việc đó do use_cls của RapidOCR đảm
        nhiệm, độc lập với bước này). image ở đây đã là BGR (sau _to_bgr).
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
    def _estimate_skew_angle(image: np.ndarray) -> float:
        """Ước lượng góc nghiêng (độ) của nội dung trên trang.

        Nhị phân hoá (Otsu) -> minAreaRect bao toàn bộ điểm nội dung ->
        góc nghiêng của hình chữ nhật nhỏ nhất đó. Trang trắng/không có
        nội dung -> trả 0.0 (không xoay).
        """
        gray = (
            cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
        )
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        coords = np.column_stack(np.where(binary > 0))
        if coords.size == 0:
            return 0.0

        angle = cv2.minAreaRect(coords)[-1]

        if angle < -45:
            return -(90 + angle)
        return -angle
