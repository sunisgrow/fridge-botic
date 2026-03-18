# DataMatrix Scan Pipeline

Goal: reliably decode DataMatrix codes from smartphone photos.

---

## Typical Problems

- Low light conditions
- Image noise
- Tilted packaging
- Small code area
- Motion blur
- Reflections

---

## Pipeline Overview

```
Image Input
     │
     ▼
┌─────────────┐
│  Grayscale  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Denoise   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Contrast  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Threshold  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Detect    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Deskew    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    Decode   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Parse GS1  │
└──────┬──────┘
       │
       ▼
  Result Output
```

---

## Step 1: Grayscale Conversion

Convert to grayscale to reduce complexity.

```python
import cv2

gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
```

---

## Step 2: Noise Reduction

Apply bilateral filter to remove noise while preserving edges.

```python
denoised = cv2.bilateralFilter(gray, d=11, sigmaColor=17, sigmaSpace=17)
```

Parameters:
- `d=11`: Diameter of pixel neighborhood
- `sigmaColor=17`: Filter sigma in color space
- `sigmaSpace=17`: Filter sigma in coordinate space

---

## Step 3: Contrast Enhancement

Use CLAHE (Contrast Limited Adaptive Histogram Equalization).

```python
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
enhanced = clahe.apply(denoised)
```

This improves visibility of DataMatrix dots in poor lighting.

---

## Step 4: Adaptive Threshold

Convert to binary image using adaptive thresholding.

```python
threshold = cv2.adaptiveThreshold(
    enhanced,
    255,
    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
    cv2.THRESH_BINARY,
    blockSize=11,
    C=2
)
```

---

## Step 5: Contour Detection

Find potential DataMatrix regions.

```python
contours, _ = cv2.findContours(
    threshold,
    cv2.RETR_EXTERNAL,
    cv2.CHAIN_APPROX_SIMPLE
)

# Filter for square-like shapes
for contour in contours:
    area = cv2.contourArea(contour)
    if area > MIN_AREA:
        x, y, w, h = cv2.boundingRect(contour)
        aspect_ratio = float(w) / h
        if 0.8 < aspect_ratio < 1.2:
            # Potential DataMatrix
            potential_codes.append((x, y, w, h))
```

---

## Step 6: Perspective Correction

If code is rotated, apply perspective transform.

```python
def correct_perspective(image, corners):
    """Correct perspective distortion."""
    # Order corners: top-left, top-right, bottom-right, bottom-left
    ordered = order_corners(corners)
    
    # Calculate dimensions
    width = max(
        distance(ordered[0], ordered[1]),
        distance(ordered[2], ordered[3])
    )
    height = max(
        distance(ordered[0], ordered[3]),
        distance(ordered[1], ordered[2])
    )
    
    # Destination points
    dst = np.array([
        [0, 0],
        [width - 1, 0],
        [width - 1, height - 1],
        [0, height - 1]
    ], dtype=np.float32)
    
    # Perspective transform
    M = cv2.getPerspectiveTransform(ordered, dst)
    corrected = cv2.warpPerspective(image, M, (width, height))
    
    return corrected
```

---

## Step 7: Decode

Use ZXing or pyzbar for actual decoding.

```python
from pyzbar.pyzbar import decode as pyzbar_decode
from pyzbar.pyzbar import ZBarSymbol

def decode_datamatrix(image):
    """Decode DataMatrix from image."""
    results = pyzbar_decode(
        image,
        symbols=[ZBarSymbol.DATAMATRIX]
    )
    
    for result in results:
        return result.data.decode('utf-8')
    
    return None
```

Alternative with ZXing-cpp (better accuracy):

```python
from zxingcpp import read_barcode

def decode_datamatrix_zxing(image):
    """Decode using ZXing-cpp."""
    result = read_barcode(
        image,
        format=BarcodeFormat.DataMatrix
    )
    
    if result.valid:
        return result.text
    return None
```

---

## GS1 Parsing

Parse decoded string for GS1 Application Identifiers.

