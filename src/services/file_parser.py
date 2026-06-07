from io import BytesIO

from fastapi import UploadFile
from pypdf import PdfReader
from docx import Document
from PIL import Image, ImageOps, ImageEnhance, ImageFilter
import pytesseract
from pdf2image import convert_from_bytes


TEXT_EXTENSIONS = (".txt", ".csv", ".md", ".json")
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg")


async def extract_text_from_file(file: UploadFile) -> str:
    content = await file.read()
    filename = (file.filename or "").lower()
    content_type = file.content_type or ""

    if filename.endswith(TEXT_EXTENSIONS):
        return content.decode("utf-8", errors="ignore").strip()

    if filename.endswith(".docx"):
        return extract_text_from_docx(content)

    if filename.endswith(".pdf") or content_type == "application/pdf":
        return extract_text_from_pdf(content)

    if filename.endswith(IMAGE_EXTENSIONS) or content_type.startswith("image/"):
        return extract_text_from_image(content)

    raise ValueError(f"Unsupported file type: {file.filename}")


def extract_text_from_docx(content: bytes) -> str:
    document = Document(BytesIO(content))
    return "\n".join(
        paragraph.text
        for paragraph in document.paragraphs
        if paragraph.text.strip()
    ).strip()


def extract_text_from_pdf(content: bytes) -> str:
    reader = PdfReader(BytesIO(content))
    text_parts = []

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text and page_text.strip():
            text_parts.append(page_text.strip())

    text = "\n".join(text_parts).strip()
    if text:
        return text

    images = convert_from_bytes(content)
    ocr_parts = []

    for image in images:
        page_text = ocr_image(image)
        if page_text:
            ocr_parts.append(page_text)

    return "\n".join(ocr_parts).strip()


def extract_text_from_image(content: bytes) -> str:
    image = Image.open(BytesIO(content))
    text = ocr_image(image)

    print(f"OCR RESULT LENGTH: {len(text)}")
    print(f"OCR RESULT: {repr(text)}")

    return text


def ocr_image(image: Image.Image) -> str:
    image = image.convert("RGB")

    # Convert to grayscale
    image = ImageOps.grayscale(image)

    # Enlarge tiny screenshot text
    scale = 5
    image = image.resize(
        (image.width * scale, image.height * scale),
        Image.Resampling.LANCZOS,
    )

    # Improve OCR readability
    image = ImageEnhance.Contrast(image).enhance(4)
    image = image.filter(ImageFilter.SHARPEN)

    # Convert to black/white for better screenshot OCR
    image = image.point(lambda p: 255 if p > 180 else 0)

    configs = [
        "--oem 3 --psm 6",
        "--oem 3 --psm 7",
        "--oem 3 --psm 11",
        "--oem 3 --psm 12",
        "--oem 3 --psm 3",
    ]

    best_text = ""

    for config in configs:
        try:
            text = pytesseract.image_to_string(
                image,
                config=config,
            ).strip()

            if len(text) > len(best_text):
                best_text = text

        except Exception as exc:
            print(f"OCR failed for config {config}: {exc}")

    return best_text.strip()
