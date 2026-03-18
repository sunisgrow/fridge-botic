# Receipt Scanner

Goal

Allow users to add products by scanning a grocery receipt.

Example:

User sends photo of receipt.

Bot extracts product list.

Products added to fridge.

---

# Architecture

User photo
↓
Bot
↓
API /scan_receipt
↓
Receipt Worker
↓
OCR
↓
Text parser
↓
Product matching

---

# Pipeline

image
↓
grayscale
↓
noise removal
↓
text detection
↓
OCR
↓
line parsing
↓
product extraction

---

# OCR

Recommended engines

Tesseract OCR

Cloud OCR APIs (optional)

---

# Receipt Structure Example

MILK 3.2% 1.99
CHEESE GAUDA 4.50
EGGS 10PCS 2.20

---

# Parsing Algorithm

OCR text
↓
split lines
↓
detect product names
↓
remove prices
↓
normalize text

---

# Example

Input

"Milk 3.2% 1.99"

Output

product_name = "Milk"

---

# Product Matching

Match OCR name with product database.

Methods

exact match

fuzzy search

example

"Milk 3.2%" → "Milk"

---

# Bot Interaction

User sends receipt.

Bot response

Detected products

Milk
Cheese
Eggs

Add to fridge?

Yes / Edit

---

# Challenges

receipt image quality

different store formats

OCR mistakes

---

# Improvements

train custom receipt parser

store-specific templates

line-item ML classifier