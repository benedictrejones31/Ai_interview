import pytest
import io
import fitz
from fastapi import HTTPException
from app.services.pdf_parser import PDFParserService


def create_sample_pdf_bytes(text: str = "Candidate Name: Alex Johnson\nSoftware Engineer with 4 years experience.") -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_extract_text_from_valid_pdf():
    sample_text = "John Doe - Senior Python & React Developer\nExperience: 5 years at TechCorp."
    pdf_bytes = create_sample_pdf_bytes(sample_text)
    extracted = PDFParserService.extract_text_from_bytes(pdf_bytes, "resume.pdf")
    assert "John Doe" in extracted
    assert "TechCorp" in extracted


def test_extract_text_empty_bytes():
    with pytest.raises(HTTPException) as excinfo:
        PDFParserService.extract_text_from_bytes(b"", "empty.pdf")
    assert excinfo.value.status_code == 400
    assert "empty" in excinfo.value.detail.lower()


def test_extract_text_insufficient_content():
    # Only 5 characters - should trigger insufficient text error
    pdf_bytes = create_sample_pdf_bytes("Hi")
    with pytest.raises(HTTPException) as excinfo:
        PDFParserService.extract_text_from_bytes(pdf_bytes, "tiny.pdf")
    assert excinfo.value.status_code == 400
    assert "sufficient" in excinfo.value.detail.lower()

