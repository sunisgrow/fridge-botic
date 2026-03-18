"""GS1 DataMatrix parser.

This module parses GS1 format strings extracted from DataMatrix codes.
GS1 format uses Application Identifiers (AI) to encode product information.

Common AIs:
    01 - GTIN (Global Trade Item Number)
    17 - Expiration date (YYMMDD)
    21 - Serial number
    10 - Batch number
    15 - Best before date
    91-99 - Custom data (e.g., crypto codes for "Честный знак")
"""

import logging
import re
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Valid Application Identifiers (2-digit)
VALID_AIS_2DIGIT = {
    '01', '02', '10', '11', '12', '13', '15', '16', '17',
    '20', '21', '22', '23', '24', '25', '30', '31', '32',
    '33', '34', '35', '36', '37', '39', '41', '42', '43',
    '44', '45', '46', '47', '48', '49', '50', '51', '52',
    '53', '54', '55', '56', '57', '58', '59', '60', '61',
    '62', '63', '64', '65', '66', '67', '68', '69', '70',
    '71', '72', '73', '74', '75', '76', '77', '78', '79',
    '80', '81', '82', '83', '84', '85', '86', '87', '88',
    '89', '90', '91', '92', '93', '94', '95', '96', '97',
    '98', '99'
}

# Fixed-length AIs (AI + length)
FIXED_LENGTH_AIS = {
    '01': 16,  # GTIN: AI(2) + 14 digits
    '02': 16,  # GTIN of contained trade items
    '15': 8,   # Best before date: AI(2) + 6 digits
    '17': 8,   # Expiration date: AI(2) + 6 digits
    '11': 8,   # Production date
    '12': 8,   # Due date
    '13': 8,   # Packaging date
    '16': 8,   # Sell by date
}


class GS1ParseError(Exception):
    """Exception raised when GS1 parsing fails."""
    pass


def _apply_ai_value(result: Dict[str, Any], ai: str, value: str) -> None:
    """
    Apply parsed AI value to result dict.
    
    Args:
        result: Result dictionary to update
        ai: Application Identifier
        value: Parsed value
    """
    if ai == '01':
        result['gtin'] = value
    elif ai == '17':
        result['expiration_date'] = parse_date_yymmdd(value)
    elif ai == '15':
        result['best_before'] = parse_date_yymmdd(value)
    elif ai == '11':
        result['production_date'] = parse_date_yymmdd(value)
    elif ai == '12':
        result['due_date'] = parse_date_yymmdd(value)
    elif ai == '13':
        result['packaging_date'] = parse_date_yymmdd(value)
    elif ai == '16':
        result['sell_by_date'] = parse_date_yymmdd(value)
    # For other AIs, store as-is
    result[f'ai{ai}'] = value


def _read_variable_field(data: str, start: int) -> tuple[str, int]:
    """
    Read variable-length field until next AI or end of string.
    
    Args:
        data: Data string
        start: Start position after AI
        
    Returns:
        Tuple of (field_value, characters_consumed)
    """
    if start >= len(data):
        return "", 0
    
    # Look for next 2-digit AI
    i = start
    while i < len(data) - 1:
        # Check if current position looks like an AI (2 digits followed by digit)
        if i + 2 < len(data) and data[i:i+2].isdigit():
            next_ai = data[i:i+2]
            if next_ai in VALID_AIS_2DIGIT:
                # Found next AI, return what we have before it
                value = data[start:i]
                return value, i - start
        
        # Also check for FNC1 (group separator)
        if data[i] == '\x1d':
            value = data[start:i]
            return value, i - start + 1
        
        i += 1
    
    # No next AI found, read to end
    value = data[start:]
    return value, len(value)


