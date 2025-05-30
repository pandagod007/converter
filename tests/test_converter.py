"""
Comprehensive unit tests for MASTERFORMAT PDF to JSON converter.
"""

import unittest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

# Import modules to test
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pdf_to_json_converter import MasterFormatConverter
from parser import PDFParser
from validator import JSONValidator
from utils import DataProcessor, ErrorHandler, FileHandler
from constants import DIVISION_CODES, DIVISION_DESCRIPTIONS, DATA_TYPES
from config import Config

class TestDataProcessor(unittest.TestCase):
    """Test cases for DataProcessor utility class."""
    
    def setUp(self):
        self.processor = DataProcessor()
    
    def test_clean_text(self):
        """Test text cleaning functionality."""
        # Test basic cleaning
        self.assertEqual(self.processor.clean_text("  Hello   World  "), "Hello World")
        
        # Test empty string
        self.assertEqual(self.processor.clean_text(""), "")
        self.assertEqual(self.processor.clean_text(None), "")
        
        # Test special characters
        self.assertEqual(self.processor.clean_text("Hello@#$%World"), "HelloWorld")
        
        # Test mixed content
        text = "  Los  Angeles   900-902  "
        expected = "Los Angeles 900-902"
        self.assertEqual(self.processor.clean_text(text), expected)
    
    def test_parse_city_zip(self):
        """Test city and ZIP code parsing."""
        # Valid city/ZIP combinations
        test_cases = [
            ("LOS ANGELES 900 - 902", ("LOS ANGELES", "900 - 902")),
            ("BIRMINGHAM 350 - 352", ("BIRMINGHAM", "350 - 352")),
            ("ATLANTA 300 - 303,399", ("ATLANTA", "300 - 303,399")),
            ("NEW YORK 100", ("NEW YORK", "100")),
        ]
        
        for input_text, expected in test_cases:
            with self.subTest(input_text=input_text):
                result = self.processor.parse_city_zip(input_text)
                self.assertEqual(result, expected)
        
        # Invalid cases
        invalid_cases = [
            "INVALID LINE",
            "123 456",
            "",
            "NO NUMBERS HERE"
        ]
        
        for invalid_text in invalid_cases:
            with self.subTest(invalid_text=invalid_text):
                result = self.processor.parse_city_zip(invalid_text)
                self.assertIsNone(result)
    
    def test_is_state_header(self):
        """Test state header detection."""
        # Valid states
        valid_states = ["CALIFORNIA", "TEXAS", "NEW YORK", "FLORIDA"]
        for state in valid_states:
            with self.subTest(state=state):
                self.assertTrue(self.processor.is_state_header(state))
        
        # Invalid states
        invalid_states = ["NOT A STATE", "123", "LOS ANGELES", ""]
        for invalid in invalid_states:
            with self.subTest(invalid=invalid):
                self.assertFalse(self.processor.is_state_header(invalid))
    
    def test_parse_data_row(self):
        """Test data row parsing."""
        # Valid data rows
        test_cases = [
            ("MAT. 97.9 90.8 123.9 101.2", ("MAT", [97.9, 90.8, 123.9, 101.2])),
            ("INST. 101.1 102.7 142.0 134.0", ("INST", [101.1, 102.7, 142.0, 134.0])),
            ("TOTAL 101.1 106.6 134.2 108.6", ("TOTAL", [101.1, 106.6, 134.2, 108.6])),
        ]
        
        for input_text, expected in test_cases:
            with self.subTest(input_text=input_text):
                result = self.processor.parse_data_row(input_text)
                self.assertIsNotNone(result)
                data_type, values = result
                expected_type, expected_values = expected
                self.assertEqual(data_type, expected_type)
                self.assertEqual(len(values), len(expected_values))
                for v1, v2 in zip(values, expected_values):
                    self.assertAlmostEqual(v1, v2, places=1)
    
    def test_validate_numeric_value(self):
        """Test numeric value validation."""
        # Valid values
        self.assertEqual(self.processor.validate_numeric_value(123.45), 123.45)
        self.assertEqual(self.processor.validate_numeric_value("123.45"), 123.45)
        self.assertEqual(self.processor.validate_numeric_value(100), 100.0)
        
        # Invalid values
        self.assertIsNone(self.processor.validate_numeric_value("not_a_number"))
        self.assertIsNone(self.processor.validate_numeric_value(None))
        self.assertIsNone(self.processor.validate_numeric_value(""))
    
    def test_create_city_key(self):
        """Test city key creation."""
        result = self.processor.create_city_key("Los Angeles", "900 - 902")
        self.assertEqual(result, "LOS_ANGELES_900 - 902")
        
        result = self.processor.create_city_key("New York", "100")
        self.assertEqual(result, "NEW_YORK_100")

