"""
PDF parsing module for MASTERFORMAT documents - FINAL WORKING VERSION.
"""

import fitz  # PyMuPDF
import pdfplumber
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from utils import DataProcessor, ErrorHandler
from constants import DIVISION_CODES, DIVISION_MAPPING, DATA_TYPES

logger = logging.getLogger(__name__)

class PDFParser:
    """PDF parser for MASTERFORMAT City Cost Indexes documents."""
    
    def __init__(self, use_pdfplumber: bool = True, use_pymupdf: bool = True):
        self.use_pdfplumber = use_pdfplumber
        self.use_pymupdf = use_pymupdf
        self.error_handler = ErrorHandler()
        self.data_processor = DataProcessor()
        
        # Patterns for 2023 format - FIXED
        self.city_inst_pattern = re.compile(r'^([A-Z\s&\.\-]+?)\s+(\d{3}(?:\s*-\s*\d{3})?(?:\s*,\s*\d{3})*)\s+INST\.\s+([\d\.\s]+)$')
        self.total_pattern = re.compile(r'^TOTAL\s+([\d\.\s]+)$')
        self.number_pattern = re.compile(r'\d+\.\d+')
    
    def parse_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Parse the entire PDF and extract all city cost index data."""
        logger.info(f"Starting PDF parsing: {pdf_path}")
        
        all_data = {}
        
        try:
            # Use PyMuPDF as primary method
            doc = fitz.open(pdf_path)
            
            for page_num in range(doc.page_count):
                logger.debug(f"Processing page {page_num + 1}")
                
                page = doc[page_num]
                text = page.get_text()
                
                if not text:
                    continue
                
                page_data = self._process_page_text_simple(text)
                all_data.update(page_data)
                
                if page_data:
                    logger.info(f"Page {page_num + 1}: Found {len(page_data)} cities")
            
            doc.close()
                
        except Exception as e:
            self.error_handler.add_error(f"Failed to parse PDF: {str(e)}", {"pdf_path": pdf_path})
            raise
        
        logger.info(f"Parsing completed. Found {len(all_data)} cities.")
        return all_data
    
    def _process_page_text_simple(self, text: str) -> Dict[str, Any]:
        """Process text from a page - simplified approach."""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        page_data = {}
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Skip header/division lines
            if self._is_header_line(line):
                i += 1
                continue
            
            # Look for city INST. pattern
            city_match = self.city_inst_pattern.match(line)
            if city_match:
                city_name = city_match.group(1).strip()
                zip_codes = city_match.group(2).strip()
                inst_numbers_str = city_match.group(3)
                
                logger.debug(f"Found city: {city_name} {zip_codes}")
                
                # Extract INST numbers
                inst_numbers = self._extract_numbers_from_text(inst_numbers_str)
                
                # Look for TOTAL line on next line
                total_numbers = []
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    total_match = self.total_pattern.match(next_line)
                    if total_match:
                        total_numbers_str = total_match.group(1)
                        total_numbers = self._extract_numbers_from_text(total_numbers_str)
                        i += 1  # Skip the TOTAL line
                
                # Build city data if we have valid numbers
                if inst_numbers and len(inst_numbers) >= 15:  # Reasonable threshold
                    city_key = self._create_city_key(city_name, zip_codes)
                    city_data = self._build_city_data_simple(inst_numbers, total_numbers)
                    
                    if city_data:
                        page_data[city_key] = city_data
                        logger.debug(f"Added data for {city_key} with {len(city_data)} divisions")
            
            i += 1
        
        return page_data
    
    def _is_header_line(self, line: str) -> bool:
        """Check if line is a header or should be skipped."""
        skip_patterns = [
            "MASTERFORMAT City Cost Indexes",
            "Year 2023 Base", 
            "015433 0241",
            "DIVISION",
            "CONTRACTOR EQUIPMENT SITE",
            "WEIGHTED AVERAGE"
        ]
        
        return any(pattern in line for pattern in skip_patterns)
    
    def _extract_numbers_from_text(self, text: str) -> List[float]:
        """Extract all numbers from text string."""
        numbers = self.number_pattern.findall(text)
        return [float(num) for num in numbers]
    
    def _create_city_key(self, city_name: str, zip_codes: str) -> str:
        """Create standardized city key."""
        # Clean city name
        city_clean = re.sub(r'[^\w\s]', '', city_name).strip().upper()
        city_clean = re.sub(r'\s+', '_', city_clean)
        
        # Clean ZIP codes
        zip_clean = zip_codes.strip()
        
        return f"{city_clean}_{zip_clean}"
    
    def _build_city_data_simple(self, inst_numbers: List[float], total_numbers: List[float]) -> Dict[str, Any]:
        """Build city data structure from numbers."""
        city_data = {}
        
        # Use the minimum count to avoid index errors
        max_divisions = min(
            len(DIVISION_CODES),
            len(inst_numbers) if inst_numbers else 0,
            len(total_numbers) if total_numbers else len(inst_numbers),
            20  # Safety limit
        )
        
        for i in range(max_divisions):
            if i >= len(DIVISION_CODES):
                break
                
            division_code = DIVISION_CODES[i]
            division_desc = DIVISION_MAPPING.get(division_code, f"Division {division_code}")
            
            division_data = {
                "division": division_desc
            }
            
            # Add INST value
            if inst_numbers and i < len(inst_numbers):
                division_data["INST"] = inst_numbers[i]
            
            # Add TOTAL value
            if total_numbers and i < len(total_numbers):
                division_data["TOTAL"] = total_numbers[i]
            
            # Only add division if it has at least one data value
            if "INST" in division_data or "TOTAL" in division_data:
                city_data[division_code] = division_data
        
        return city_data
    
    def get_parsing_summary(self) -> Dict[str, Any]:
        """Get summary of parsing process."""
        return {
            "error_summary": self.error_handler.get_summary(),
            "libraries_used": {
                "pdfplumber": self.use_pdfplumber,
                "pymupdf": self.use_pymupdf
            }
        }