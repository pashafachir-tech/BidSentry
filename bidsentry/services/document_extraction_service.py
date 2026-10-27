"""Extract text from user supplied procurement documents without storing files."""

from __future__ import annotations

import io
import re
import zipfile
import zlib
from pathlib import PurePath
from typing import Any
from xml.etree import ElementTree

from bidsentry.types.schemas import ValidationError


MAX_DOCUMENT_BYTES = 8 * 1024 * 1024
MAX_EXPANDED_FILE_BYTES = 8 * 1024 * 1024
MAX_EXTRACTED_CHARACTERS = 1_000_000
MAX_PDF_PAGES = 500
SUPPORTED_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".docx", ".pdf"}


class DocumentExtractionService:
    def extract(self, filename: str, content: bytes) -> dict[str, Any]:
        safe_name = PurePath(str(filename or "")).name[:240]
        extension = PurePath(safe_name).suffix.casefold()
        if extension not in SUPPORTED_EXTENSIONS:
            allowed = ", ".join(sorted(SUPPORTED_EXTENSIONS))
            raise ValidationError(f"Format file belum didukung. Gunakan: {allowed}.", [{"field": "file", "issue": "unsupported_format"}])
        if not isinstance(content, bytes) or not content:
            raise ValidationError("File kosong atau tidak dapat dibaca.", [{"field": "file", "issue": "empty_file"}])
        if len(content) > MAX_DOCUMENT_BYTES:
            raise ValidationError("Ukuran file maksimum 8 MB.", [{"field": "file", "issue": "file_too_large"}])

        try:
            if extension == ".docx":
                text = self._docx(content)
            elif extension == ".pdf":
                text = self._pdf(content)
            else:
                text = self._plain_text(content, extension)
        except ValidationError:
            raise
        except Exception as exc:
            raise ValidationError("Isi file tidak dapat diekstrak. Pastikan file tidak rusak dan tidak diproteksi.", [{"field": "file", "issue": "extraction_failed"}]) from exc

        text = "\n".join(line.rstrip() for line in text.replace("\x00", "").splitlines()).strip()
        if not text:
            raise ValidationError("Tidak ada teks yang dapat dibaca. PDF hasil scan memerlukan OCR sebelum diunggah.", [{"field": "file", "issue": "no_extractable_text"}])
        if len(text) > MAX_EXTRACTED_CHARACTERS:
            raise ValidationError("Hasil ekstraksi melebihi 1.000.000 karakter per bagian. Pecah dokumen menjadi beberapa bagian sebelum mengunggah.", [{"field": "file", "issue": "text_too_long"}])
        return {"filename": safe_name, "text": text, "characters": len(text)}

    @staticmethod
    def _plain_text(content: bytes, extension: str) -> str:
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError:
            try:
                text = content.decode("cp1252")
            except UnicodeDecodeError:
                text = content.decode("latin-1")
        if extension == ".json":
            import json
            try:
                value = json.loads(text)
                return json.dumps(value, ensure_ascii=False, indent=2)
            except json.JSONDecodeError:
                return text
        return text

    @staticmethod
    def _docx(content: bytes) -> str:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            info = archive.getinfo("word/document.xml")
            if info.file_size > MAX_EXPANDED_FILE_BYTES:
                raise ValidationError("Isi dokumen DOCX setelah dibuka melebihi batas aman 8 MB.", [{"field": "file", "issue": "expanded_file_too_large"}])
            with archive.open(info) as stream:
                document = stream.read(MAX_EXPANDED_FILE_BYTES + 1)
            if len(document) > MAX_EXPANDED_FILE_BYTES:
                raise ValidationError("Isi dokumen DOCX setelah dibuka melebihi batas aman 8 MB.", [{"field": "file", "issue": "expanded_file_too_large"}])
        if b"<!DOCTYPE" in document.upper() or b"<!ENTITY" in document.upper():
            raise ValidationError("Deklarasi XML khusus tidak diizinkan pada DOCX.", [{"field": "file", "issue": "unsafe_xml_declaration"}])
        root = ElementTree.fromstring(document)
        ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
        paragraphs: list[str] = []
        for paragraph in root.iter(f"{ns}p"):
            parts: list[str] = []
            for node in paragraph.iter():
                if node.tag == f"{ns}t" and node.text:
                    parts.append(node.text)
                elif node.tag == f"{ns}tab":
                    parts.append("\t")
                elif node.tag in {f"{ns}br", f"{ns}cr"}:
                    parts.append("\n")
            value = "".join(parts).strip()
            if value:
                paragraphs.append(value)
        return "\n".join(paragraphs)

    @staticmethod
    def _pdf(content: bytes) -> str:
        # 1. Prioritize PyMuPDF (fast, robust C-based parser, handles modern/complex PDFs in milliseconds)
        try:
            import pymupdf
            doc = pymupdf.open(stream=content, filetype="pdf")
            if len(doc) > MAX_PDF_PAGES:
                raise ValidationError("PDF melebihi batas 500 halaman. Pecah dokumen menjadi beberapa bagian.", [{"field": "file", "issue": "too_many_pages"}])
            parts: list[str] = []
            character_count = 0
            for page in doc:
                page_text = page.get_text() or ""
                character_count += len(page_text)
                if character_count > MAX_EXTRACTED_CHARACTERS:
                    raise ValidationError("Hasil ekstraksi PDF melebihi 1.000.000 karakter. Pecah dokumen menjadi beberapa bagian.", [{"field": "file", "issue": "text_too_long"}])
                parts.append(page_text)
            text = "\n".join(parts).strip()
            if text:
                return text
        except ValidationError:
            raise
        except Exception:
            pass

        # 2. Try pypdf
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(content), strict=False)
            pages = reader.pages
            if len(pages) > MAX_PDF_PAGES:
                raise ValidationError("PDF melebihi batas 500 halaman. Pecah dokumen menjadi beberapa bagian.", [{"field": "file", "issue": "too_many_pages"}])
            parts = []
            character_count = 0
            for page in pages:
                page_text = page.extract_text() or ""
                character_count += len(page_text)
                if character_count > MAX_EXTRACTED_CHARACTERS:
                    raise ValidationError("Hasil ekstraksi PDF melebihi 1.000.000 karakter. Pecah dokumen menjadi beberapa bagian.", [{"field": "file", "issue": "text_too_long"}])
                parts.append(page_text)
            text = "\n".join(parts).strip()
            if text:
                return text
        except ValidationError:
            raise
        except Exception:
            pass

        # 3. Try pdfplumber
        try:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                if len(pdf.pages) > MAX_PDF_PAGES:
                    raise ValidationError("PDF melebihi batas 500 halaman. Pecah dokumen menjadi beberapa bagian.", [{"field": "file", "issue": "too_many_pages"}])
                parts = []
                character_count = 0
                for page in pdf.pages:
                    page_text = page.extract_text() or ""
                    character_count += len(page_text)
                    if character_count > MAX_EXTRACTED_CHARACTERS:
                        raise ValidationError("Hasil ekstraksi PDF melebihi 1.000.000 karakter. Pecah dokumen menjadi beberapa bagian.", [{"field": "file", "issue": "text_too_long"}])
                    parts.append(page_text)
                text = "\n".join(parts).strip()
                if text:
                    return text
        except ValidationError:
            raise
        except Exception:
            pass

        # 4. Fallback only if all modern libraries fail or are not available
        return DocumentExtractionService._pdf_basic(content)

    @staticmethod
    def _pdf_basic(content: bytes) -> str:
        """Best-effort extraction for uncomplicated PDFs when parsers are absent."""
        source = content.decode("latin-1", errors="ignore")
        streams: list[str] = []
        expanded_bytes = 0
        for match in re.finditer(r"stream\r?\n(.*?)\r?\nendstream", source, flags=re.DOTALL):
            raw = match.group(1).encode("latin-1", errors="ignore")
            decoded = raw
            for window in (zlib.MAX_WBITS, -zlib.MAX_WBITS):
                try:
                    inflater = zlib.decompressobj(window)
                    candidate = inflater.decompress(raw, MAX_EXPANDED_FILE_BYTES - expanded_bytes + 1)
                    if len(candidate) > MAX_EXPANDED_FILE_BYTES - expanded_bytes or inflater.unconsumed_tail:
                        raise ValidationError("PDF memuat data terkompresi yang melebihi batas aman 8 MB.", [{"field": "file", "issue": "expanded_file_too_large"}])
                    if inflater.eof:
                        decoded = candidate
                        break
                except zlib.error:
                    continue
            expanded_bytes += len(decoded)
            if expanded_bytes > MAX_EXPANDED_FILE_BYTES:
                raise ValidationError("PDF memuat data terkompresi yang melebihi batas aman 8 MB.", [{"field": "file", "issue": "expanded_file_too_large"}])
            streams.append(decoded.decode("latin-1", errors="ignore"))
            if len(streams) > 200:
                break
        text_source = "\n".join(streams) or source
        found: list[str] = []
        token = re.compile(r"\(((?:\\.|[^\\)])*)\)\s*Tj|\[([^\]]*?)\]\s*TJ")
        for item in token.finditer(text_source):
            value = item.group(1) if item.group(1) is not None else item.group(2)
            pieces = re.findall(r"\(((?:\\.|[^\\)])*)\)|<([0-9A-Fa-f]+)>", value)
            decoded_pieces: list[str] = []
            for literal, hexadecimal in pieces:
                if hexadecimal:
                    try:
                        decoded_pieces.append(bytes.fromhex(hexadecimal).decode("utf-16-be" if len(hexadecimal) % 4 == 0 else "latin-1", errors="ignore"))
                    except ValueError:
                        continue
                else:
                    literal = re.sub(r"\\([\\()])", r"\1", literal)
                    literal = re.sub(r"\\([0-7]{1,3})", lambda m: chr(int(m.group(1), 8)), literal)
                    decoded_pieces.append(literal.replace(r"\n", "\n").replace(r"\r", "\r").replace(r"\t", "\t"))
            if decoded_pieces:
                found.append("".join(decoded_pieces))
        return "\n".join(found)
