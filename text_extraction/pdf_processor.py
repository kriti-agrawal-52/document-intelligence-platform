"""
PDF Processing Module for Document Intelligence Platform

This module handles PDF file processing including:
- Converting PDF pages to images
- Extracting text from each page using OpenAI Vision API
- Concatenating extracted text from all pages
- Handling PDF metadata extraction
"""

import io
import base64
import tempfile
import os
from typing import List, Tuple, Optional
from pdf2image import convert_from_bytes
from PIL import Image
import PyPDF2
import openai
from shared.config import get_config

config = get_config()


class PDFProcessor:
    """Handles PDF processing operations."""
    
    def __init__(self, openai_client):
        """Initialize PDF processor with OpenAI client."""
        self.openai_client = openai_client
        self.config = config
    
    def extract_pdf_metadata(self, pdf_bytes: bytes) -> dict:
        """Extract metadata from PDF file."""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
            metadata = {
                "num_pages": len(pdf_reader.pages),
                "title": pdf_reader.metadata.get("/Title", "") if pdf_reader.metadata else "",
                "author": pdf_reader.metadata.get("/Author", "") if pdf_reader.metadata else "",
                "creator": pdf_reader.metadata.get("/Creator", "") if pdf_reader.metadata else "",
                "producer": pdf_reader.metadata.get("/Producer", "") if pdf_reader.metadata else "",
                "creation_date": str(pdf_reader.metadata.get("/CreationDate", "")) if pdf_reader.metadata else "",
            }
            return metadata
        except Exception as e:
            print(f"Error extracting PDF metadata: {e}")
            return {"num_pages": 0, "error": str(e)}
    
    def convert_pdf_to_images(self, pdf_bytes: bytes, dpi: int = 200) -> List[Image.Image]:
        """
        Convert PDF pages to PIL Images.
        
        Args:
            pdf_bytes: PDF file content as bytes
            dpi: Resolution for image conversion (default: 200)
            
        Returns:
            List of PIL Image objects, one per page
        """
        try:
            # Convert PDF to images using pdf2image
            images = convert_from_bytes(
                pdf_bytes,
                dpi=dpi,
                fmt='PNG',
                thread_count=1  # Keep it single-threaded for consistency
            )
            print(f"Successfully converted PDF to {len(images)} images")
            return images
        except Exception as e:
            print(f"Error converting PDF to images: {e}")
            raise Exception(f"Failed to convert PDF to images: {str(e)}")
    
    def image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 string for OpenAI API."""
        try:
            # Convert image to bytes
            img_buffer = io.BytesIO()
            image.save(img_buffer, format='PNG')
            img_bytes = img_buffer.getvalue()
            
            # Encode to base64
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            return img_base64
        except Exception as e:
            print(f"Error converting image to base64: {e}")
            raise Exception(f"Failed to convert image to base64: {str(e)}")
    
    async def extract_text_from_image(self, image: Image.Image, page_number: int) -> str:
        """
        Extract text from a single page image using OpenAI Vision API.
        
        Args:
            image: PIL Image object
            page_number: Page number for logging purposes
            
        Returns:
            Extracted text from the image
        """
        try:
            # Convert image to base64
            img_base64 = self.image_to_base64(image)
            
            print(f"Extracting text from page {page_number}...")
            
            # Call OpenAI Vision API
            response = self.openai_client.chat.completions.create(
                model=self.config.openai.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"{self.config.openai.prompt_for_text_extraction} This is page {page_number} of a PDF document."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{img_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=self.config.openai.max_tokens,
                temperature=self.config.openai.temperature
            )
            
            extracted_text = response.choices[0].message.content
            print(f"Successfully extracted text from page {page_number}: {len(extracted_text)} characters")
            
            return extracted_text
            
        except Exception as e:
            print(f"Error extracting text from page {page_number}: {e}")
            return f"[Error extracting text from page {page_number}: {str(e)}]"
    
    async def process_pdf(self, pdf_bytes: bytes, document_name: str) -> Tuple[str, dict, int]:
        """
        Complete PDF processing workflow.
        
        Args:
            pdf_bytes: PDF file content as bytes
            document_name: Name of the document for logging
            
        Returns:
            Tuple of (concatenated_text, pdf_metadata, num_pages)
        """
        try:
            print(f"Starting PDF processing for: {document_name}")
            
            # Step 1: Extract PDF metadata
            pdf_metadata = self.extract_pdf_metadata(pdf_bytes)
            num_pages = pdf_metadata.get("num_pages", 0)
            
            if num_pages == 0:
                raise Exception("PDF has no pages or is corrupted")
            
            print(f"PDF has {num_pages} pages")
            
            # Step 2: Convert PDF to images
            images = self.convert_pdf_to_images(pdf_bytes)
            
            if len(images) != num_pages:
                print(f"Warning: Expected {num_pages} pages, got {len(images)} images")
            
            # Step 3: Extract text from each page
            extracted_texts = []
            for i, image in enumerate(images, 1):
                page_text = await self.extract_text_from_image(image, i)
                extracted_texts.append(f"--- Page {i} ---\n{page_text}\n")
            
            # Step 4: Concatenate all extracted text
            concatenated_text = "\n".join(extracted_texts)
            
            print(f"Successfully processed PDF: {len(concatenated_text)} total characters extracted")
            
            return concatenated_text, pdf_metadata, len(images)
            
        except Exception as e:
            print(f"Error processing PDF {document_name}: {e}")
            raise Exception(f"Failed to process PDF: {str(e)}")
    
    def validate_pdf(self, pdf_bytes: bytes) -> bool:
        """
        Validate if the uploaded file is a valid PDF.
        
        Args:
            pdf_bytes: File content as bytes
            
        Returns:
            True if valid PDF, False otherwise
        """
        try:
            # Try to read the PDF
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
            
            # Check if it has at least one page
            if len(pdf_reader.pages) == 0:
                return False
                
            # Try to access the first page (basic validation)
            first_page = pdf_reader.pages[0]
            
            return True
        except Exception as e:
            print(f"PDF validation failed: {e}")
            return False
    
    def get_pdf_size_info(self, pdf_bytes: bytes) -> dict:
        """Get PDF file size information for validation."""
        try:
            size_mb = len(pdf_bytes) / (1024 * 1024)
            metadata = self.extract_pdf_metadata(pdf_bytes)
            
            return {
                "size_bytes": len(pdf_bytes),
                "size_mb": round(size_mb, 2),
                "num_pages": metadata.get("num_pages", 0),
                "estimated_processing_time": metadata.get("num_pages", 0) * 10  # ~10 seconds per page
            }
        except Exception as e:
            print(f"Error getting PDF size info: {e}")
            return {"error": str(e)}


def create_pdf_processor(openai_client) -> PDFProcessor:
    """Factory function to create PDFProcessor instance."""
    return PDFProcessor(openai_client)
