# Telegram Bot Dialog Map

Purpose

Define all Telegram bot user interaction flows.

---

# Main Menu

Buttons

Add Product

Scan Product

My Fridge

Recipes

Shopping List

Analytics

Settings

---

# Flow: Add Product Manually

User presses

Add Product

Bot asks

Enter product name

User sends name

Bot searches product catalog

Bot shows suggestions

User selects product

Bot asks

Expiration date?

Bot saves item

---

# Flow: Scan Product

User presses

Scan Product

Bot asks

Send product photo or barcode

User sends image

Bot processes scan

Bot shows detected product

User confirms

Product added to fridge

---

# Flow: View Fridge

User presses

My Fridge

Bot shows list

Milk — expires in 2 days
Cheese — expires in 5 days

---

# Flow: Expiration Alerts

Background worker detects expiring product.

Bot sends notification

"Milk expires tomorrow"

Buttons

Mark consumed
Extend expiration

---

# Flow: Recipes

User presses

Recipes

Bot analyzes fridge

Bot suggests

Omelette
Pasta
Salad

---

# Flow: Shopping List

User presses

Shopping List

Bot shows current list.

User can:

add item
mark purchased

---

# Flow: Receipt Scan

User sends receipt photo.

Bot detects products.

Bot asks confirmation.

Products added to fridge.

---

# Flow: Analytics

User presses

Analytics

Bot shows statistics

Food waste: 6%

Most used products

Milk
Eggs
Bread

---

# Flow: Settings

User can configure

notification time

measurement units

language