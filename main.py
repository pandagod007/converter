"""
Main entry point for MASTERFORMAT PDF to JSON converter.
"""

import argparse
import sys
import logging
from pathlib import Path
from typing import Optional

from pdf_to_json_converter import MasterFormatConverter
from config import Config

logger = logging.getLogger(__name__)

def setup_argument_parser() -> argparse.ArgumentParser:
    """Setup command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Convert MASTERFORMAT City Cost Indexes PDF to JSON format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py input.pdf
  python main.py input.pdf --output output.json
  python main.py input.pdf --output output.json --strict
  python main.py --validate existing_output.json
        """
    )
    
    parser.add_argument(
        'input_file',
        nargs='?',
        help='Input PDF file path'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Output JSON file path (default: masterformat_output.json)'
    )
    
    parser.add_argument(
        '--config', '-c',
        help='Configuration file path'
    )
    
    parser.add_argument(
        '--strict',
        action='store_true',
        help='Enable strict validation mode'
    )
    
    parser.add_argument(
        '--no-subdivisions',
        action='store_true',
        help='Disable subdivision extraction'
    )
    
    parser.add_argument(
        '--validate',
        help='Validate an existing JSON file instead of converting'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Set logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Don\'t create backup of existing output file'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='MASTERFORMAT Converter 1.0.0'
    )
    
    return parser

def load_config(config_path: Optional[str], args: argparse.Namespace) -> Config:
    """Load configuration from file and command line arguments."""
    if config_path:
        # Load from file (implement JSON config loading if needed)
        config = Config()
    else:
        # Load from environment and defaults
        config = Config.from_env()
    
    # Override with command line arguments
    if args.output:
        config.OUTPUT_JSON_PATH = args.output
    
    if args.strict:
        config.STRICT_VALIDATION = True
    
    if args.no_subdivisions:
        config.INCLUDE_SUBDIVISIONS = False
    
    config.LOG_LEVEL = args.log_level
    
    return config

def main() -> int:
    """Main entry point."""
    parser = setup_argument_parser()
    args = parser.parse_args()
    
    try:
        # Load configuration
        config = load_config(args.config, args)
        
        # Initialize converter
        converter = MasterFormatConverter(config)
        
        # Handle validation mode
        if args.validate:
            logger.info(f"Validating JSON file: {args.validate}")
            result = converter.validate_existing_json(args.validate)
            
            print("\nValidation Results:")
            print(f"Valid: {result['validation_result']['valid']}")
            print(f"Cities: {result['validation_result']['cities_valid']}/{result['validation_result']['cities_processed']}")
            print(f"Data Completeness: {result['quality_metrics']['data_completeness_percentage']:.1f}%")
            
            return 0 if result['validation_result']['valid'] else 1
        
        # Handle conversion mode
        if not args.input_file:
            parser.error("Input file is required for conversion mode")
        
        input_path = Path(args.input_file)
        if not input_path.exists():
            logger.error(f"Input file not found: {input_path}")
            return 1
        
        # Perform conversion
        logger.info(f"Converting {input_path} to JSON...")
        
        result_data = converter.convert_pdf_to_json(
            str(input_path),
            args.output
        )
        
        # Print summary
        print(f"\nConversion completed successfully!")
        print(f"Cities extracted: {len(result_data)}")
        print(f"Output file: {args.output or config.OUTPUT_JSON_PATH}")
        
        # Print conversion summary
        summary = converter.get_conversion_summary()
        if summary['conversion_errors']['error_count'] > 0:
            print(f"Errors encountered: {summary['conversion_errors']['error_count']}")
        
        if summary['conversion_errors']['warning_count'] > 0:
            print(f"Warnings: {summary['conversion_errors']['warning_count']}")
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Conversion interrupted by user")
        return 1
    
    except Exception as e:
        logger.error(f"Conversion failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())