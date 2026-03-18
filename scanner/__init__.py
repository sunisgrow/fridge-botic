"""Scanner module for DataMatrix code recognition.

This module provides:
- Image preprocessing for DataMatrix detection
- GS1 format parsing
- DataMatrix decoding using zxing-cpp
"""

from .image_preprocessing import (
    ImagePreprocessor,
    load_image,
    preprocess_for_decode,
    preprocess_pipeline
)
from .gs1_parser import (
    GS1Parser,
    GS1ParseError,
    parse_gs1,
    normalize_gtin,
    extract_gtin,
    extract_expiration_date
)
from .datamatrix_decoder import (
    DataMatrixDecoder,
    scan_datamatrix,
    scan_image,
    ScanError,
    NoCodeDetected,
    DecodeFailed
)

__all__ = [
    # Image preprocessing
    'ImagePreprocessor',
    'load_image',
    'preprocess_for_decode',
    'preprocess_pipeline',
    # GS1 parsing
    'GS1Parser',
    'GS1ParseError',
    'parse_gs1',
    'normalize_gtin',
    'extract_gtin',
    'extract_expiration_date',
    # Decoding
    'DataMatrixDecoder',
    'scan_datamatrix',
    'scan_image',
    'ScanError',
    'NoCodeDetected',
    'DecodeFailed'
]
