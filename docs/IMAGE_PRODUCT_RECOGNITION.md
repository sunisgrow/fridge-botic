# Image Product Recognition

Goal

Allow the bot to recognize products from a photo of packaging without scanning DataMatrix.

Example:

User sends photo of milk carton.

Bot response:

Detected product:
"Danone Milk 3.2%"

Confirm?

---

# Use Cases

Product without visible DataMatrix

Damaged barcode

Quick product addition

---

# Architecture

User Photo
↓
Bot receives image
↓
API /recognize_product
↓
Recognition Worker
↓
CNN Model
↓
Top predictions
↓
User confirmation

---

# Recognition Approaches

## Approach 1 — Logo + text recognition

Pipeline:

image
↓
object detection
↓
logo detection
↓
OCR text extraction
↓
product match

Tools:

OpenCV
Tesseract OCR

Pros

easy to implement

Cons

less accurate

---

## Approach 2 — Deep learning classification

Train CNN model to classify product packaging.

Models:

MobileNet
EfficientNet

Input

product image

Output

product class

---

# Training Dataset

Possible sources

Open product image datasets

Retail catalog images

User uploaded photos

Dataset structure

dataset/

milk/
milk1.jpg
milk2.jpg

cheese/
cheese1.jpg
cheese2.jpg

---

# Training Pipeline

images
↓
resize 224x224
↓
data augmentation
↓
train CNN
↓
export model

---

# Inference

image
↓
resize
↓
model prediction
↓
top 3 products

Example result

1 Milk 3.2%
2 Yogurt Strawberry
3 Kefir

---

# Bot Interaction

User sends photo.

Bot response

Detected product:

Milk 3.2%

Is this correct?

Yes / Choose other

---

# Future Improvements

multi-product detection

brand recognition

ingredient detection