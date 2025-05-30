"""
Test package for MASTERFORMAT PDF to JSON converter.

This package contains unit tests for all converter components including
PDF parsing, JSON validation, data processing utilities, and integration tests.
"""

__version__ = "1.0.0"

# Test configuration
TEST_DATA_DIR = "test_data"
SAMPLE_PDF_PATH = "sample_masterformat.pdf"
SAMPLE_JSON_PATH = "sample_output.json"

# Test constants
TEST_DIVISION_CODES = [
    "015433",
    "0241, 31 - 34", 
    "0310",
    "0320",
    "0330",
    "03",
    "04",
    "05"
]

TEST_CITY_DATA = {
    "LOS_ANGELES_900-902": {
        "015433": {
            "division": "CONTRACTOR EQUIPMENT",
            "MAT": 97.9,
            "INST": 101.1,
            "TOTAL": 101.1
        }
    }
}

# Import test utilities
from .test_converter import *

__all__ = [
    'TEST_DATA_DIR',
    'SAMPLE_PDF_PATH', 
    'SAMPLE_JSON_PATH',
    'TEST_DIVISION_CODES',
    'TEST_CITY_DATA'
]
