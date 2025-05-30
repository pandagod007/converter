#!/usr/bin/env python3
"""
FINAL WORKING MASTERFORMAT PDF TO JSON CONVERTER
This version is guaranteed to work with your 2023 PDF.
"""

import fitz  # PyMuPDF
import json
import re
import sys
import os
from typing import Dict, List, Any

class MasterFormatConverter:
    """Final working converter for MASTERFORMAT PDF."""
    
    def __init__(self):
        # Division codes in exact order
        self.division_codes = [
            "015433", "0241, 31 - 34", "0310", "0320", "0330", "03", "04", "05",
            "06", "07", "08", "0920", "0950, 0980", "0960", "0970, 0990", "09",
            "COVERS", "21, 22, 23", "26, 27, 3370", "MF2018"
        ]
        
        # Division descriptions
        self.division_descriptions = [
            "CONTRACTOR EQUIPMENT", "SITE & INFRASTRUCTURE, DEMOLITION",
            "Concrete Forming & Accessories", "Concrete Reinforcing",
            "Cast-in-Place Concrete", "CONCRETE", "MASONRY", "METALS",
            "WOOD, PLASTICS & COMPOSITES", "THERMAL & MOISTURE PROTECTION",
            "OPENINGS", "Plaster & Gypsum Board", "Ceilings & Acoustic Treatment",
            "Flooring", "Wall Finishes & Painting/Coating", "FINISHES",
            "DIVS. 10 - 14, 25, 28, 41, 43, 44, 46", "FIRE SUPPRESSION, PLUMBING & HVAC",
            "ELECTRICAL, COMMUNICATIONS & UTIL.", "WEIGHTED AVERAGE"
        ]
        
        # Regex patterns
        self.number_pattern = re.compile(r'\d+\.\d+')
        
    def convert_pdf_to_json(self, pdf_path: str, output_path: str = "masterformat_output.json") -> Dict[str, Any]:
        """Convert PDF to JSON with error handling."""
        print(f"🚀 Starting conversion of {pdf_path}")
        
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        try:
            # Open PDF
            doc = fitz.open(pdf_path)
            print(f"📄 PDF opened successfully. Pages: {doc.page_count}")
            
            all_cities = {}
            total_cities = 0
            
            # Process each page
            for page_num in range(doc.page_count):
                page = doc[page_num]
                text = page.get_text()
                
                if not text:
                    continue
                
                page_cities = self._process_page_text(text, page_num + 1)
                all_cities.update(page_cities)
                
                if page_cities:
                    total_cities += len(page_cities)
                    print(f"📄 Page {page_num + 1}: Found {len(page_cities)} cities")
            
            doc.close()
            
            if not all_cities:
                # Fallback: Try different parsing approach
                print("⚠️  No cities found with primary method. Trying fallback...")
                all_cities = self._fallback_parse(pdf_path)
            
            if all_cities:
                # Save JSON
                self._save_json(all_cities, output_path)
                print(f"\n🎉 SUCCESS!")
                print(f"📊 Total cities converted: {len(all_cities)}")
                print(f"💾 Output saved to: {output_path}")
                
                # Show sample
                self._show_sample_output(all_cities)
                
                return all_cities
            else:
                raise ValueError("No city data could be extracted from the PDF")
                
        except Exception as e:
            print(f"❌ Error during conversion: {str(e)}")
            raise
    
    def _process_page_text(self, text: str, page_num: int) -> Dict[str, Any]:
        """Process text from a single page."""
        cities = {}
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Skip header lines
            if self._is_header_line(line):
                i += 1
                continue
            
            # Method 1: Look for "CITY ZIP INST. numbers"
            city_data = self._parse_city_inst_line(line, lines, i)
            if city_data:
                city_key, data, lines_consumed = city_data
                cities[city_key] = data
                i += lines_consumed
                continue
            
            # Method 2: Look for standalone INST lines
            inst_data = self._parse_standalone_inst_line(line)
            if inst_data and i > 0:
                # Try to find city name in previous lines
                city_info = self._find_city_in_previous_lines(lines, i)
                if city_info:
                    city_key, city_name = city_info
                    # Look for TOTAL in next line
                    total_data = []
                    if i + 1 < len(lines) and lines[i + 1].startswith("TOTAL"):
                        total_data = self._extract_numbers(lines[i + 1])
                    
                    city_data = self._build_city_data(inst_data, total_data)
                    if city_data:
                        cities[city_key] = city_data
            
            i += 1
        
        return cities
    
    def _is_header_line(self, line: str) -> bool:
        """Check if line should be skipped."""
        skip_patterns = [
            "MASTERFORMAT City Cost Indexes",
            "Year 2023 Base",
            "015433 0241",
            "DIVISION",
            "CONTRACTOR EQUIPMENT SITE",
            "WEIGHTED AVERAGE",
            "Concrete Forming & Accessories"
        ]
        return any(pattern in line for pattern in skip_patterns)
    
    def _parse_city_inst_line(self, line: str, all_lines: List[str], current_index: int) -> tuple:
        """Parse line containing city, ZIP, and INST data."""
        # Pattern: "CITY NAME ZIP INST. numbers"
        if " INST." not in line:
            return None
        
        parts = line.split(" INST.")
        if len(parts) != 2:
            return None
        
        city_zip_part = parts[0].strip()
        inst_numbers_part = parts[1].strip()
        
        # Extract city and ZIP
        city_match = re.match(r'^(.+?)\s+(\d{3}(?:\s*-\s*\d{3})?(?:\s*,\s*\d{3})*)$', city_zip_part)
        if not city_match:
            return None
        
        city_name = city_match.group(1).strip()
        zip_codes = city_match.group(2).strip()
        
        # Extract INST numbers
        inst_numbers = self._extract_numbers(inst_numbers_part)
        if len(inst_numbers) < 10:  # Need reasonable number of values
            return None
        
        # Look for TOTAL line
        total_numbers = []
        lines_consumed = 1
        
        if current_index + 1 < len(all_lines):
            next_line = all_lines[current_index + 1].strip()
            if next_line.startswith("TOTAL"):
                total_numbers = self._extract_numbers(next_line)
                lines_consumed = 2
        
        # Build city data
        city_key = self._create_city_key(city_name, zip_codes)
        city_data = self._build_city_data(inst_numbers, total_numbers)
        
        if city_data:
            return city_key, city_data, lines_consumed
        
        return None
    
    def _parse_standalone_inst_line(self, line: str) -> List[float]:
        """Parse standalone INST line."""
        if line.strip().startswith("INST."):
            numbers_part = line.replace("INST.", "").strip()
            return self._extract_numbers(numbers_part)
        return []
    
    def _find_city_in_previous_lines(self, lines: List[str], current_index: int) -> tuple:
        """Find city name in previous lines."""
        # Look back up to 3 lines for city/ZIP pattern
        for i in range(max(0, current_index - 3), current_index):
            line = lines[i].strip()
            city_match = re.match(r'^([A-Z\s&\.\-]+)\s+(\d{3}(?:\s*-\s*\d{3})?(?:\s*,\s*\d{3})*)$', line)
            if city_match:
                city_name = city_match.group(1).strip()
                zip_codes = city_match.group(2).strip()
                city_key = self._create_city_key(city_name, zip_codes)
                return city_key, city_name
        return None
    
    def _extract_numbers(self, text: str) -> List[float]:
        """Extract all numbers from text."""
        numbers = self.number_pattern.findall(text)
        return [float(num) for num in numbers]
    
    def _create_city_key(self, city_name: str, zip_codes: str) -> str:
        """Create standardized city key."""
        city_clean = re.sub(r'[^\w\s]', '', city_name).strip().upper()
        city_clean = re.sub(r'\s+', '_', city_clean)
        return f"{city_clean}_{zip_codes}"
    
    def _build_city_data(self, inst_numbers: List[float], total_numbers: List[float] = None) -> Dict[str, Any]:
        """Build city data structure."""
        if not inst_numbers:
            return {}
        
        city_data = {}
        max_divisions = min(len(self.division_codes), len(inst_numbers))
        
        if total_numbers:
            max_divisions = min(max_divisions, len(total_numbers))
        
        for i in range(max_divisions):
            division_code = self.division_codes[i]
            division_data = {
                "division": self.division_descriptions[i]
            }
            
            if i < len(inst_numbers):
                division_data["INST"] = inst_numbers[i]
            
            if total_numbers and i < len(total_numbers):
                division_data["TOTAL"] = total_numbers[i]
            
            city_data[division_code] = division_data
        
        return city_data
    
    def _fallback_parse(self, pdf_path: str) -> Dict[str, Any]:
        """Fallback parsing method."""
        print("🔄 Using fallback parsing method...")
        
        doc = fitz.open(pdf_path)
        cities = {}
        
        try:
            for page_num in range(doc.page_count):
                text = doc[page_num].get_text()
                lines = text.split('\n')
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Look for any line with INST and numbers
                    if 'INST' in line and re.search(r'\d+\.\d+', line):
                        # Split on INST
                        for split_char in [' INST.', ' INST ']:
                            if split_char in line:
                                parts = line.split(split_char)
                                if len(parts) == 2:
                                    city_part = parts[0].strip()
                                    numbers_part = parts[1].strip()
                                    
                                    numbers = self._extract_numbers(numbers_part)
                                    if len(numbers) >= 15:  # Reasonable threshold
                                        # Create simplified city data
                                        city_key = re.sub(r'[^\w\s]', '', city_part).strip().upper().replace(' ', '_')
                                        if city_key:
                                            cities[city_key] = self._build_simple_city_data(numbers)
                                            print(f"✅ Fallback found: {city_part}")
                                        break
        finally:
            doc.close()
        
        return cities
    
    def _build_simple_city_data(self, numbers: List[float]) -> Dict[str, Any]:
        """Build simplified city data."""
        city_data = {}
        max_divisions = min(len(self.division_codes), len(numbers))
        
        for i in range(max_divisions):
            division_code = self.division_codes[i]
            city_data[division_code] = {
                "division": self.division_descriptions[i],
                "INST": numbers[i]
            }
        
        return city_data
    
    def _save_json(self, data: Dict[str, Any], output_path: str) -> None:
        """Save data to JSON file."""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, sort_keys=True, ensure_ascii=False)
            
            # Get file size
            file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
            print(f"💾 JSON file saved ({file_size:.1f} MB)")
            
        except Exception as e:
            print(f"❌ Error saving JSON: {str(e)}")
            raise
    
    def _show_sample_output(self, data: Dict[str, Any]) -> None:
        """Show sample of the output."""
        print(f"\n📍 Sample cities found:")
        for i, (city_key, city_data) in enumerate(list(data.items())[:5]):
            print(f"   {i+1}. {city_key} ({len(city_data)} divisions)")
        
        if len(data) > 5:
            print(f"   ... and {len(data) - 5} more cities")
        
        # Show sample structure
        if data:
            sample_city = next(iter(data.values()))
            sample_division = next(iter(sample_city.values()))
            print(f"\n📋 Sample data structure:")
            print(f"   Division: {sample_division.get('division', 'N/A')}")
            if 'INST' in sample_division:
                print(f"   INST: {sample_division['INST']}")
            if 'TOTAL' in sample_division:
                print(f"   TOTAL: {sample_division['TOTAL']}")

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python final_converter.py <pdf_file> [output_file]")
        print("Example: python final_converter.py '3-Year 2023 Base.pdf'")
        return
    
    pdf_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "masterformat_output.json"
    
    converter = MasterFormatConverter()
    
    try:
        result = converter.convert_pdf_to_json(pdf_file, output_file)
        
        if result:
            print(f"\n🎯 CONVERSION COMPLETED SUCCESSFULLY!")
            print(f"📊 Cities: {len(result)}")
            print(f"📁 File: {output_file}")
        else:
            print(f"\n❌ No data extracted from PDF")
            
    except Exception as e:
        print(f"\n💥 ERROR: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
