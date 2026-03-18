# API Contracts

Purpose

Define all backend API endpoints.

All routers must follow these contracts.

---

# Users API

GET /users/me

Response

user profile

---

# Products API

GET /products/search

Parameters

query

Response

list of products

---

GET /products/{id}

Return product details.

---

# Fridge API

GET /fridge/items

Return all user fridge items.

---

POST /fridge/items

Add product to fridge.

Payload

product_id
quantity
expiration_date

---

DELETE /fridge/items/{id}

Remove item from fridge.

---

# Scan API

POST /scan/datamatrix

Upload image containing DataMatrix code.

Response

decoded product data

---

POST /scan/receipt

Upload receipt image.

Response

detected products

---

POST /scan/product_photo

Upload product photo.

Response

recognized product candidates

---

# Recipes API

GET /recipes/suggestions

Return recipes based on fridge content.

---

GET /recipes/{id}

Return recipe details.

---

# Shopping API

GET /shopping/list

Return active shopping list.

---

POST /shopping/generate

Generate list based on fridge and recipes.

---

# Analytics API

GET /analytics/summary

Return user food statistics.

---

GET /analytics/waste

Return food waste report.

---

GET /analytics/consumption

Return consumption statistics.