def parse_gs1(data: str) -> Dict[str, Any]:
    """
    Parse GS1 DataMatrix string.

    Supports two formats:
        1. Standard: 01046070048916942159Dr  (no brackets, fixed/variable fields)
        2. Brackets: (01)04607004891694(21)59Dr%6(93)ytV7

    Args:
        data: Raw decoded DataMatrix string

    Returns:
        Dictionary with parsed fields:
            - gtin: Global Trade Item Number (14 digits)
            - expiration_date: Expiration date (ISO format YYYY-MM-DD)
            - serial: Serial number
            - batch: Batch number
            - best_before: Best before date (ISO format)
            - raw: Original raw string
    """
    if not data:
        raise GS1ParseError("Empty data string")

    result: Dict[str, Any] = {
        'gtin': None,
        'expiration_date': None,
        'serial': None,
        'batch': None,
        'best_before': None,
        'raw': data
    }

    # Strip any leading/trailing whitespace
    clean_data = data.strip()

    # Try bracketed format first
    if '(' in clean_data:
        return _parse_bracketed_gs1(clean_data, result)

    # Fallback to standard format
    clean_data = clean_data.replace('\x1d', '')  # Remove FNC1
    return _parse_standard_gs1(clean_data, result)


def _parse_bracketed_gs1(data: str, result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse GS1 data in bracketed format.

    Format example: (01)04607004891694(21)59Dr%6(93)ytV7

    Algorithm:
    - Find all AI patterns: \\(\\d{2}\\)
    - For each AI, find next AI, extract data until then
    - Handle embedded brackets in value fields (e.g., serial number)

    Args:
        data: Data string with brackets
        result: Pre-initialized result dict

    Returns:
        Updated result dict
    """
    import re

    # Find all AI positions and lengths
    ai_pattern = r'\((\d{2})\)'
    matches = list(re.finditer(ai_pattern, data))

    if not matches:
        logger.warning("No valid AI patterns found in bracketed format")
        return result

    i = 0
    while i < len(matches):
        match = matches[i]
        ai = match.group(1)

        # End of this field: next AI or end of string
        if i + 1 < len(matches):
            end_pos = matches[i + 1].start()
        else:
            end_pos = len(data)

        # Extract field value between current AI and next AI
        field_start = match.end()
        field_value = data[field_start:end_pos]

        # Process variable-length AI fields (only known ones need parsing)
        if ai in FIXED_LENGTH_AIS:
            # Fixed-length: value length known, so we can just take it
            required_len = FIXED_LENGTH_AIS[ai] - 2  # -2 for AI itself
            if len(field_value) < required_len:
                logger.debug(f"Truncated fixed field for AI {ai}: got {len(field_value)}, need {required_len}")
                continue
            value = field_value[:required_len]
            _apply_ai_value(result, ai, value)
        elif ai == '10':
            # Batch number — variable, but might contain brackets
            # Stop at next AI or end of string — already done by parsing bounds
            result['batch'] = field_value
        elif ai == '21':
            # Serial number — variable, might contain brackets
            # In "Честный знак", серийный номер может быть: 59Dr%6 — без скобок внутри
            # Но в принципе, может содержать что угодно — просто берем как есть
            result['serial'] = field_value
        elif ai == '22':
            # Consumer variant
            result['consumer_variant'] = field_value
        elif ai == '37':
            # Count
            result['count'] = field_value
        elif ai in ('91', '92', '93', '94', '95', '96', '97', '98', '99'):
            # Custom fields — preserve as-is
            result[f'ai{ai}'] = field_value
        else:
            # Unknown AI, but known fixed length
            logger.debug(f"Unknown AI {ai} in bracketed format")

        i += 1

    return result


def _parse_standard_gs1(data: str, result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse GS1 data in standard (non-bracketed) format.

    Algorithm:
    - Scan for 2-digit AIs
    - For fixed-length AIs, consume exact number of characters
    - For variable-length AIs (10, 21, 22, 37), consume until next AI or FNC1

    Args:
        data: Cleaned data string (no FNC1)
        result: Pre-initialized result dict

    Returns:
        Updated result dict
    """
    i = 0
    while i < len(data):
        # Need at least 2 characters for AI
        if i + 1 >= len(data):
            break

        # Read AI (2 digits)
        ai = data[i:i + 2]

        if not ai.isdigit():
            # Skip non-digit characters
            i += 1
            continue

        if ai in FIXED_LENGTH_AIS:
            # Fixed-length field
            length = FIXED_LENGTH_AIS[ai]
            if i + length > len(data):
                logger.warning(f"Truncated field for AI {ai}")
                break

            value = data[i + 2:i + length]
            _apply_ai_value(result, ai, value)
            i += length

        elif ai == '10':
            # Batch number (variable length)
            value, consumed = _read_variable_field(data, i + 2)
            result['batch'] = value
            i += 2 + consumed

        elif ai == '21':
            # Serial number (variable length)
            value, consumed = _read_variable_field(data, i + 2)
            result['serial'] = value
            i += 2 + consumed

        elif ai == '22':
            # Consumer product variant (variable length)
            value, consumed = _read_variable_field(data, i + 2)
            result['consumer_variant'] = value
            i += 2 + consumed

        elif ai == '37':
            # Count of trade items (variable length)
            value, consumed = _read_variable_field(data, i + 2)
            result['count'] = value
            i += 2 + consumed

        elif ai in ('91', '92', '93', '94', '95', '96', '97', '98', '99'):
            # Custom/crypto fields (variable length)
            value, consumed = _read_variable_field(data, i + 2)
            result[f'ai{ai}'] = value
            i += 2 + consumed

        else:
            # Unknown AI - try to skip
            logger.debug(f"Unknown AI: {ai}")
            i += 2
            # Try to find next AI
            while i < len(data) - 1:
                if data[i:i + 2].isdigit():
                    potential_ai = data[i:i + 2]
                    if potential_ai in VALID_AIS_2DIGIT:
                        break
                i += 1

    return result


# ... существующий код ...


def parse_date_yymmdd(date_str: str) -> Optional[str]:
    """
    Parse YYMMDD date format to ISO date.

    Args:
        date_str: Date string in YYMMDD format

    Returns:
        ISO date string (YYYY-MM-DD) or None if invalid
    """
    if not date_str or len(date_str) != 6:
        logger.warning(f"Invalid date format: {date_str}")
        return None

    try:
        # Parse YYMMDD
        year = int(date_str[0:2])
        month = int(date_str[2:4])
        day = int(date_str[4:6])

        # Handle year (assume 2000-2099 for years 00-99)
        full_year = 2000 + year

        # Validate date
        date = datetime(full_year, month, day)
        return date.strftime('%Y-%m-%d')

    except (ValueError, IndexError) as e:
        logger.warning(f"Failed to parse date '{date_str}': {e}")
        return None


def normalize_gtin(gtin: str) -> str:
    """
    Normalize GTIN to 14 digits (add leading zeros if needed).

    Args:
        gtin: GTIN string (8, 12, 13, or 14 digits)

    Returns:
        14-digit GTIN string
    """
    if not gtin:
        return ""
    
    # Remove any non-digit characters
    gtin = re.sub(r'\D', '', gtin)
    
    # Pad to 14 digits
    if len(gtin) < 14:
        gtin = gtin.zfill(14)
    
    return gtin


def extract_gtin(data: str) -> Optional[str]:
    """
    Extract GTIN from GS1 data string.

    Args:
        data: GS1 data string

    Returns:
        GTIN string or None if not found
    """
    parsed = parse_gs1(data)
    return parsed.get('gtin')


def extract_expiration_date(data: str) -> Optional[str]:
    """
    Extract expiration date from GS1 data string.

    Args:
        data: GS1 data string

    Returns:
        ISO date string or None if not found
    """
    parsed = parse_gs1(data)
    return parsed.get('expiration_date')


class GS1Parser:
    """
    GS1 DataMatrix parser class.
    
    Provides a class-based interface for parsing GS1 format strings.
    """
    
    def __init__(self):
        """Initialize GS1 parser."""
        pass
    
    def parse(self, data: str) -> Dict[str, Any]:
        """
        Parse GS1 DataMatrix string.
        
        Args:
            data: Raw decoded DataMatrix string
            
        Returns:
            Dictionary with parsed fields
        """
        return parse_gs1(data)
    
    def normalize_gtin(self, gtin: str) -> str:
        """
        Normalize GTIN to 14 digits.
        
        Args:
            gtin: GTIN string
            
        Returns:
            14-digit GTIN string
        """
        return normalize_gtin(gtin)
    
    def extract_gtin(self, data: str) -> Optional[str]:
        """
        Extract GTIN from data string.
        
        Args:
            data: GS1 data string
            
        Returns:
            GTIN string or None
        """
        return extract_gtin(data)
    
    def extract_expiration_date(self, data: str) -> Optional[str]:
        """
        Extract expiration date from data string.
        
        Args:
            data: GS1 data string
            
        Returns:
            ISO date string or None
        """
        return extract_expiration_date(data)