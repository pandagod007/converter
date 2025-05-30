"""
Utility functions for MASTERFORMAT PDF to JSON conversion.
"""

import re
import logging
from typing import List, Optional, Tuple, Union, Dict, Any
from constants import (
    CITY_ZIP_PATTERN, STATE_PATTERN, DATA_ROW_PATTERN, 
    NUMBER_PATTERN, US_STATES
)

logger = logging.getLogger(__name__)

class DataProcessor:
    """Utility class for data processing and validation."""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text."""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove special characters that might interfere
        text = re.sub(r'[^\w\s\-\.,&]', '', text)
        
        return text.strip()
    
    @staticmethod
    def parse_city_zip(line: str) -> Optional[Tuple[str, str]]:
        """
        Parse city name and ZIP code from a line.
        Returns tuple of (city_name, zip_codes) or None if no match.
        """
        line = DataProcessor.clean_text(line)
        match = re.match(CITY_ZIP_PATTERN, line)
        
        if match:
            city_name = match.group(1).strip()
            zip_codes = match.group(2).strip()
            return city_name, zip_codes
        
        return None
    
    @staticmethod
    def is_state_header(line: str) -> bool:
        """Check if line is a state header."""
        line = DataProcessor.clean_text(line).upper()
        return line in US_STATES
    
    @staticmethod
    def parse_data_row(line: str) -> Optional[Tuple[str, List[float]]]:
        """
        Parse a data row (MAT., INST., or TOTAL).
        Returns tuple of (data_type, values) or None if no match.
        """
        line = DataProcessor.clean_text(line)
        match = re.match(DATA_ROW_PATTERN, line)
        
        if match:
            data_type = match.group(1).replace('.', '')  # Remove period
            values_str = match.group(2)
            
            # Extract all numbers from the values string
            numbers = re.findall(NUMBER_PATTERN, values_str)
            values = [float(num) for num in numbers]
            
            return data_type, values
        
        return None
    
    @staticmethod
    def extract_numbers(text: str) -> List[float]:
        """Extract all numeric values from text."""
        numbers = re.findall(NUMBER_PATTERN, text)
        return [float(num) for num in numbers]
    
    @staticmethod
    def validate_numeric_value(value: Union[str, float, None]) -> Optional[float]:
        """Validate and convert a numeric value."""
        if value is None:
            return None
        
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            try:
                return float(value.strip())
            except (ValueError, AttributeError):
                return None
        
        return None
    
    @staticmethod
    def create_city_key(city_name: str, zip_codes: str) -> str:
        """Create a standardized key for a city."""
        # Clean and format city name
        city_clean = DataProcessor.clean_text(city_name).upper()
        
        # Format ZIP codes
        zip_clean = DataProcessor.clean_text(zip_codes)
        
        return f"{city_clean}_{zip_clean}"
    
    @staticmethod
    def split_text_lines(text: str) -> List[str]:
        """Split text into lines and clean them."""
        lines = text.split('\n')
        return [DataProcessor.clean_text(line) for line in lines if line.strip()]
    
    @staticmethod
    def is_valid_data_row(values: List[float], expected_count: int = 20) -> bool:
        """Validate if a data row has the expected number of values."""
        return len(values) == expected_count and all(
            isinstance(v, (int, float)) for v in values
        )
    
    @staticmethod
    def format_json_key(key: str) -> str:
        """Format a key for JSON output."""
        # Remove special characters and normalize spacing
        key = re.sub(r'[^\w\s\-]', '', key)
        key = re.sub(r'\s+', '_', key.strip())
        return key.upper()
    
    @staticmethod
    def log_processing_stats(stats: Dict[str, Any]) -> None:
        """Log processing statistics."""
        logger.info("Processing Statistics:")
        for key, value in stats.items():
            logger.info(f"  {key}: {value}")

class FileHandler:
    """Utility class for file operations."""
    
    @staticmethod
    def ensure_directory(file_path: str) -> None:
        """Ensure the directory for a file path exists."""
        import os
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
    
    @staticmethod
    def backup_file(file_path: str) -> str:
        """Create a backup of an existing file."""
        import os
        import shutil
        from datetime import datetime
        
        if os.path.exists(file_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{file_path}.backup_{timestamp}"
            shutil.copy2(file_path, backup_path)
            return backup_path
        return ""
    
    @staticmethod
    def get_file_size_mb(file_path: str) -> float:
        """Get file size in megabytes."""
        import os
        if os.path.exists(file_path):
            return os.path.getsize(file_path) / (1024 * 1024)
        return 0.0

class ErrorHandler:
    """Utility class for error handling and reporting."""
    
    def __init__(self, max_errors: int = 100):
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
        self.max_errors = max_errors
    
    def add_error(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Add an error to the error list."""
        error = {
            'message': message,
            'context': context or {},
            'timestamp': self._get_timestamp()
        }
        self.errors.append(error)
        logger.error(f"Error: {message} - Context: {context}")
        
        if len(self.errors) >= self.max_errors:
            raise RuntimeError(f"Maximum number of errors ({self.max_errors}) exceeded")
    
    def add_warning(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Add a warning to the warning list."""
        warning = {
            'message': message,
            'context': context or {},
            'timestamp': self._get_timestamp()
        }
        self.warnings.append(warning)
        logger.warning(f"Warning: {message} - Context: {context}")
    
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of errors and warnings."""
        return {
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
            'errors': self.errors,
            'warnings': self.warnings
        }
    
    def clear(self) -> None:
        """Clear all errors and warnings."""
        self.errors.clear()
        self.warnings.clear()
    
    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()