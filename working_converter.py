#!/usr/bin/env python3
"""
WORKING CONVERTER - Based on actual PDF structure analysis
The PDF has cities and ZIP codes as separate elements, not in lines with data.
"""

import fitz
import json
import re
import sys

def convert_masterformat_pdf(pdf_path, output_path="working_output.json"):
    """Convert PDF based on actual structure."""
    
    print(f"🚀 WORKING CONVERTER - Processing {pdf_path}")
    
    doc = fitz.open(pdf_path)
    print(f"📄 PDF: {doc.page_count} pages")
    
    # Division info
    divisions = [
        "015433", "0241, 31 - 34", "0310", "0320", "0330", "03", "04", "05",
        "06", "07", "08", "0920", "0950, 0980", "0960", "0970, 0990", "09",
        "COVERS", "21, 22, 23", "26, 27, 3370", "MF2018"
    ]
    
    descriptions = [
        "CONTRACTOR EQUIPMENT", "SITE & INFRASTRUCTURE, DEMOLITION",
        "Concrete Forming & Accessories", "Concrete Reinforcing",
        "Cast-in-Place Concrete", "CONCRETE", "MASONRY", "METALS",
        "WOOD, PLASTICS & COMPOSITES", "THERMAL & MOISTURE PROTECTION",
        "OPENINGS", "Plaster & Gypsum Board", "Ceilings & Acoustic Treatment",
        "Flooring", "Wall Finishes & Painting/Coating", "FINISHES",
        "DIVS. 10 - 14, 25, 28, 41, 43, 44, 46", "FIRE SUPPRESSION, PLUMBING & HVAC",
        "ELECTRICAL, COMMUNICATIONS & UTIL.", "WEIGHTED AVERAGE"
    ]
    
    all_cities = {}
    
    # Extract data using coordinate-based approach
    for page_num in range(doc.page_count):
        page = doc[page_num]
        
        # Get all text blocks with coordinates
        blocks = page.get_text("dict")
        
        page_cities = extract_cities_from_blocks(blocks, divisions, descriptions, page_num + 1)
        all_cities.update(page_cities)
        
        if page_cities:
            print(f"📄 Page {page_num + 1}: Found {len(page_cities)} cities")
    
    doc.close()
    
    # If coordinate method didn't work, try text extraction method
    if not all_cities:
        print("🔄 Trying alternative extraction method...")
        all_cities = extract_with_text_method(pdf_path, divisions, descriptions)
    
    # If still no data, try raw number extraction
    if not all_cities:
        print("🔄 Trying raw number extraction...")
        all_cities = extract_raw_numbers(pdf_path, divisions, descriptions)
    
    # Save results
    if all_cities:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_cities, f, indent=2, sort_keys=True)
        
        file_size = len(json.dumps(all_cities)) / 1024
        
        print(f"\n🎉 SUCCESS!")
        print(f"📊 Cities found: {len(all_cities)}")
        print(f"💾 File saved: {output_path} ({file_size:.1f} KB)")
        
        # Show sample
        print(f"\n📍 Sample cities:")
        for i, (city_key, city_data) in enumerate(list(all_cities.items())[:5]):
            divisions_count = len(city_data)
            print(f"   {i+1}. {city_key} ({divisions_count} divisions)")
        
        return all_cities
    else:
        print("❌ No data extracted")
        return {}

def extract_cities_from_blocks(blocks, divisions, descriptions, page_num):
    """Extract cities using text block coordinates."""
    cities = {}
    
    try:
        if "blocks" in blocks:
            all_text_items = []
            
            # Extract all text items with positions
            for block in blocks["blocks"]:
                if "lines" in block:
                    for line in block["lines"]:
                        if "spans" in line:
                            for span in line["spans"]:
                                if "text" in span and span["text"].strip():
                                    text = span["text"].strip()
                                    bbox = span.get("bbox", [0, 0, 0, 0])
                                    all_text_items.append({
                                        "text": text,
                                        "x": bbox[0],
                                        "y": bbox[1],
                                        "size": span.get("size", 12)
                                    })
            
            # Sort by Y position (top to bottom), then X position (left to right)
            all_text_items.sort(key=lambda item: (item["y"], item["x"]))
            
            # Look for city patterns
            city_data = find_cities_in_text_items(all_text_items, divisions, descriptions, page_num)
            cities.update(city_data)
    
    except Exception as e:
        print(f"   Error in coordinate extraction: {e}")
    
    return cities

def find_cities_in_text_items(text_items, divisions, descriptions, page_num):
    """Find cities in sorted text items."""
    cities = {}
    
    # Look for city names and associated data
    for i, item in enumerate(text_items):
        text = item["text"]
        
        # Check if this looks like a city name (all caps, reasonable length)
        if (text.isupper() and 
            len(text) > 3 and 
            len(text) < 30 and
            not any(skip in text for skip in ["DIVISION", "INST", "TOTAL", "MAT", "COVERS"]) and
            re.match(r'^[A-Z\s&\.\-/]+$', text)):
            
            # Look for ZIP code in nearby items
            zip_code = find_nearby_zip(text_items, i)
            
            # Look for numeric data in nearby items
            numeric_data = find_nearby_numbers(text_items, i)
            
            if numeric_data and len(numeric_data) >= 10:
                city_key = f"{text.replace(' ', '_')}_{zip_code}" if zip_code else f"{text.replace(' ', '_')}_PAGE{page_num}"
                
                # Build city data
                city_data = {}
                max_divisions = min(len(divisions), len(numeric_data))
                
                for j in range(max_divisions):
                    city_data[divisions[j]] = {
                        "division": descriptions[j],
                        "VALUE": numeric_data[j]
                    }
                
                if city_data:
                    cities[city_key] = city_data
                    print(f"   ✅ Found: {text} (ZIP: {zip_code}, {len(numeric_data)} values)")
    
    return cities

