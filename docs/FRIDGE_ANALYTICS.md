# Fridge Analytics

Goal

Provide insights about food consumption and waste.

---

# Metrics

Products consumed

Products expired

Food waste volume

Purchase frequency

---

# Data Sources

fridge_items

expiration_date

removal_date

shopping_list_history

---

# Example Analytics

## Expired products

Top expired items

Milk
Yogurt
Salad

---

## Waste rate

Formula

expired_items / total_items

Example

expired = 10
total = 100

waste_rate = 10%

---

# Consumption statistics

Track how often product appears in fridge.

Example

Milk → every 5 days

Eggs → every 7 days

---

# Purchase prediction

Estimate when product will run out.

Algorithm

average consumption interval

Example

milk bought every 5 days

Prediction

buy again in 4 days

---

# Analytics Pipeline

fridge data
↓
analytics worker
↓
aggregation queries
↓
analytics tables

---

# Database Tables

product_usage_stats

product_id
times_added
times_expired
average_lifetime

---

# Bot Interaction

User command

/analytics

Bot response

Your food statistics

Food waste: 8%

Most wasted

Milk
Salad

Most consumed

Milk
Eggs

---

# Visualization

Charts

weekly consumption

monthly waste

top products

---

# Future Extensions

nutrition tracking

calorie analytics

diet recommendations