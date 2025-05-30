"""
Constants and mappings for MASTERFORMAT PDF to JSON conversion.
"""

from typing import Dict, List, Tuple

# Division codes in exact order as they appear in the PDF
DIVISION_CODES: List[str] = [
    "015433",
    "0241, 31 - 34",
    "0310",
    "0320",
    "0330",
    "03",
    "04",
    "05",
    "06",
    "07",
    "08",
    "0920",
    "0950, 0980",
    "0960",
    "0970, 0990",
    "09",
    "COVERS",
    "21, 22, 23",
    "26, 27, 3370",
    "MF2018"
]

# Division descriptions in exact order
DIVISION_DESCRIPTIONS: List[str] = [
    "CONTRACTOR EQUIPMENT",
    "SITE & INFRASTRUCTURE, DEMOLITION",
    "Concrete Forming & Accessories",
    "Concrete Reinforcing",
    "Cast-in-Place Concrete",
    "CONCRETE",
    "MASONRY",
    "METALS",
    "WOOD, PLASTICS & COMPOSITES",
    "THERMAL & MOISTURE PROTECTION",
    "OPENINGS",
    "Plaster & Gypsum Board",
    "Ceilings & Acoustic Treatment",
    "Flooring",
    "Wall Finishes & Painting/Coating",
    "FINISHES",
    "DIVS. 10 - 14, 25, 28, 41, 43, 44, 46",
    "FIRE SUPPRESSION, PLUMBING & HVAC",
    "ELECTRICAL, COMMUNICATIONS & UTIL.",
    "WEIGHTED AVERAGE"
]

# Mapping of division codes to descriptions
DIVISION_MAPPING: Dict[str, str] = dict(zip(DIVISION_CODES, DIVISION_DESCRIPTIONS))

# Data type labels
DATA_TYPES: List[str] = ["MAT", "INST", "TOTAL"]

# Concrete subdivisions mapping
CONCRETE_SUBDIVISIONS: Dict[str, str] = {
    "0310": "Concrete Forming & Accessories",
    "0320": "Concrete Reinforcing", 
    "0330": "Cast-in-Place Concrete"
}

# Finishes subdivisions mapping
FINISHES_SUBDIVISIONS: Dict[str, str] = {
    "0920": "Plaster & Gypsum Board",
    "0950, 0980": "Ceilings & Acoustic Treatment",
    "0960": "Flooring",
    "0970, 0990": "Wall Finishes & Painting/Coating"
}

# Regular expressions
CITY_ZIP_PATTERN = r'^([A-Z\s\.\-&]+)\s+(\d{3}(?:\s*-\s*\d{3})?(?:\s*,\s*\d{3})*)$'
STATE_PATTERN = r'^[A-Z\s]{2,}$'
DATA_ROW_PATTERN = r'^(MAT\.|INST\.|TOTAL)\s+([\d\.\s]+)$'
NUMBER_PATTERN = r'\d+\.\d+'

# US States and territories
US_STATES: List[str] = [
    "ALABAMA", "ALASKA", "ARIZONA", "ARKANSAS", "CALIFORNIA", "COLORADO",
    "CONNECTICUT", "DELAWARE", "FLORIDA", "GEORGIA", "HAWAII", "IDAHO",
    "ILLINOIS", "INDIANA", "IOWA", "KANSAS", "KENTUCKY", "LOUISIANA",
    "MAINE", "MARYLAND", "MASSACHUSETTS", "MICHIGAN", "MINNESOTA",
    "MISSISSIPPI", "MISSOURI", "MONTANA", "NEBRASKA", "NEVADA",
    "NEW HAMPSHIRE", "NEW JERSEY", "NEW MEXICO", "NEW YORK",
    "NORTH CAROLINA", "NORTH DAKOTA", "OHIO", "OKLAHOMA", "OREGON",
    "PENNSYLVANIA", "RHODE ISLAND", "SOUTH CAROLINA", "SOUTH DAKOTA",
    "TENNESSEE", "TEXAS", "UTAH", "VERMONT", "VIRGINIA", "WASHINGTON",
    "WEST VIRGINIA", "WISCONSIN", "WYOMING", "PUERTO RICO", "GUAM"
]

# Logging configuration
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# File paths
DEFAULT_OUTPUT_PATH = 'masterformat_output.json'
DEFAULT_LOG_PATH = 'converter.log'

# Processing parameters
MAX_DIVISIONS = 20
EXPECTED_VALUES_PER_ROW = 20
MIN_CITY_NAME_LENGTH = 3
MAX_CITY_NAME_LENGTH = 50