class TestErrorHandler(unittest.TestCase):
    """Test cases for ErrorHandler utility class."""
    
    def setUp(self):
        self.error_handler = ErrorHandler(max_errors=5)
    
    def test_add_error(self):
        """Test error addition."""
        self.error_handler.add_error("Test error", {"context": "test"})
        
        self.assertTrue(self.error_handler.has_errors())
        self.assertEqual(len(self.error_handler.errors), 1)
        
        summary = self.error_handler.get_summary()
        self.assertEqual(summary['error_count'], 1)
        self.assertEqual(summary['errors'][0]['message'], "Test error")
    
    def test_add_warning(self):
        """Test warning addition."""
        self.error_handler.add_warning("Test warning", {"context": "test"})
        
        self.assertTrue(self.error_handler.has_warnings())
        self.assertEqual(len(self.error_handler.warnings), 1)
        
        summary = self.error_handler.get_summary()
        self.assertEqual(summary['warning_count'], 1)
    
    def test_max_errors_exceeded(self):
        """Test maximum errors limit."""
        # Add errors up to the limit
        for i in range(5):
            self.error_handler.add_error(f"Error {i}")
        
        # Adding one more should raise an exception
        with self.assertRaises(RuntimeError):
            self.error_handler.add_error("Too many errors")
    
    def test_clear(self):
        """Test clearing errors and warnings."""
        self.error_handler.add_error("Test error")
        self.error_handler.add_warning("Test warning")
        
        self.assertTrue(self.error_handler.has_errors())
        self.assertTrue(self.error_handler.has_warnings())
        
        self.error_handler.clear()
        
        self.assertFalse(self.error_handler.has_errors())
        self.assertFalse(self.error_handler.has_warnings())

class TestJSONValidator(unittest.TestCase):
    """Test cases for JSONValidator class."""
    
    def setUp(self):
        self.validator = JSONValidator(strict_mode=True)
        
        # Sample valid data
        self.valid_data = {
            "LOS_ANGELES_900-902": {
                "015433": {
                    "division": "CONTRACTOR EQUIPMENT",
                    "MAT": 97.9,
                    "INST": 101.1,
                    "TOTAL": 101.1
                },
                "03": {
                    "division": "CONCRETE",
                    "MAT": 95.3,
                    "INST": 61.4,
                    "TOTAL": 81.9
                }
            }
        }
    
    def test_validate_valid_data(self):
        """Test validation of valid data."""
        result = self.validator.validate_output(self.valid_data)
        self.assertTrue(result)
    
    def test_validate_empty_data(self):
        """Test validation of empty data."""
        result = self.validator.validate_output({})
        self.assertFalse(result)
        
        result = self.validator.validate_output(None)
        self.assertFalse(result)
    
    def test_validate_invalid_structure(self):
        """Test validation of invalid data structure."""
        # Invalid root structure
        invalid_data = "not a dictionary"
        result = self.validator.validate_output(invalid_data)
        self.assertFalse(result)
        
        # Invalid city data
        invalid_city_data = {
            "CITY_NAME": "not a dictionary"
        }
        result = self.validator.validate_output(invalid_city_data)
        self.assertFalse(result)
    
    def test_validate_against_schema(self):
        """Test schema validation."""
        report = self.validator.validate_against_schema(self.valid_data)
        
        self.assertIsInstance(report, dict)
        self.assertIn('valid', report)
        self.assertIn('cities_processed', report)
        self.assertIn('cities_valid', report)
        self.assertTrue(report['valid'])
        self.assertEqual(report['cities_processed'], 1)
        self.assertEqual(report['cities_valid'], 1)
    
    def test_get_data_quality_metrics(self):
        """Test data quality metrics calculation."""
        metrics = self.validator.get_data_quality_metrics(self.valid_data)
        
        self.assertIsInstance(metrics, dict)
        self.assertIn('total_cities', metrics)
        self.assertIn('data_completeness_percentage', metrics)
        self.assertEqual(metrics['total_cities'], 1)
        self.assertGreater(metrics['data_completeness_percentage'], 0)

