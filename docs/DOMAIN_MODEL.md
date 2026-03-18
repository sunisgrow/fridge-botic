# Domain Model

Purpose

Define the core domain entities used across the entire system.

All database models, API schemas and services must derive from this model.

---

# Core Entities

User

Represents Telegram user.

Fields

id
telegram_id
username
created_at

Relations

user has many fridge_items
user has many shopping_lists

---

Product

Represents product in global catalog.

Fields

id
gtin
name
brand
category
image_url
weight
ingredients

Relations

product used in fridge_items

---

Brand

Represents manufacturer brand.

Fields

id
name

---

Category

Represents product category.

Examples

Dairy
Meat
Vegetables
Fruits
Drinks
Frozen food

Fields

id
name
parent_category_id

---

FridgeItem

Represents product stored in user's fridge.

Fields

id
user_id
product_id
quantity
expiration_date
added_at

Relations

belongs to user
belongs to product

---

Receipt

Represents scanned receipt.

Fields

id
user_id
store_name
scan_date

Relations

receipt has many receipt_items

---

ReceiptItem

Represents product detected on receipt.

Fields

id
receipt_id
product_name
price
quantity

---

Recipe

Represents cooking recipe.

Fields

id
name
instructions
calories

Relations

recipe has many recipe_ingredients

---

RecipeIngredient

Fields

id
recipe_id
ingredient_name
quantity

---

ShoppingList

Fields

id
user_id
created_at

Relations

shopping_list has many shopping_items

---

ShoppingItem

Fields

id
shopping_list_id
product_name
quantity
status

status values

pending
purchased

---

AnalyticsStats

Aggregated analytics data.

Fields

id
product_id
times_added
times_expired
average_lifetime