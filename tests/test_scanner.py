"""Test DataMatrix scanner with real images."""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scanner import scan_datamatrix, DataMatrixDecoder, GS1Parser, normalize_gtin


# Expected results for test images
EXPECTED_RESULTS = {
    "photo_2026-03-15_23-24-55.jpg": {
        "gtin": "04607163091577",
        "serial": "5nf+.FSH8B%NW",
        "ai93": "0bBq"
    },
    "photo_2026-03-15_23-58-36.jpg": {
        "gtin": "04600605034156",
        "serial": "5%z6\"6",
        "ai93": "v2XL"
    },
    "photo_2026-03-15_23-59-53.jpg": {
        "gtin": "04607004891694",
        "serial": "59Dr%6",
        "ai93": "ytV7"
    }
}


def test_scanner():
    """Test scanner with images from tests/img folder."""
    img_dir = Path(__file__).parent / "img"
    
    # Find all jpg files
    jpg_files = sorted(img_dir.glob("*.jpg"))
    
    if not jpg_files:
        print("No test images found!")
        return
    
    print(f"Found {len(jpg_files)} test images\n")
    print("=" * 60)
    
    decoder = DataMatrixDecoder()
    parser = GS1Parser()
    
    results = []
    
    for jpg_path in jpg_files:
        print(f"\n[IMAGE] {jpg_path.name}")
        print("-" * 40)
        
        # Get expected results
        expected = EXPECTED_RESULTS.get(jpg_path.name, {})
        
        # Read image
        with open(jpg_path, "rb") as f:
            image_data = f.read()
        
        # Scan
        result = scan_datamatrix(image_data)
        
        print(f"\n[SCAN RESULT]")
        print(f"  Success: {result['success']}")
        
        if result['success']:
            print(f"  Raw data: {result['raw_data']}")
            print(f"  GTIN: {result['gtin']}")
            print(f"  Serial: {result['serial']}")
            print(f"  AI93 (crypto): {result.get('ai93', 'N/A')}")
            
            if result['error']:
                print(f"  Error: {result['error']}")
            
            # Verify against expected
            gtin_ok = result['gtin'] == expected.get('gtin')
            serial_ok = result['serial'] == expected.get('serial')
            
            print(f"\n  [VALIDATION]")
            print(f"    GTIN:   {'PASS' if gtin_ok else 'FAIL'} (expected: {expected.get('gtin')})")
            print(f"    Serial: {'PASS' if serial_ok else 'FAIL'} (expected: {expected.get('serial')})")
            
            test_passed = gtin_ok and serial_ok
        else:
            print(f"  Error: {result['error']}")
            test_passed = False
        
        results.append({
            'file': jpg_path.name,
            'success': result['success'],
            'passed': test_passed,
            'gtin': result['gtin'],
            'serial': result['serial']
        })
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    successful = sum(1 for r in results if r['success'])
    passed = sum(1 for r in results if r.get('passed', False))
    
    print(f"Total: {len(results)}, Decoded: {successful}, Passed: {passed}")
    
    for r in results:
        status = "[PASS]" if r.get('passed') else "[FAIL]"
        gtin = r['gtin'] or "N/A"
        serial = r['serial'] or "N/A"
        print(f"  {status} {r['file']}")
        print(f"         GTIN={gtin}, Serial={serial}")


def test_gs1_parser():
    """Test GS1 parser with known data strings."""
    print("\n" + "=" * 60)
    print("GS1 Parser Tests")
    print("=" * 60)
    
    test_cases = [
        # Format without parentheses
        ("0104607163091577215nf+.FSH8B%NW 930bBq", "04607163091577"),
        ("0104600605034156215%z6\"693v2XL", "04600605034156"),
        ("01046070048916942159Dr%693ytV7", "04607004891694"),
        # Format with parentheses (from zxing-cpp)
        ("(01)04607163091577(21)5nf+.FSH8B%NW(93)0bBq", "04607163091577"),
        ("(01)04600605034156(21)5%z6\"6(93)v2XL", "04600605034156"),
    ]
    
    parser = GS1Parser()
    
    for raw_data, expected_gtin in test_cases:
        print(f"\nInput: {raw_data[:40]}...")
        
        result = parser.parse(raw_data)
        
        print(f"  GTIN: {result['gtin']}")
        print(f"  Serial: {result['serial']}")
        print(f"  AI93: {result.get('ai93', 'N/A')}")
        
        gtin_match = result['gtin'] == expected_gtin
        print(f"  GTIN match: {'YES' if gtin_match else 'NO'}")


if __name__ == "__main__":
    print("DataMatrix Scanner Test Suite\n")
    
    # Test parser first
    test_gs1_parser()
    
    # Test with images
    test_scanner()
