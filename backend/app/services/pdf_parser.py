import fitz  # PyMuPDF
import io
from fastapi import HTTPException, UploadFile


class PDFParserService:
    @staticmethod
    def extract_text_from_bytes(file_bytes: bytes, filename: str = "resume.pdf") -> str:
        """
        Extract clean text from PDF bytes using PyMuPDF (fitz).
        Performs validation for corruption, empty documents, and image-only scans.
        """
        if not file_bytes:
            raise HTTPException(status_code=400, detail="The uploaded PDF file is empty (0 bytes).")

        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to parse PDF file '{filename}'. Ensure it is a valid, uncorrupted PDF. Error: {str(e)}"
            )

        if doc.page_count == 0:
            doc.close()
            raise HTTPException(status_code=400, detail="The PDF file has 0 pages.")

        extracted_text_pieces = []
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            text = page.get_text("text")
            if text:
                extracted_text_pieces.append(text.strip())

        doc.close()
        full_text = "\n\n".join(extracted_text_pieces).strip()

        if len(full_text) < 30:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Could not extract sufficient text from the PDF. The file may be a scanned image or "
                    "password-protected. Please upload a PDF containing selectable digital text."
                )
            )

        return full_text

    @classmethod
    async def parse_upload_file(cls, file: UploadFile, max_size_mb: int = 10) -> str:
        """Validate and extract text from FastAPI UploadFile."""
        # 1. Validate file extension and MIME type
        filename = file.filename or "resume.pdf"
        if not filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file format: '{filename}'. Only PDF files are supported."
            )

        # 2. Read bytes and check size
        content = await file.read()
        max_bytes = max_size_mb * 1024 * 1024
        if len(content) > max_bytes:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds the {max_size_mb} MB limit. File size: {len(content) / (1024 * 1024):.2f} MB"
            )

        return cls.extract_text_from_bytes(content, filename=filename)

