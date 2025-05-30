"""
JSON output validation module for MASTERFORMAT converter.
"""

import logging
from typing import Dict, Any, List, Set, Optional
from constants import DIVISION_CODES, DIVISION_DESCRIPTIONS, DATA_TYPES
from utils import ErrorHandler

logger = logging.getLogger(__name__)

class JSONValidator:
    """Validator for JSON output structure and data integrity."""
    
    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode
        self.error_handler = ErrorHandler()
    
    def validate_output(self, data: Dict[str, Any]) -> bool:
        """
        Validate the complete JSON output structure and data.
        
        Args:
            data: The JSON data to validate
            
        Returns:
            True if validation passes, False otherwise
        """
        logger.info("Starting JSON output validation...")
        
        if not data:
            self.error_handler.add_error("Output data is empty")
            return False
        
        # Validate overall structure
        if not self._validate_structure(data):
            return False
        
        # Validate each city's data
        valid_cities = 0
        for city_key, city_data in data.items():
            if self._validate_city_data(city_key, city_data):
                valid_cities += 1
        
        logger.info(f"Validation completed. {valid_cities}/{len(data)} cities valid.")
        
        # In strict mode, all cities must be valid
        if self.strict_mode and valid_cities != len(data):
            self.error_handler.add_error(f"Strict validation failed: {len(data) - valid_cities} cities invalid")
            return False
        
        return True
    
    def _validate_structure(self, data: Dict[str, Any]) -> bool:
        """Validate the overall structure of the data."""
        if not isinstance(data, dict):
            self.error_handler.add_error("Root data must be a dictionary")
            return False
        
        # Check that we have city data
        if len(data) == 0:
            self.error_handler.add_error("No city data found")
            return False
        
        return True
    
    def _validate_city_data(self, city_key: str, city_data: Dict[str, Any]) -> bool:
        """Validate data for a single city."""
        if not isinstance(city_data, dict):
            self.error_handler.add_error(f"City data for {city_key} must be a dictionary")
            return False
        
        # Check that we have division data
        if len(city_data) == 0:
            self.error_handler.add_error(f"No division data found for city {city_key}")
            return False
        
        # Validate each division
        valid_divisions = 0
        for division_code, division_data in city_data.items():
            if self._validate_division_data(city_key, division_code, division_data):
                valid_divisions += 1
        
        # Check if we have the expected number of divisions
        expected_divisions = len(DIVISION_CODES)
        if valid_divisions < expected_divisions * 0.8:
             self.error_handler.add_warning(
                f"City {city_key} has only {valid_divisions}/{expected_divisions} valid divisions",
                {"city": city_key, "valid_divisions": valid_divisions}
            )
        
        return valid_divisions > 0
    
    def _validate_division_data(self, city_key: str, division_code: str, division_data: Dict[str, Any]) -> bool:
        """Validate data for a single division."""
        if not isinstance(division_data, dict):
            self.error_handler.add_error(
                f"Division data for {city_key}.{division_code} must be a dictionary"
            )
            return False
        
        # Check required fields
        if "division" not in division_data:
            self.error_handler.add_error(
                f"Missing 'division' field for {city_key}.{division_code}"
            )
            return False
        
        # Validate division description
        if not isinstance(division_data["division"], str):
            self.error_handler.add_error(
                f"Division description for {city_key}.{division_code} must be a string"
            )
            return False
        
        # Check for at least one data type (MAT, INST, or TOTAL)
        has_data = False
        for data_type in DATA_TYPES:
            if data_type in division_data:
                if self._validate_numeric_value(division_data[data_type], city_key, division_code, data_type):
                    has_data = True
        
        if not has_data:
            self.error_handler.add_warning(
                f"No valid data values found for {city_key}.{division_code}"
            )
        
        # Validate subdivisions if present
        if "subdivisions" in division_data:
            self._validate_subdivisions(city_key, division_code, division_data["subdivisions"])
        
        return True
    
    def _validate_numeric_value(self, value: Any, city_key: str, division_code: str, data_type: str) -> bool:
        """Validate a numeric value."""
        if value is None:
            return False
        
        if not isinstance(value, (int, float)):
            self.error_handler.add_error(
                f"Value for {city_key}.{division_code}.{data_type} must be numeric, got {type(value)}"
            )
            return False
        
        # Check for reasonable ranges (cost indexes typically 0-500)
        if value < 0 or value > 1000:
            self.error_handler.add_warning(
                f"Unusual value for {city_key}.{division_code}.{data_type}: {value}",
                {"city": city_key, "division": division_code, "data_type": data_type, "value": value}
            )
        
        return True
    
    def _validate_subdivisions(self, city_key: str, division_code: str, subdivisions: Dict[str, Any]) -> bool:
        """Validate subdivision data."""
        if not isinstance(subdivisions, dict):
            self.error_handler.add_error(
                f"Subdivisions for {city_key}.{division_code} must be a dictionary"
            )
            return False
        
        valid_subdivisions = 0
        for sub_code, sub_data in subdivisions.items():
            if self._validate_division_data(city_key, f"{division_code}.{sub_code}", sub_data):
                valid_subdivisions += 1
        
        return valid_subdivisions > 0
    
    def validate_against_schema(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate data against expected schema and return validation report.
        
        Args:
            data: The JSON data to validate
            
        Returns:
            Validation report with detailed results
        """
        report = {
            "valid": True,
            "cities_processed": 0,
            "cities_valid": 0,
            "divisions_processed": 0,
            "divisions_valid": 0,
            "missing_divisions": [],
            "data_quality_issues": [],
            "errors": [],
            "warnings": []
        }
        
        if not data:
            report["valid"] = False
            report["errors"].append("No data to validate")
            return report
        
        for city_key, city_data in data.items():
            report["cities_processed"] += 1
            
            if not isinstance(city_data, dict):
                report["errors"].append(f"Invalid city data structure for {city_key}")
                continue
            
            city_valid = True
            city_divisions = set()
            
            for division_code, division_data in city_data.items():
                report["divisions_processed"] += 1
                city_divisions.add(division_code)
                
                if self._validate_division_data(city_key, division_code, division_data):
                    report["divisions_valid"] += 1
                else:
                    city_valid = False
            
            # Check for missing divisions
            expected_divisions = set(DIVISION_CODES)
            missing = expected_divisions - city_divisions
            if missing:
                report["missing_divisions"].extend([f"{city_key}: {list(missing)}"])
                if len(missing) > len(expected_divisions) * 0.2:  # More than 20% missing
                    city_valid = False
            
            if city_valid:
                report["cities_valid"] += 1
        
        # Overall validation result
        if report["cities_valid"] < report["cities_processed"] * 0.8:  # Less than 80% valid
            report["valid"] = False
        
        # Add error handler results
        error_summary = self.error_handler.get_summary()
        report["errors"].extend([e["message"] for e in error_summary["errors"]])
        report["warnings"].extend([w["message"] for w in error_summary["warnings"]])
        
        return report
    
    def get_data_quality_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate data quality metrics."""
        metrics = {
            "total_cities": len(data),
            "total_divisions": 0,
            "complete_data_points": 0,
            "missing_data_points": 0,
            "data_completeness_percentage": 0.0,
            "cities_with_subdivisions": 0,
            "average_divisions_per_city": 0.0
        }
        
        if not data:
            return metrics
        
        total_possible_data_points = 0
        
        for city_data in data.values():
            if isinstance(city_data, dict):
                metrics["total_divisions"] += len(city_data)
                
                for division_code, division_data in city_data.items():
                    if isinstance(division_data, dict):
                        # Count data points for each division
                        for data_type in DATA_TYPES:
                            total_possible_data_points += 1
                            if data_type in division_data and division_data[data_type] is not None:
                                metrics["complete_data_points"] += 1
                            else:
                                metrics["missing_data_points"] += 1
                        
                        # Check for subdivisions
                        if "subdivisions" in division_data:
                            metrics["cities_with_subdivisions"] += 1
        
        # Calculate percentages
        if total_possible_data_points > 0:
            metrics["data_completeness_percentage"] = (
                metrics["complete_data_points"] / total_possible_data_points * 100
            )
        
        if metrics["total_cities"] > 0:
            metrics["average_divisions_per_city"] = metrics["total_divisions"] / metrics["total_cities"]
        
        return metrics
    
    def generate_validation_report(self, data: Dict[str, Any]) -> str:
        """Generate a human-readable validation report."""
        validation_result = self.validate_against_schema(data)
        quality_metrics = self.get_data_quality_metrics(data)
        
        report_lines = [
            "MASTERFORMAT JSON Validation Report",
            "=" * 40,
            "",
            f"Overall Validation: {'PASSED' if validation_result['valid'] else 'FAILED'}",
            "",
            "Summary Statistics:",
            f"  Cities Processed: {validation_result['cities_processed']}",
            f"  Cities Valid: {validation_result['cities_valid']}",
            f"  Divisions Processed: {validation_result['divisions_processed']}",
            f"  Divisions Valid: {validation_result['divisions_valid']}",
            "",
            "Data Quality Metrics:",
            f"  Data Completeness: {quality_metrics['data_completeness_percentage']:.1f}%",
            f"  Complete Data Points: {quality_metrics['complete_data_points']}",
            f"  Missing Data Points: {quality_metrics['missing_data_points']}",
            f"  Average Divisions per City: {quality_metrics['average_divisions_per_city']:.1f}",
            f"  Cities with Subdivisions: {quality_metrics['cities_with_subdivisions']}",
            ""
        ]
        
        if validation_result['missing_divisions']:
            report_lines.extend([
                "Missing Divisions:",
                *[f"  {missing}" for missing in validation_result['missing_divisions'][:10]],
                ""
            ])
        
        if validation_result['errors']:
            report_lines.extend([
                "Errors:",
                *[f"  {error}" for error in validation_result['errors'][:10]],
                ""
            ])
        
        if validation_result['warnings']:
            report_lines.extend([
                "Warnings:",
                *[f"  {warning}" for warning in validation_result['warnings'][:10]],
                ""
            ])
        
        return "\n".join(report_lines)