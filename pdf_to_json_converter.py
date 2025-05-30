"""
Main MASTERFORMAT PDF to JSON converter class.
"""

import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from parser import PDFParser
from validator import JSONValidator
from utils import DataProcessor, FileHandler, ErrorHandler
from config import Config
from constants import LOG_FORMAT, LOG_DATE_FORMAT

logger = logging.getLogger(__name__)

class MasterFormatConverter:
    """
    Main converter class for MASTERFORMAT PDF to JSON conversion.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the converter with configuration."""
        self.config = config or Config()
        self.parser = PDFParser(
            use_pdfplumber=self.config.USE_PDFPLUMBER,
            use_pymupdf=self.config.USE_PYMUPDF
        )
        self.validator = JSONValidator(strict_mode=self.config.STRICT_VALIDATION)
        self.error_handler = ErrorHandler(max_errors=self.config.MAX_ERRORS)
        
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        logging.basicConfig(
            level=getattr(logging, self.config.LOG_LEVEL),
            format=LOG_FORMAT,
            datefmt=LOG_DATE_FORMAT
        )
        
        if self.config.FILE_LOGGING:
            file_handler = logging.FileHandler(self.config.LOG_FILE_PATH)
            file_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
            logging.getLogger().addHandler(file_handler)
    
    def convert_pdf_to_json(self, 
                           input_path: str, 
                           output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Convert MASTERFORMAT PDF to JSON format.
        
        Args:
            input_path: Path to input PDF file
            output_path: Path for output JSON file (optional)
            
        Returns:
            Dictionary containing the converted data
            
        Raises:
            FileNotFoundError: If input file doesn't exist
            ValueError: If PDF parsing fails
            RuntimeError: If validation fails in strict mode
        """
        logger.info(f"Starting conversion: {input_path}")
        
        # Validate input file
        input_file = Path(input_path)
        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        if not input_file.suffix.lower() == '.pdf':
            raise ValueError(f"Input file must be a PDF: {input_path}")
        
        # Set output path if not provided
        if output_path is None:
            output_path = self.config.OUTPUT_JSON_PATH
        
        try:
            # Parse PDF
            logger.info("Parsing PDF...")
            raw_data = self.parser.parse_pdf(str(input_file))
            
            if not raw_data:
                raise ValueError("No data extracted from PDF")
            
            logger.info(f"Extracted data for {len(raw_data)} cities")
            
            # Validate output if enabled
            if self.config.STRICT_VALIDATION:
                logger.info("Validating output...")
                is_valid = self.validator.validate_output(raw_data)
                
                if not is_valid:
                    error_summary = self.validator.error_handler.get_summary()
                    raise RuntimeError(f"Validation failed: {error_summary['error_count']} errors")
            
            # Save to file
            self._save_json(raw_data, output_path)
            
            # Generate reports
            self._generate_reports(raw_data, output_path)
            
            logger.info(f"Conversion completed successfully: {output_path}")
            return raw_data
            
        except Exception as e:
            self.error_handler.add_error(f"Conversion failed: {str(e)}")
            logger.error(f"Conversion failed: {str(e)}")
            raise
    
    def _save_json(self, data: Dict[str, Any], output_path: str) -> None:
        """Save data to JSON file."""
        logger.info(f"Saving JSON to: {output_path}")
        
        # Ensure output directory exists
        FileHandler.ensure_directory(output_path)
        
        # Backup existing file if it exists
        backup_path = FileHandler.backup_file(output_path)
        if backup_path:
            logger.info(f"Created backup: {backup_path}")
        
        # Save JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(
                data,
                f,
                indent=self.config.JSON_INDENT_SIZE if self.config.INDENT_JSON else None,
                sort_keys=self.config.SORT_KEYS,
                ensure_ascii=False
            )
        
        # Log file size
        file_size = FileHandler.get_file_size_mb(output_path)
        logger.info(f"JSON file saved ({file_size:.1f} MB)")
    
    def _generate_reports(self, data: Dict[str, Any], output_path: str) -> None:
        """Generate validation and summary reports."""
        output_dir = Path(output_path).parent
        
        # Generate validation report
        validation_report = self.validator.generate_validation_report(data)
        report_path = output_dir / "validation_report.txt"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(validation_report)
        
        logger.info(f"Validation report saved: {report_path}")
        
        # Generate summary statistics
        quality_metrics = self.validator.get_data_quality_metrics(data)
        parsing_summary = self.parser.get_parsing_summary()
        
        summary = {
            "conversion_summary": {
                "input_file": str(Path(self.config.INPUT_PDF_PATH).name),
                "output_file": str(Path(output_path).name),
                "total_cities": len(data),
                "data_quality": quality_metrics,
                "parsing_info": parsing_summary
            }
        }
        
        summary_path = output_dir / "conversion_summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, sort_keys=True)
        
        logger.info(f"Summary report saved: {summary_path}")
    
    def validate_existing_json(self, json_path: str) -> Dict[str, Any]:
        """
        Validate an existing JSON file.
        
        Args:
            json_path: Path to JSON file to validate
            
        Returns:
            Validation report
        """
        logger.info(f"Validating existing JSON: {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        validation_result = self.validator.validate_against_schema(data)
        quality_metrics = self.validator.get_data_quality_metrics(data)
        
        return {
            "validation_result": validation_result,
            "quality_metrics": quality_metrics
        }
    
    def get_conversion_summary(self) -> Dict[str, Any]:
        """Get summary of the last conversion process."""
        return {
            "parser_summary": self.parser.get_parsing_summary(),
            "validation_summary": self.validator.error_handler.get_summary(),
            "conversion_errors": self.error_handler.get_summary()
        }