"""
Configuration settings for MASTERFORMAT PDF to JSON converter.
"""

import os
from typing import Dict, Any

class Config:
    """Configuration class for the converter."""
    
    # File paths
    INPUT_PDF_PATH: str = ""
    OUTPUT_JSON_PATH: str = "masterformat_output.json"
    LOG_FILE_PATH: str = "converter.log"
    
    # Processing settings
    STRICT_VALIDATION: bool = True
    INCLUDE_SUBDIVISIONS: bool = True
    SKIP_EMPTY_VALUES: bool = False
    
    # PDF parsing settings
    PDF_PASSWORD: str = ""
    USE_PDFPLUMBER: bool = True
    USE_PYMUPDF: bool = True
    
    # Output formatting
    INDENT_JSON: bool = True
    JSON_INDENT_SIZE: int = 2
    SORT_KEYS: bool = True
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    CONSOLE_LOGGING: bool = True
    FILE_LOGGING: bool = True
    
    # Error handling
    CONTINUE_ON_ERROR: bool = True
    MAX_ERRORS: int = 100
    
    # Performance settings
    BATCH_SIZE: int = 50
    MEMORY_LIMIT_MB: int = 1024
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'Config':
        """Create config from dictionary."""
        config = cls()
        for key, value in config_dict.items():
            if hasattr(config, key):
                setattr(config, key, value)
        return config
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Create config from environment variables."""
        config = cls()
        
        # Override with environment variables
        config.INPUT_PDF_PATH = os.getenv('MASTERFORMAT_INPUT_PATH', config.INPUT_PDF_PATH)
        config.OUTPUT_JSON_PATH = os.getenv('MASTERFORMAT_OUTPUT_PATH', config.OUTPUT_JSON_PATH)
        config.LOG_FILE_PATH = os.getenv('MASTERFORMAT_LOG_PATH', config.LOG_FILE_PATH)
        config.LOG_LEVEL = os.getenv('MASTERFORMAT_LOG_LEVEL', config.LOG_LEVEL)
        
        # Boolean settings
        config.STRICT_VALIDATION = os.getenv('MASTERFORMAT_STRICT_VALIDATION', 'true').lower() == 'true'
        config.INCLUDE_SUBDIVISIONS = os.getenv('MASTERFORMAT_INCLUDE_SUBDIVISIONS', 'true').lower() == 'true'
        config.CONTINUE_ON_ERROR = os.getenv('MASTERFORMAT_CONTINUE_ON_ERROR', 'true').lower() == 'true'
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            key: value for key, value in self.__dict__.items()
            if not key.startswith('_')
        }