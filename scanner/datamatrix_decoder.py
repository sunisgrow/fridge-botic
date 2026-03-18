"""DataMatrix decoder.

This module provides DataMatrix code decoding functionality.
Uses zxing-cpp for high-accuracy decoding.
"""

import logging
from typing import Optional, Dict, Any

import cv2
import numpy as np

try:
    from zxingcpp import read_barcode, BarcodeFormat
    ZXING_AVAILABLE = True
except ImportError:
    ZXING_AVAILABLE = False
    logging.warning("zxing-cpp not available, DataMatrix decoding will be limited")

from .image_preprocessing import (
    load_image,
    preprocess_for_decode,
    preprocess_pipeline,
    find_potential_codes,
    extract_region
)
from .gs1_parser import parse_gs1, GS1ParseError

logger = logging.getLogger(__name__)

# Multi-scale factors for detection
DETECTION_SCALES = [1.0, 0.75, 0.5]


class ScanError(Exception):
    """Base exception for scan errors."""
    pass


class NoCodeDetected(ScanError):
    """No DataMatrix code found in image."""
    pass


class CodeDamaged(ScanError):
    """DataMatrix code is damaged or unreadable."""
    pass


class DecodeFailed(ScanError):
    """Failed to decode DataMatrix."""
    pass


def decode_datamatrix(image: np.ndarray) -> Optional[str]:
    """
    Decode DataMatrix code from image.

    Args:
        image: OpenCV image array (grayscale or BGR)

    Returns:
        Decoded string or None if failed
    """
    if not ZXING_AVAILABLE:
        logger.error("zxing-cpp not available")
        return None

    # Ensure grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    try:
        result = read_barcode(
            gray,
            formats=BarcodeFormat.DataMatrix,
            try_rotate=True
        )

        if result:
            return result.text

    except Exception as e:
        logger.debug(f"zxing-cpp decode failed: {e}")

    return None


def decode_with_preprocessing(image: np.ndarray) -> Optional[str]:
    """
    Decode DataMatrix with preprocessing pipeline.

    Tries multiple preprocessing strategies:
    1. Direct decode
    2. Enhanced contrast decode
    3. Binary threshold decode
    4. Multi-scale decode

    Args:
        image: OpenCV image array

    Returns:
        Decoded string or None if failed
    """
    # Strategy 1: Direct decode
    result = decode_datamatrix(image)
    if result:
        logger.debug("Decoded with direct strategy")
        return result

    # Strategy 2: Enhanced contrast
    enhanced = preprocess_for_decode(image)
    result = decode_datamatrix(enhanced)
    if result:
        logger.debug("Decoded with enhanced contrast strategy")
        return result

    # Strategy 3: Binary threshold
    binary = preprocess_pipeline(image)
    result = decode_datamatrix(binary)
    if result:
        logger.debug("Decoded with binary threshold strategy")
        return result

    # Strategy 4: Multi-scale
    for scale in DETECTION_SCALES[1:]:  # Skip 1.0, already tried
        h, w = image.shape[:2]
        new_w = int(w * scale)
        new_h = int(h * scale)

        resized = cv2.resize(image, (new_w, new_h))
        result = decode_datamatrix(resized)

        if result:
            logger.debug(f"Decoded with scale {scale}")
            return result

    # Strategy 5: Region-based
    regions = find_potential_codes(binary, min_area=500)
    for region_bbox in regions:
        region = extract_region(image, region_bbox)
        result = decode_datamatrix(region)
        if result:
            logger.debug("Decoded from extracted region")
            return result

    return None


def scan_image(image_data: bytes) -> Dict[str, Any]:
    """
    Scan image for DataMatrix code and parse GS1 data.

    Full pipeline:
        image → preprocess → decode → parse GS1 → return result

    Args:
        image_data: Image binary data

    Returns:
        Dictionary with:
            - success: bool
            - raw_data: Optional[str] - raw decoded string
            - gtin: Optional[str] - 14-digit GTIN
            - expiration_date: Optional[str] - ISO date
            - serial: Optional[str] - serial number
            - batch: Optional[str] - batch number
            - error: Optional[str] - error message

    Raises:
        NoCodeDetected: If no DataMatrix code found
        DecodeFailed: If decoding fails
    """
    # Load image
    image = load_image(image_data)
    if image is None:
        raise DecodeFailed("Failed to load image")

    # Decode
    raw_data = decode_with_preprocessing(image)

    if not raw_data:
        raise NoCodeDetected("No DataMatrix code found in image")

    # Parse GS1
    try:
        parsed = parse_gs1(raw_data)

        return {
            'success': True,
            'raw_data': raw_data,
            'gtin': parsed.get('gtin'),
            'expiration_date': parsed.get('expiration_date'),
            'serial': parsed.get('serial'),
            'batch': parsed.get('batch'),
            'best_before': parsed.get('best_before'),
            'ai93': parsed.get('ai93'),
            'error': None
        }

    except GS1ParseError as e:
        logger.warning(f"GS1 parse error: {e}")
        # Return raw data even if parsing failed
        return {
            'success': True,
            'raw_data': raw_data,
            'gtin': None,
            'expiration_date': None,
            'serial': None,
            'batch': None,
            'best_before': None,
            'ai93': None,
            'error': f"GS1 parse error: {e}"
        }


class DataMatrixDecoder:
    """
    DataMatrix decoder class.

    Provides methods for decoding DataMatrix codes from images.
    """

    def __init__(self, use_preprocessing: bool = True):
        """
        Initialize decoder.

        Args:
            use_preprocessing: Whether to use preprocessing pipeline
        """
        self.use_preprocessing = use_preprocessing

    def decode(self, image: np.ndarray) -> Optional[str]:
        """
        Decode DataMatrix from image.

        Args:
            image: OpenCV image array

        Returns:
            Decoded string or None
        """
        if self.use_preprocessing:
            return decode_with_preprocessing(image)
        return decode_datamatrix(image)

    def scan(self, image_data: bytes) -> Dict[str, Any]:
        """
        Scan image for DataMatrix code.

        Args:
            image_data: Image binary data

        Returns:
            Scan result dictionary
        """
        return scan_image(image_data)

    def is_available(self) -> bool:
        """Check if decoder is available."""
        return ZXING_AVAILABLE


def scan_datamatrix(image_data: bytes) -> Dict[str, Any]:
    """
    Convenience function for scanning DataMatrix.

    Args:
        image_data: Image binary data

    Returns:
        Scan result dictionary
    """
    try:
        return scan_image(image_data)
    except ScanError as e:
        return {
            'success': False,
            'raw_data': None,
            'gtin': None,
            'expiration_date': None,
            'serial': None,
            'batch': None,
            'best_before': None,
            'ai93': None,
            'error': str(e)
        }
