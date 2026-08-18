import io
import os
import logging
from typing import Tuple, Dict, Any, List

logger = logging.getLogger(__name__)

class DocumentExtractionService:
    """
    Extracts text and line-level metadata from uploaded candidate documents (PDF, DOCX, TXT).
    """

    @staticmethod
    def extract_from_bytes(file_bytes: bytes, filename: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Returns (clean_full_text, line_segments_with_metadata)
        """
        ext = os.path.splitext(filename)[1].lower()
        full_text = ""
        lines: List[Dict[str, Any]] = []

        try:
            if ext == ".pdf":
                full_text = DocumentExtractionService._extract_pdf(file_bytes)
            elif ext in [".docx", ".doc"]:
                full_text = DocumentExtractionService._extract_docx(file_bytes)
            elif ext in [".txt", ".md", ".csv"]:
                full_text = file_bytes.decode("utf-8", errors="ignore")
            else:
                full_text = file_bytes.decode("utf-8", errors="ignore")
        except Exception as e:
            logger.error(f"Error parsing document {filename}: {e}")
            full_text = file_bytes.decode("utf-8", errors="ignore")

        # Clean and construct line-level citations
        raw_lines = [l.strip() for l in full_text.split("\n") if l.strip()]
        for idx, line in enumerate(raw_lines):
            lines.append({
                "line_number": idx + 1,
                "text": line
            })

        return full_text, lines

    @staticmethod
    def _extract_pdf(file_bytes: bytes) -> str:
        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
            text_parts = []
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            return "\n".join(text_parts)
        except Exception as e:
            logger.warning(f"PyPDF2 failed: {e}")
            return file_bytes.decode("utf-8", errors="ignore")

    @staticmethod
    def _extract_docx(file_bytes: bytes) -> str:
        try:
            import docx
            doc = docx.Document(io.BytesIO(file_bytes))
            text_parts = [para.text for para in doc.paragraphs if para.text.strip()]
            return "\n".join(text_parts)
        except Exception:
            try:
                import docx2txt
                return docx2txt.process(io.BytesIO(file_bytes))
            except Exception as e:
                logger.warning(f"Docx extraction failed: {e}")
                return file_bytes.decode("utf-8", errors="ignore")

extraction_service = DocumentExtractionService()