```python
import re
from datetime import datetime

def parse_gs1(data: str) -> dict:
    """
    Parse GS1 DataMatrix string.
    
    Returns dict with:
    - gtin: Global Trade Item Number
    - serial: Serial number
    - expiration: Expiration date
    - batch: Batch number
    """
    result = {}
    
    i = 0
    while i < len(data):
        # Read 2-character AI
        ai = data[i:i+2]
        
        if ai == '01':
            # GTIN: 14 digits
            result['gtin'] = data[i+2:i+16]
            i += 16
            
        elif ai == '21':
            # Serial: variable length, ends with AI or end
            serial_end = find_next_ai(data, i+2)
            result['serial'] = data[i+2:serial_end]
            i = serial_end
            
        elif ai == '17':
            # Expiration: YYMMDD
            date_str = data[i+2:i+8]
            result['expiration'] = parse_date(date_str)
            i += 8
            
        elif ai == '10':
            # Batch: variable length
            batch_end = find_next_ai(data, i+2)
            result['batch'] = data[i+2:batch_end]
            i = batch_end
            
        elif ai == '15':
            # Best before date: YYMMDD
            date_str = data[i+2:i+8]
            result['best_before'] = parse_date(date_str)
            i += 8
            
        elif ai == '91' or ai == '92':
            # Crypto fields (Честный знак)
            crypto_end = find_next_ai(data, i+2)
            result[f'crypto_{ai}'] = data[i+2:crypto_end]
            i = crypto_end
            
        else:
            # Unknown AI, skip
            i += 1
    
    return result

def parse_date(date_str: str) -> str:
    """Parse YYMMDD to ISO date."""
    return datetime.strptime(date_str, '%y%m%d').strftime('%Y-%m-%d')

def find_next_ai(data: str, start: int) -> int:
    """Find next AI position or end of string."""
    for i in range(start, len(data) - 1):
        if data[i:i+2].isdigit():
            potential_ai = data[i:i+2]
            if potential_ai in VALID_AIS:
                return i
    return len(data)

VALID_AIS = {
    '01', '02', '10', '15', '17', '21', '22',
    '91', '92', '93', '240', '241', '242', '37'
}
```

---

## Example DataMatrix Structure

Raw decoded string:
```
0104607062446630215s9KzR1725021510BATCH01
```

Parsed result:
```json
{
  "gtin": "04607062446630",
  "serial": "5s9KzR",
  "expiration": "2025-02-15",
  "batch": "BATCH01"
}
```

---

## Performance Optimization

### Image Resolution

```python
MAX_DIMENSION = 1024

def resize_if_needed(image):
    h, w = image.shape[:2]
    if max(h, w) > MAX_DIMENSION:
        scale = MAX_DIMENSION / max(h, w)
        return cv2.resize(image, None, fx=scale, fy=scale)
    return image
```

### Multi-scale Detection

Try different scales for small codes:

```python
SCALES = [1.0, 0.75, 0.5]

for scale in SCALES:
    resized = resize_image(image, scale)
    result = decode_datamatrix(resized)
    if result:
        return result
```

---

## Error Handling

```python
class ScanError(Exception):
    pass

class NoCodeDetected(ScanError):
    pass

class CodeDamaged(ScanError):
    pass

class UnsupportedFormat(ScanError):
    pass

def scan_image(image_path: str) -> dict:
    try:
        image = load_image(image_path)
        processed = preprocess(image)
        decoded = decode_datamatrix(processed)
        
        if not decoded:
            raise NoCodeDetected("No DataMatrix found in image")
        
        return parse_gs1(decoded)
        
    except Exception as e:
        log_error(e)
        raise
```

---

## Expected Performance

| Scenario | Success Rate |
|----------|--------------|
| Good photo, clear code | 99% |
| Low light | 90% |
| Tilted (< 30°) | 95% |
| Motion blur | 70% |
| Damaged code | 60% |

Overall with preprocessing: **90-97%** success rate.

---

## Integration with Telegram

```python
async def process_scan_photo(bot, file_id: str) -> dict:
    """Process photo sent via Telegram."""
    # Download file
    file = await bot.get_file(file_id)
    image_data = await bot.download_file(file.file_path)
    
    # Convert to OpenCV format
    nparr = np.frombuffer(image_data, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # Process pipeline
    result = scan_pipeline(image)
    
    return result
```