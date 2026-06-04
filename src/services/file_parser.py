from io import BytesIO

from fastapi import UploadFile
from pypdf import PdfReader
from docx import Document
from PIL import Image
import pytesseract
from pdf2image import convert_from_bytes


TEXT_EXTENSIONS = (".txt", ".csv", ".md", ".json")
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg")


async def extract_text_from_file(file: UploadFile) -> str:
    content = await file.read()
    filename = (file.filename or "").lower()
    content_type = file.content_type or ""

    if filename.endswith(TEXT_EXTENSIONS):
        return content.decode("utf-8", errors="ignore")

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
    )


def extract_text_from_pdf(content: bytes) -> str:
    reader = PdfReader(BytesIO(content))

    text_parts = []

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text_parts.append(page_text)

    text = "\n".join(text_parts).strip()

    if text:
        return text

    images = convert_from_bytes(content)

    ocr_parts = []

    for image in images:
        page_text = pytesseract.image_to_string(image)
        if page_text.strip():
            ocr_parts.append(page_text)

    return "\n".join(ocr_parts)


def extract_text_from_image(content: bytes) -> str:
    image = Image.open(BytesIO(content))
    return pytesseract.image_to_string(image)
