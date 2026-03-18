"""Image preprocessing for DataMatrix scanning.

This module provides image preprocessing pipeline to improve
DataMatrix code detection and decoding accuracy.

Pipeline:
    image → grayscale → denoise → contrast → threshold → decode
"""

import logging
from typing import Optional, Tuple, List

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# Constants for preprocessing
MAX_DIMENSION = 2048
MIN_CODE_AREA = 500
DENOISE_D = 11
DENOISE_SIGMA_COLOR = 17
DENOISE_SIGMA_SPACE = 17
CLAHE_CLIP_LIMIT = 2.0
CLAHE_TILE_SIZE = (8, 8)
THRESHOLD_BLOCK_SIZE = 11
THRESHOLD_C = 2


def load_image(image_data: bytes) -> Optional[np.ndarray]:
    """
    Load image from binary data.

    Args:
        image_data: Image binary data (JPEG, PNG, etc.)

    Returns:
        OpenCV image array or None if failed
    """
    try:
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image is None:
            logger.error("Failed to decode image")
            return None
        return image
    except Exception as e:
        logger.error(f"Error loading image: {e}")
        return None


def resize_if_needed(image: np.ndarray, max_dimension: int = MAX_DIMENSION) -> np.ndarray:
    """
    Resize image if it exceeds max dimension.

    Args:
        image: Input image
        max_dimension: Maximum width or height

    Returns:
        Resized image if needed, original otherwise
    """
    h, w = image.shape[:2]
    if max(h, w) > max_dimension:
        scale = max_dimension / max(h, w)
        new_w = int(w * scale)
        new_h = int(h * scale)
        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        logger.debug(f"Resized image from {w}x{h} to {new_w}x{new_h}")
        return resized
    return image


def to_grayscale(image: np.ndarray) -> np.ndarray:
    """
    Convert image to grayscale.

    Args:
        image: Input BGR image

    Returns:
        Grayscale image
    """
    if len(image.shape) == 3:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return image


def denoise(image: np.ndarray) -> np.ndarray:
    """
    Apply bilateral filter to remove noise while preserving edges.

    Args:
        image: Grayscale image

    Returns:
        Denoised image
    """
    return cv2.bilateralFilter(
        image,
        d=DENOISE_D,
        sigmaColor=DENOISE_SIGMA_COLOR,
        sigmaSpace=DENOISE_SIGMA_SPACE
    )


def enhance_contrast(image: np.ndarray) -> np.ndarray:
    """
    Enhance contrast using CLAHE.

    CLAHE (Contrast Limited Adaptive Histogram Equalization) improves
    visibility of DataMatrix dots in poor lighting conditions.

    Args:
        image: Grayscale image

    Returns:
        Contrast-enhanced image
    """
    clahe = cv2.createCLAHE(
        clipLimit=CLAHE_CLIP_LIMIT,
        tileGridSize=CLAHE_TILE_SIZE
    )
    return clahe.apply(image)


def apply_adaptive_threshold(image: np.ndarray) -> np.ndarray:
    """
    Apply adaptive thresholding to create binary image.

    Args:
        image: Grayscale image

    Returns:
        Binary image
    """
    return cv2.adaptiveThreshold(
        image,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=THRESHOLD_BLOCK_SIZE,
        C=THRESHOLD_C
    )


def find_potential_codes(image: np.ndarray, min_area: int = MIN_CODE_AREA) -> List[Tuple[int, int, int, int]]:
    """
    Find potential DataMatrix code regions using contour detection.

    Args:
        image: Binary image
        min_area: Minimum contour area to consider

    Returns:
        List of bounding boxes (x, y, w, h) for potential codes
    """
    contours, _ = cv2.findContours(
        image,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    potential_codes = []

    for contour in contours:
        area = cv2.contourArea(contour)
        if area < min_area:
            continue

        x, y, w, h = cv2.boundingRect(contour)
        aspect_ratio = float(w) / h if h > 0 else 0

        # DataMatrix codes are roughly square
        if 0.7 < aspect_ratio < 1.4:
            potential_codes.append((x, y, w, h))

    logger.debug(f"Found {len(potential_codes)} potential DataMatrix regions")
    return potential_codes


def extract_region(image: np.ndarray, bbox: Tuple[int, int, int, int], padding: int = 10) -> np.ndarray:
    """
    Extract region from image with padding.

    Args:
        image: Source image
        bbox: Bounding box (x, y, w, h)
        padding: Padding around region

    Returns:
        Extracted region
    """
    x, y, w, h = bbox
    h_img, w_img = image.shape[:2]

    x1 = max(0, x - padding)
    y1 = max(0, y - padding)
    x2 = min(w_img, x + w + padding)
    y2 = min(h_img, y + h + padding)

    return image[y1:y2, x1:x2]


def preprocess_pipeline(image: np.ndarray) -> np.ndarray:
    """
    Full preprocessing pipeline.

    Args:
        image: Input BGR image

    Returns:
        Preprocessed binary image
    """
    # Resize if needed
    image = resize_if_needed(image)

    # Convert to grayscale
    gray = to_grayscale(image)

    # Denoise
    denoised = denoise(gray)

    # Enhance contrast
    enhanced = enhance_contrast(denoised)

    # Apply threshold
    binary = apply_adaptive_threshold(enhanced)

    return binary


def preprocess_for_decode(image: np.ndarray) -> np.ndarray:
    """
    Prepare image for DataMatrix decoding.

    This is a simpler pipeline optimized for zxing-cpp.

    Args:
        image: Input BGR image

    Returns:
        Preprocessed grayscale image
    """
    # Resize if needed
    image = resize_if_needed(image)

    # Convert to grayscale
    gray = to_grayscale(image)

    # Enhance contrast
    enhanced = enhance_contrast(gray)

    return enhanced


class ImagePreprocessor:
    """
    Image preprocessor for DataMatrix scanning.

    Provides methods for image preprocessing and region detection.
    """

    def __init__(
        self,
        max_dimension: int = MAX_DIMENSION,
        min_code_area: int = MIN_CODE_AREA
    ):
        """
        Initialize preprocessor.

        Args:
            max_dimension: Maximum image dimension
            min_code_area: Minimum code area to detect
        """
        self.max_dimension = max_dimension
        self.min_code_area = min_code_area

    def preprocess(self, image_data: bytes) -> Optional[np.ndarray]:
        """
        Load and preprocess image.

        Args:
            image_data: Image binary data

        Returns:
            Preprocessed image or None if failed
        """
        image = load_image(image_data)
        if image is None:
            return None

        return preprocess_for_decode(image)

    def find_code_regions(self, image: np.ndarray) -> List[np.ndarray]:
        """
        Find potential DataMatrix code regions.

        Args:
            image: Input image

        Returns:
            List of extracted regions
        """
        binary = preprocess_pipeline(image)
        bboxes = find_potential_codes(binary, self.min_code_area)

        regions = []
        for bbox in bboxes:
            region = extract_region(image, bbox)
            regions.append(region)

        return regions