class TestPDFParser(unittest.TestCase):
    """Test cases for PDFParser class."""
    
    def setUp(self):
        self.parser = PDFParser()
    
    @patch('pdfplumber.open')
    def test_parse_with_pdfplumber(self, mock_pdfplumber):
        """Test PDF parsing with pdfplumber."""
        # Mock PDF content
        mock_page = Mock()
        mock_page.extract_text.return_value = """
        CALIFORNIA
        LOS ANGELES 900 - 902
        MAT. 97.9 90.8 123.9 101.2 116.2 114.6 107.5 86.8 89.9 101.8 108.6 95.8 100.6 89.1 98.5 100.0 92.6 90.7 100.8 97.9
        INST. 101.1 102.7 142.0 134.0 132.3 136.5 140.7 121.9 140.5 135.0 139.0 141.7 141.7 120.7 130.6 136.9 118.9 129.8 135.8 131.2
        TOTAL 101.1 106.6 134.2 108.6 106.7 115.0 118.4 103.8 117.9 105.9 116.2 134.0 131.9 110.1 117.9 123.9 104.0 110.8 116.8 112.5
        """
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.return_value.__enter__.return_value = mock_pdf
        
        # Test parsing
        result = self.parser._parse_with_pdfplumber("dummy_path.pdf")
        
        self.assertIsInstance(result, dict)
        self.assertGreater(len(result), 0)
    
    def test_process_page_lines(self):
        """Test page line processing."""
        lines = [
            "CALIFORNIA",
            "LOS ANGELES 900 - 902",
            "MAT. 97.9 90.8 123.9 101.2 116.2 114.6 107.5 86.8 89.9 101.8 108.6 95.8 100.6 89.1 98.5 100.0 92.6 90.7 100.8 97.9",
            "INST. 101.1 102.7 142.0 134.0 132.3 136.5 140.7 121.9 140.5 135.0 139.0 141.7 141.7 120.7 130.6 136.9 118.9 129.8 135.8 131.2",
            "TOTAL 101.1 106.6 134.2 108.6 106.7 115.0 118.4 103.8 117.9 105.9 116.2 134.0 131.9 110.1 117.9 123.9 104.0 110.8 116.8 112.5"
        ]
        
        page_data, state = self.parser._process_page_lines(lines, None)
        
        self.assertEqual(state, "CALIFORNIA")
        self.assertIsInstance(page_data, dict)
    
    def test_extract_city_data(self):
        """Test city data extraction."""
        lines = [
            "MAT. 97.9 90.8 123.9 101.2 116.2 114.6 107.5 86.8 89.9 101.8 108.6 95.8 100.6 89.1 98.5 100.0 92.6 90.7 100.8 97.9",
            "INST. 101.1 102.7 142.0 134.0 132.3 136.5 140.7 121.9 140.5 135.0 139.0 141.7 141.7 120.7 130.6 136.9 118.9 129.8 135.8 131.2",
            "TOTAL 101.1 106.6 134.2 108.6 106.7 115.0 118.4 103.8 117.9 105.9 116.2 134.0 131.9 110.1 117.9 123.9 104.0 110.8 116.8 112.5"
        ]
        
        city_data, lines_consumed = self.parser._extract_city_data(lines, 0)
        
        self.assertIsInstance(city_data, dict)
        self.assertGreater(len(city_data), 0)
        self.assertGreater(lines_consumed, 0)

