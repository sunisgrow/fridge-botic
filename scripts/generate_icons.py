#!/usr/bin/env python3
"""Generate placeholder icons for the scanner webapp."""

import base64
import struct
import zlib

def create_simple_png(width, height, color=(33, 150, 243)):
    """Create a simple solid color PNG."""
    def crc32(data):
        return zlib.crc32(data) & 0xffffffff
    
    # PNG signature
    signature = b'\x89PNG\r\n\x1a\n'
    
    # IHDR chunk
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    ihdr_crc = crc32(b'IHDR' + ihdr_data)
    ihdr = struct.pack('>I', 13) + b'IHDR' + ihdr_data + struct.pack('>I', ihdr_crc)
    
    # IDAT chunk (raw image data)
    raw_data = b''
    for y in range(height):
        raw_data += b'\x00'  # filter type
        for x in range(width):
            raw_data += bytes(color)
    
    compressed = zlib.compress(raw_data, 9)
    idat_crc = crc32(b'IDAT' + compressed)
    idat = struct.pack('>I', len(compressed)) + b'IDAT' + compressed + struct.pack('>I', idat_crc)
    
    # IEND chunk
    iend_crc = crc32(b'IEND')
    iend = struct.pack('>I', 0) + b'IEND' + struct.pack('>I', iend_crc)
    
    return signature + ihdr + idat + iend

# Create icons
with open('webapp/icon-192.png', 'wb') as f:
    f.write(create_simple_png(192, 192))

with open('webapp/icon-512.png', 'wb') as f:
    f.write(create_simple_png(512, 512))

print("Icons created successfully!")
