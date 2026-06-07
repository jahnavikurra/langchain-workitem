from io import BytesIO
import logging

from fastapi import UploadFile
from pypdf import PdfReader
from docx import Document
from PIL import Image, ImageOps, ImageEnhance, ImageFilter
import pytesseract
from pdf2image import convert_from_bytes

logger = logging.getLogger(__name__)

TEXT_EXTENSIONS = (".txt", ".csv", ".md", ".json")
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg")


async def extract_text_from_file(file: UploadFile) -> str:
    content = await file.read()
    filename = (file.filename or "").lower()
    content_type = file.content_type or ""

    logger.info(f"Uploaded file: {filename}")
    logger.info(f"Content type: {content_type}")
    logger.info(f"File size: {len(content)} bytes")

    if filename.endswith(TEXT_EXTENSIONS):
        text = content.decode("utf-8", errors="ignore").strip()
        logger.info(f"Text file extracted length: {len(text)}")
        return text

    if filename.endswith(".docx"):
        return extract_text_from_docx(content)

    if filename.endswith(".pdf") or content_type == "application/pdf":
        return extract_text_from_pdf(content)

    if filename.endswith(IMAGE_EXTENSIONS) or content_type.startswith("image/"):
        return extract_text_from_image(content)

    raise ValueError(f"Unsupported file type: {file.filename}")


def extract_text_from_docx(content: bytes) -> str:
    document = Document(BytesIO(content))
    text = "\n".join(
        paragraph.text
        for paragraph in document.paragraphs
        if paragraph.text.strip()
    ).strip()

    logger.info(f"DOCX extracted length: {len(text)}")
    return text


def extract_text_from_pdf(content: bytes) -> str:
    reader = PdfReader(BytesIO(content))
    text_parts = []

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text and page_text.strip():
            text_parts.append(page_text.strip())

    text = "\n".join(text_parts).strip()

    if text:
        logger.info(f"PDF text extracted length: {len(text)}")
        return text

    logger.info("PDF has no selectable text. Running OCR on PDF pages.")

    images = convert_from_bytes(content)
    ocr_parts = []

    for index, image in enumerate(images):
        logger.info(f"Running OCR on PDF page {index + 1}")
        page_text = ocr_image(image)

        if page_text:
            ocr_parts.append(page_text)

    final_text = "\n".join(ocr_parts).strip()
    logger.info(f"PDF OCR extracted length: {len(final_text)}")

    return final_text


def extract_text_from_image(content: bytes) -> str:
    image = Image.open(BytesIO(content))

    logger.info(f"Image format: {image.format}")
    logger.info(f"Image mode: {image.mode}")

    text = ocr_image(image)

    logger.info(f"Final OCR text length: {len(text)}")
    logger.info(f"Final OCR text preview: {repr(text[:500])}")

    return text.strip()


def crop_to_text_area(image: Image.Image) -> Image.Image:
    """
    Crops large blank screenshot areas.
    This helps when the uploaded PNG has tiny text inside a large canvas.
    """
    gray = ImageOps.grayscale(image)
    gray = ImageOps.autocontrast(gray)

    mask = gray.point(lambda p: 255 if p < 245 else 0)
    bbox = mask.getbbox()

    if not bbox:
        logger.warning("No text bounding box detected. Using full image.")
        return image

    left, top, right, bottom = bbox
    padding = 50

    left = max(left - padding, 0)
    top = max(top - padding, 0)
    right = min(right + padding, image.width)
    bottom = min(bottom + padding, image.height)

    cropped = image.crop((left, top, right, bottom))

    logger.info(
        f"Cropped image from {image.width}x{image.height} "
        f"to {cropped.width}x{cropped.height}"
    )

    return cropped


def preprocess_for_ocr(image: Image.Image) -> Image.Image:
    image = image.convert("RGB")

    image = crop_to_text_area(image)

    image = ImageOps.grayscale(image)

    scale = 5
    image = image.resize(
        (image.width * scale, image.height * scale),
        Image.Resampling.LANCZOS,
    )

    image = ImageOps.autocontrast(image)
    image = ImageEnhance.Contrast(image).enhance(3.0)
    image = ImageEnhance.Sharpness(image).enhance(2.0)
    image = image.filter(ImageFilter.SHARPEN)

    logger.info(f"Processed OCR image size: {image.width}x{image.height}")

    return image


def ocr_image(image: Image.Image) -> str:
    logger.info(f"Original image size: {image.width}x{image.height}")

    processed_image = preprocess_for_ocr(image)

    configs = [
        "--oem 3 --psm 7",   # single line text
        "--oem 3 --psm 6",   # block of text
        "--oem 3 --psm 11",  # sparse text
        "--oem 3 --psm 3",   # automatic page segmentation
    ]

    best_text = ""

    for config in configs:
        try:
            text = pytesseract.image_to_string(
                processed_image,
                config=config,
            ).strip()

            logger.info(
                f"OCR config [{config}] returned "
                f"{len(text)} chars: {repr(text[:200])}"
            )

            if len(text) > len(best_text):
                best_text = text

        except Exception as exc:
            logger.exception(f"OCR failed for config {config}: {exc}")

    logger.info(f"BEST OCR RESULT LENGTH: {len(best_text)}")
    logger.info(f"BEST OCR RESULT PREVIEW: {repr(best_text[:500])}")

    return best_text.strip()