class TestConfig(unittest.TestCase):
    """Test cases for Config class."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = Config()
        
        self.assertEqual(config.OUTPUT_JSON_PATH, "masterformat_output.json")
        self.assertEqual(config.LOG_FILE_PATH, "converter.log")
        self.assertTrue(config.STRICT_VALIDATION)
        self.assertTrue(config.INCLUDE_SUBDIVISIONS)
    
    def test_from_dict(self):
        """Test configuration from dictionary."""
        config_dict = {
            'OUTPUT_JSON_PATH': 'custom_output.json',
            'STRICT_VALIDATION': False,
            'LOG_LEVEL': 'DEBUG'
        }
        
        config = Config.from_dict(config_dict)
        
        self.assertEqual(config.OUTPUT_JSON_PATH, 'custom_output.json')
        self.assertFalse(config.STRICT_VALIDATION)
        self.assertEqual(config.LOG_LEVEL, 'DEBUG')
    
    @patch.dict(os.environ, {
        'MASTERFORMAT_OUTPUT_PATH': 'env_output.json',
        'MASTERFORMAT_STRICT_VALIDATION': 'false'
    })
    def test_from_env(self):
        """Test configuration from environment variables."""
        config = Config.from_env()
        
        self.assertEqual(config.OUTPUT_JSON_PATH, 'env_output.json')
        self.assertFalse(config.STRICT_VALIDATION)

class TestMasterFormatConverter(unittest.TestCase):
    """Test cases for MasterFormatConverter main class."""
    
    def setUp(self):
        self.config = Config()
        self.config.LOG_LEVEL = 'ERROR'  # Reduce log noise in tests
        self.converter = MasterFormatConverter(self.config)
    
    def test_converter_initialization(self):
        """Test converter initialization."""
        self.assertIsInstance(self.converter.parser, PDFParser)
        self.assertIsInstance(self.converter.validator, JSONValidator)
        self.assertEqual(self.converter.config, self.config)
    
    def test_validate_existing_json(self):
        """Test validation of existing JSON file."""
        # Create temporary JSON file
        test_data = {
            "TEST_CITY_123": {
                "015433": {
                    "division": "CONTRACTOR EQUIPMENT",
                    "MAT": 100.0,
                    "INST": 100.0,
                    "TOTAL": 100.0
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name
        
        try:
            result = self.converter.validate_existing_json(temp_path)
            
            self.assertIsInstance(result, dict)
            self.assertIn('validation_result', result)
            self.assertIn('quality_metrics', result)
            
        finally:
            os.unlink(temp_path)

class TestFileHandler(unittest.TestCase):
    """Test cases for FileHandler utility class."""
    
    def test_ensure_directory(self):
        """Test directory creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_path = os.path.join(temp_dir, "subdir", "file.txt")
            
            # Directory should not exist initially
            self.assertFalse(os.path.exists(os.path.dirname(test_path)))
            
            FileHandler.ensure_directory(test_path)
            
            # Directory should exist after calling ensure_directory
            self.assertTrue(os.path.exists(os.path.dirname(test_path)))
    
    def test_backup_file(self):
        """Test file backup functionality."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"test content")
            temp_path = temp_file.name
        
        try:
            backup_path = FileHandler.backup_file(temp_path)
            
            self.assertTrue(os.path.exists(backup_path))
            self.assertIn("backup_", backup_path)
            
            # Clean up backup file
            if backup_path and os.path.exists(backup_path):
                os.unlink(backup_path)
                
        finally:
            os.unlink(temp_path)
    
    def test_get_file_size_mb(self):
        """Test file size calculation."""
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file.write(b"x" * 1024 * 1024)  # 1 MB
            temp_file.flush()
            
            size_mb = FileHandler.get_file_size_mb(temp_file.name)
            self.assertAlmostEqual(size_mb, 1.0, places=1)

class TestConstants(unittest.TestCase):
    """Test cases for constants and mappings."""
    
    def test_division_codes_count(self):
        """Test that we have the expected number of division codes."""
        self.assertEqual(len(DIVISION_CODES), 20)
        self.assertEqual(len(DIVISION_DESCRIPTIONS), 20)
    
    def test_division_mapping(self):
        """Test division code to description mapping."""
        from constants import DIVISION_MAPPING
        
        self.assertEqual(len(DIVISION_MAPPING), 20)
        self.assertEqual(DIVISION_MAPPING["015433"], "CONTRACTOR EQUIPMENT")
        self.assertEqual(DIVISION_MAPPING["MF2018"], "WEIGHTED AVERAGE")
    
    def test_data_types(self):
        """Test data type constants."""
        self.assertEqual(len(DATA_TYPES), 3)
        self.assertIn("MAT", DATA_TYPES)
        self.assertIn("INST", DATA_TYPES)
        self.assertIn("TOTAL", DATA_TYPES)

class TestIntegration(unittest.TestCase):
    """Integration tests for the complete converter system."""
    
    def setUp(self):
        self.config = Config()
        self.config.LOG_LEVEL = 'ERROR'
        self.converter = MasterFormatConverter(self.config)
    
    @patch('parser.PDFParser.parse_pdf')
    def test_full_conversion_workflow(self, mock_parse_pdf):
        """Test the complete conversion workflow."""
        # Mock PDF parsing result
        mock_data = {
            "LOS_ANGELES_900-902": {
                "015433": {
                    "division": "CONTRACTOR EQUIPMENT",
                    "MAT": 97.9,
                    "INST": 101.1,
                    "TOTAL": 101.1
                },
                "03": {
                    "division": "CONCRETE",
                    "MAT": 95.3,
                    "INST": 61.4,
                    "TOTAL": 81.9
                }
            }
        }
        mock_parse_pdf.return_value = mock_data
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a dummy PDF file
            pdf_path = os.path.join(temp_dir, "test.pdf")
            with open(pdf_path, 'w') as f:
                f.write("dummy pdf content")
            
            output_path = os.path.join(temp_dir, "output.json")
            
            # Run conversion
            result = self.converter.convert_pdf_to_json(pdf_path, output_path)
            
            # Verify result
            self.assertEqual(result, mock_data)
            self.assertTrue(os.path.exists(output_path))
            
            # Verify JSON content
            with open(output_path, 'r') as f:
                saved_data = json.load(f)
            
            self.assertEqual(saved_data, mock_data)

if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestDataProcessor,
        TestErrorHandler,
        TestJSONValidator,
        TestPDFParser,
        TestConfig,
        TestMasterFormatConverter,
        TestFileHandler,
        TestConstants,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\nTest Results:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