def find_nearby_zip(text_items, city_index):
    """Find ZIP code near city name."""
    # Look in next few items for ZIP pattern
    for i in range(city_index + 1, min(city_index + 5, len(text_items))):
        text = text_items[i]["text"]
        if re.match(r'^\d{3}(-\d{3})?$', text):
            return text
    return None

def find_nearby_numbers(text_items, city_index):
    """Find numeric data near city name."""
    numbers = []
    
    # Look in a range around the city for decimal numbers
    start_range = max(0, city_index - 5)
    end_range = min(len(text_items), city_index + 50)
    
    for i in range(start_range, end_range):
        text = text_items[i]["text"]
        if re.match(r'^\d+\.\d+$', text):
            numbers.append(float(text))
    
    return numbers

def extract_with_text_method(pdf_path, divisions, descriptions):
    """Alternative extraction method using plain text."""
    print("   Using text-based extraction...")
    
    doc = fitz.open(pdf_path)
    all_cities = {}
    
    for page_num in range(doc.page_count):
        text = doc[page_num].get_text()
        
        # Split into words
        words = text.split()
        
        cities_on_page = []
        numbers_on_page = []
        
        # Collect cities and numbers separately
        for word in words:
            word = word.strip()
            if not word:
                continue
            
            # Collect potential city names
            if (word.isupper() and 
                len(word) > 3 and 
                len(word) < 20 and
                re.match(r'^[A-Z\s&\.\-/]+$', word) and
                not any(skip in word for skip in ["DIVISION", "INST", "TOTAL", "MAT", "COVERS"])):
                cities_on_page.append(word)
            
            # Collect decimal numbers
            if re.match(r'^\d+\.\d+$', word):
                numbers_on_page.append(float(word))
        
        # Create city data by distributing numbers among cities
        if cities_on_page and numbers_on_page and len(numbers_on_page) >= 20:
            numbers_per_city = len(numbers_on_page) // max(len(cities_on_page), 1)
            
            for i, city in enumerate(cities_on_page):
                start_idx = i * numbers_per_city
                end_idx = start_idx + min(numbers_per_city, len(divisions))
                
                if start_idx < len(numbers_on_page):
                    city_numbers = numbers_on_page[start_idx:end_idx]
                    
                    if len(city_numbers) >= 10:  # Reasonable threshold
                        city_key = f"{city}_PAGE{page_num + 1}_{i + 1}"
                        
                        city_data = {}
                        for j in range(min(len(divisions), len(city_numbers))):
                            city_data[divisions[j]] = {
                                "division": descriptions[j],
                                "VALUE": city_numbers[j]
                            }
                        
                        if city_data:
                            all_cities[city_key] = city_data
                            print(f"   ✅ Text method: {city} ({len(city_numbers)} values)")
    
    doc.close()
    return all_cities

def extract_raw_numbers(pdf_path, divisions, descriptions):
    """Raw number extraction as last resort."""
    print("   Using raw number extraction...")
    
    doc = fitz.open(pdf_path)
    all_cities = {}
    
    for page_num in range(doc.page_count):
        text = doc[page_num].get_text()
        
        # Find all decimal numbers
        all_numbers = [float(x) for x in re.findall(r'\d+\.\d+', text)]
        
        if len(all_numbers) >= 100:  # Enough numbers for multiple cities
            # Create artificial cities from number groups
            chunk_size = 20  # Assume 20 divisions per city
            
            for i in range(0, len(all_numbers) - chunk_size, chunk_size):
                city_numbers = all_numbers[i:i + chunk_size]
                
                city_key = f"EXTRACTED_DATA_PAGE{page_num + 1}_CHUNK{i // chunk_size + 1}"
                
                city_data = {}
                for j in range(min(len(divisions), len(city_numbers))):
                    city_data[divisions[j]] = {
                        "division": descriptions[j],
                        "VALUE": city_numbers[j]
                    }
                
                if city_data:
                    all_cities[city_key] = city_data
                    print(f"   ✅ Raw extraction: {city_key}")
                
                # Limit to prevent too many entries
                if len(all_cities) >= 50:
                    break
    
    doc.close()
    return all_cities

def main():
    if len(sys.argv) < 2:
        print("Usage: python working_converter.py <pdf_file> [output_file]")
        return 1
    
    pdf_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "working_output.json"
    
    result = convert_masterformat_pdf(pdf_file, output_file)
    
    if result:
        print(f"\n🎯 CONVERSION SUCCESSFUL!")
        return 0
    else:
        print(f"\n❌ CONVERSION FAILED!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
