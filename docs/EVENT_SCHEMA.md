# Event Schema

Purpose

Define internal events used across the system.

Event-driven architecture allows workers and services
to react to system events asynchronously.

---

# Event Format

Each event contains:

event_type
timestamp
payload

Example

{
 "event_type": "product_scanned",
 "timestamp": "...",
 "payload": {...}
}

---

# Event Types

product_scanned

Triggered when product DataMatrix is decoded.

Payload

user_id
gtin
serial
expiration_date

---

product_added

Triggered when product added to fridge.

Payload

user_id
product_id
quantity

---

product_expiring

Triggered when expiration approaching.

Payload

user_id
product_id
days_left

---

product_expired

Triggered when product expired.

Payload

user_id
product_id

---

receipt_scanned

Triggered after receipt parsing.

Payload

user_id
products_list

---

photo_product_detected

Triggered when product recognized from image.

Payload

user_id
predicted_product
confidence

---

analytics_updated

Triggered when analytics aggregation completed.

Payload

date
stats_summary

---

# Event Transport

Events transmitted via Redis queue.

Workers subscribe to specific events.

---

# Example Flow

User scans product
↓
scan_worker decodes DataMatrix
↓
emit event product_scanned
↓
API creates fridge item
↓
emit event product_added
↓
analytics_worker updates statistics