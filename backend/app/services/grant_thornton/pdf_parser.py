"""
Grant Thornton PDF Parser Module

Converts PDF annual reports to structured chunks with metadata for RAG retrieval.
Leverages existing Docling infrastructure while maintaining Grant Thornton spec.

Key Features:
- Page-by-page PDF processing
- Markdown conversion with header preservation
- Header-based chunking for context maintenance
- MD5 hash generation for caching
- Metadata enrichment (page numbers, header hierarchy)

Author: Claude Code
Date: 2026-01-01
"""

import hashlib
import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import PyPDF2
from langchain.schema import Document
from langchain.text_splitter import MarkdownHeaderTextSplitter

logger = logging.getLogger(__name__)


class PDFParser:
    """
    Grant Thornton PDF Parser

    Converts PDF annual reports into markdown chunks with header-based splitting.
    Reuses existing Docling infrastructure for PDF-to-markdown conversion.
    """

    def __init__(self, temp_dir: str = "/tmp/grant_thornton"):
        """
        Initialize PDF parser.

        Args:
            temp_dir: Directory for temporary file storage
        """
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        # Header tags for markdown splitting (per GT spec)
        self.header_tags = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]

    def calculate_md5(self, pdf_path: str) -> str:
        """
        Calculate MD5 hash of PDF file for caching.

        Args:
            pdf_path: Path to PDF file

        Returns:
            MD5 hash string
        """
        md5_hash = hashlib.md5()
        with open(pdf_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()

    async def parse_pdf(
        self,
        pdf_path: str,
        use_docling: bool = True
    ) -> Dict[str, Any]:
        """
        Parse PDF into structured chunks with metadata.

        Args:
            pdf_path: Path to PDF file
            use_docling: Whether to use Docling for conversion (default True)

        Returns:
            Dictionary containing:
                - md5_hash: Unique document identifier
                - chunks: List of Document objects with content and metadata
                - page_count: Total number of pages
                - split_pages: List of individual page data
        """
        logger.info(f"Parsing PDF: {pdf_path}")

        # Calculate MD5 for caching
        md5_hash = self.calculate_md5(pdf_path)
        logger.info(f"Document MD5: {md5_hash}")

        # Split PDF into pages
        split_pages = await self._split_pdf(pdf_path, md5_hash)
        page_count = len(split_pages)
        logger.info(f"Split into {page_count} pages")

        # Convert pages to markdown
        all_chunks = []
        for page_data in split_pages:
            if use_docling:
                chunks = await self._pdf_to_markdown_docling(page_data)
            else:
                chunks = await self._pdf_to_markdown_fallback(page_data)

            all_chunks.extend(chunks)

        logger.info(f"Generated {len(all_chunks)} chunks")

        return {
            "md5_hash": md5_hash,
            "chunks": all_chunks,
            "page_count": page_count,
            "split_pages": split_pages
        }

    async def _split_pdf(
        self,
        pdf_path: str,
        md5_hash: str
    ) -> List[Dict[str, Any]]:
        """
        Split PDF into individual pages with metadata.

        Args:
            pdf_path: Path to source PDF
            md5_hash: Document identifier

        Returns:
            List of page metadata dictionaries
        """
        split_pages = []
        split_dir = self.temp_dir / md5_hash
        split_dir.mkdir(exist_ok=True)

        try:
            with open(pdf_path, 'rb') as pdf_file:
                reader = PyPDF2.PdfReader(pdf_file)
                total_pages = len(reader.pages)

                for page_num in range(total_pages):
                    # Create single-page PDF
                    writer = PyPDF2.PdfWriter()
                    writer.add_page(reader.pages[page_num])

                    # Save page PDF
                    page_path = split_dir / f"page_{page_num + 1}.pdf"
                    with open(page_path, 'wb') as page_file:
                        writer.write(page_file)

                    # Create metadata
                    page_data = {
                        "path": str(pdf_path),
                        "page": page_num + 1,
                        "split_root": str(split_dir),
                        "page_path": str(page_path),
                        "EOF": str(page_num == total_pages - 1)
                    }
                    split_pages.append(page_data)

        except Exception as e:
            logger.error(f"Error splitting PDF: {e}", exc_info=True)
            raise

        return split_pages

    async def _pdf_to_markdown_docling(
        self,
        page_data: Dict[str, Any]
    ) -> List[Document]:
        """
        Convert PDF page to markdown using Docling.

        Args:
            page_data: Page metadata dictionary

        Returns:
            List of Document chunks with metadata
        """
        try:
            from docling.document_converter import DocumentConverter

            # Convert page to markdown
            converter = DocumentConverter()
            result = converter.convert(page_data["page_path"])

            # Extract markdown content
            if hasattr(result, 'document') and hasattr(result.document, 'export_to_markdown'):
                markdown_content = result.document.export_to_markdown()
            else:
                # Fallback: Extract text and format as markdown
                markdown_content = self._format_as_markdown(result)

            # Split by headers
            chunks = self._split_by_headers(
                markdown_content,
                page_data
            )

            return chunks

        except ImportError:
            logger.warning("Docling not available, using fallback")
            return await self._pdf_to_markdown_fallback(page_data)

        except Exception as e:
            logger.error(f"Error in Docling conversion: {e}", exc_info=True)
            return await self._pdf_to_markdown_fallback(page_data)

    async def _pdf_to_markdown_fallback(
        self,
        page_data: Dict[str, Any]
    ) -> List[Document]:
        """
        Fallback PDF to markdown using PyPDF2.

        Args:
            page_data: Page metadata dictionary

        Returns:
            List of Document chunks
        """
        try:
            with open(page_data["page_path"], 'rb') as pdf_file:
                reader = PyPDF2.PdfReader(pdf_file)

                if len(reader.pages) > 0:
                    text = reader.pages[0].extract_text()

                    # Simple markdown formatting
                    markdown_content = self._text_to_markdown(text)

                    # Split by headers
                    chunks = self._split_by_headers(
                        markdown_content,
                        page_data
                    )

                    return chunks
                else:
                    return []

        except Exception as e:
            logger.error(f"Error in fallback conversion: {e}")
            return []

    def _format_as_markdown(self, docling_result: Any) -> str:
        """
        Format Docling result as markdown.

        Args:
            docling_result: Docling conversion result

        Returns:
            Markdown-formatted string
        """
        # Extract text from Docling result
        if hasattr(docling_result, 'document'):
            if hasattr(docling_result.document, 'text'):
                return docling_result.document.text
            elif hasattr(docling_result.document, 'content'):
                return str(docling_result.document.content)

        # Fallback
        return str(docling_result)

    def _text_to_markdown(self, text: str) -> str:
        """
        Convert plain text to simple markdown with header detection.

        Args:
            text: Plain text content

        Returns:
            Markdown-formatted text
        """
        lines = text.split('\n')
        markdown_lines = []

        for line in lines:
            stripped = line.strip()

            # Detect headers (all caps lines or numbered sections)
            if stripped and (stripped.isupper() or
                           (len(stripped) > 0 and stripped[0].isdigit() and '.' in stripped[:5])):
                # Convert to header
                markdown_lines.append(f"## {stripped}")
            else:
                markdown_lines.append(line)

        return '\n'.join(markdown_lines)

    def _split_by_headers(
        self,
        markdown_content: str,
        page_data: Dict[str, Any]
    ) -> List[Document]:
        """
        Split markdown content by headers and create Document chunks.

        Args:
            markdown_content: Markdown text
            page_data: Page metadata

        Returns:
            List of Document objects with metadata
        """
        # Use LangChain's MarkdownHeaderTextSplitter
        splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=self.header_tags
        )

        try:
            splits = splitter.split_text(markdown_content)

            # Enrich with metadata
            chunks = []
            for idx, split in enumerate(splits):
                # Extract header hierarchy from metadata
                header_metadata = split.metadata if hasattr(split, 'metadata') else {}

                # Create comprehensive metadata
                metadata = {
                    "path": page_data["path"],
                    "page": page_data["page"],
                    "chunk": idx + 1,
                    "EOF": page_data["EOF"],
                    "header": header_metadata,
                    "source": f"page_{page_data['page']}_chunk_{idx + 1}"
                }

                # Create Document
                doc = Document(
                    page_content=split.page_content if hasattr(split, 'page_content') else str(split),
                    metadata=metadata
                )
                chunks.append(doc)

            # If no splits (no headers), create single chunk
            if not chunks:
                doc = Document(
                    page_content=markdown_content,
                    metadata={
                        "path": page_data["path"],
                        "page": page_data["page"],
                        "chunk": 1,
                        "EOF": page_data["EOF"],
                        "header": {},
                        "source": f"page_{page_data['page']}_chunk_1"
                    }
                )
                chunks.append(doc)

            return chunks

        except Exception as e:
            logger.error(f"Error splitting by headers: {e}")

            # Fallback: Create single chunk
            doc = Document(
                page_content=markdown_content,
                metadata={
                    "path": page_data["path"],
                    "page": page_data["page"],
                    "chunk": 1,
                    "EOF": page_data["EOF"],
                    "header": {},
                    "source": f"page_{page_data['page']}_chunk_1"
                }
            )
            return [doc]


async def parse_financial_report(pdf_path: str) -> Dict[str, Any]:
    """
    Convenience function to parse financial PDF report.

    Args:
        pdf_path: Path to PDF file

    Returns:
        Parsed document data with chunks and metadata
    """
    parser = PDFParser()
    return await parser.parse_pdf(pdf_path)
