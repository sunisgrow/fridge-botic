-- Database schema for Fridge Telegram Bot
-- Target DB: PostgreSQL
-- Version: 1.0

-- ============================================
-- USERS AND AUTHENTICATION
-- ============================================

CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username TEXT,
    first_name TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    timezone TEXT DEFAULT 'UTC',
    language_code TEXT DEFAULT 'ru'
);

COMMENT ON TABLE users IS 'Registered bot users';
COMMENT ON COLUMN users.telegram_id IS 'Unique Telegram user identifier';

-- ============================================
-- FRIDGES AND STORAGE
-- ============================================

CREATE TABLE fridges (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    name TEXT DEFAULT 'Main fridge',
    created_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE fridges IS 'User fridges - users can have multiple fridges';

CREATE TABLE fridge_zones (
    id BIGSERIAL PRIMARY KEY,
    fridge_id BIGINT REFERENCES fridges(id) ON DELETE CASCADE,
    name TEXT NOT NULL
);

COMMENT ON TABLE fridge_zones IS 'Storage zones within fridge: freezer, door, shelf, etc.';

-- ============================================
-- PRODUCT CATALOG
-- ============================================

CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    icon TEXT
);

COMMENT ON TABLE categories IS 'Product categories: Dairy, Meat, Vegetables, etc.';

-- Insert default categories
INSERT INTO categories (name, icon) VALUES
    ('Молочные продукты', '🥛'),
    ('Мясо', '🥩'),
    ('Рыба', '🐟'),
    ('Овощи', '🥬'),
    ('Фрукты', '🍎'),
    ('Напитки', '🥤'),
    ('Соусы', '🫗'),
    ('Заморозка', '🧊'),
    ('Хлеб', '🍞'),
    ('Снеки', '🍿'),
    ('Другое', '📦');

CREATE TABLE brands (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    country TEXT
);

COMMENT ON TABLE brands IS 'Product brands: Danone, Coca-Cola, etc.';

CREATE TABLE products (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    category_id INTEGER REFERENCES categories(id),
    brand_id INTEGER REFERENCES brands(id),
    default_shelf_life_days INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE products IS 'Product library - master catalog of products';

CREATE TABLE product_gtins (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT REFERENCES products(id) ON DELETE CASCADE,
    gtin VARCHAR(14) UNIQUE NOT NULL
);

COMMENT ON TABLE product_gtins IS 'GTIN codes linked to products - enables barcode lookup';

-- ============================================
-- FRIDGE CONTENTS
-- ============================================

CREATE TABLE fridge_items (
    id BIGSERIAL PRIMARY KEY,
    fridge_id BIGINT REFERENCES fridges(id) ON DELETE CASCADE,
    zone_id BIGINT REFERENCES fridge_zones(id),
    product_id BIGINT REFERENCES products(id),
    quantity INTEGER DEFAULT 1,
    added_at TIMESTAMP DEFAULT NOW(),
    expiration_date DATE,
    opened BOOLEAN DEFAULT FALSE,
    note TEXT
);

COMMENT ON TABLE fridge_items IS 'Items stored in user fridges';

-- ============================================
-- DATAMATRIX SCANNING
-- ============================================

CREATE TABLE datamatrix_codes (
    id BIGSERIAL PRIMARY KEY,
    gtin VARCHAR(14),
    serial TEXT,
    batch TEXT,
    expiration_date DATE,
    raw_code TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE datamatrix_codes IS 'Decoded DataMatrix codes from Chestny Znak system';

CREATE TABLE scan_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    datamatrix_id BIGINT REFERENCES datamatrix_codes(id),
    image_file_id TEXT,
    scanned_at TIMESTAMP DEFAULT NOW(),
    success BOOLEAN
);

COMMENT ON TABLE scan_logs IS 'Log of all scanning attempts';

-- ============================================
-- NOTIFICATIONS
-- ============================================

CREATE TABLE notification_settings (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    days_before INTEGER DEFAULT 3,
    enabled BOOLEAN DEFAULT TRUE,
    notification_time TIME DEFAULT '09:00:00'
);

COMMENT ON TABLE notification_settings IS 'User notification preferences';

CREATE TABLE notification_queue (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    fridge_item_id BIGINT REFERENCES fridge_items(id),
    notify_at TIMESTAMP,
    sent BOOLEAN DEFAULT FALSE,
    sent_at TIMESTAMP
);

COMMENT ON TABLE notification_queue IS 'Queue of pending notifications';

-- ============================================
-- RECIPES
-- ============================================

CREATE TABLE recipes (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    instructions TEXT,
    cooking_time_minutes INTEGER,
    servings INTEGER DEFAULT 2,
    source_url TEXT
);

COMMENT ON TABLE recipes IS 'Recipe database';

CREATE TABLE recipe_ingredients (
    id BIGSERIAL PRIMARY KEY,
    recipe_id BIGINT REFERENCES recipes(id) ON DELETE CASCADE,
    ingredient_name TEXT NOT NULL,
    quantity TEXT,
    is_optional BOOLEAN DEFAULT FALSE
);

COMMENT ON TABLE recipe_ingredients IS 'Ingredients required for recipes';

-- ============================================
-- SHOPPING LISTS
-- ============================================

CREATE TABLE shopping_lists (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    is_completed BOOLEAN DEFAULT FALSE
);

COMMENT ON TABLE shopping_lists IS 'Shopping lists';

CREATE TABLE shopping_list_items (
    id BIGSERIAL PRIMARY KEY,
    shopping_list_id BIGINT REFERENCES shopping_lists(id) ON DELETE CASCADE,
    product_name TEXT NOT NULL,
    quantity INTEGER DEFAULT 1,
    is_purchased BOOLEAN DEFAULT FALSE,
    fridge_item_id BIGINT REFERENCES fridge_items(id)
);

COMMENT ON TABLE shopping_list_items IS 'Items in shopping lists';

-- ============================================
-- CUSTOM PRODUCTS (User-defined)
-- ============================================

CREATE TABLE custom_products (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    name TEXT NOT NULL,
    category_id INTEGER REFERENCES categories(id),
    default_shelf_life_days INTEGER
);

COMMENT ON TABLE custom_products IS 'User-created custom products not in main catalog';

-- ============================================
-- ANALYTICS
-- ============================================

CREATE TABLE product_usage_stats (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    product_id BIGINT REFERENCES products(id),
    times_added INTEGER DEFAULT 0,
    times_expired INTEGER DEFAULT 0,
    times_used INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE product_usage_stats IS 'Statistics on product usage patterns';

-- ============================================
-- INDEXES
-- ============================================

-- GTIN lookup (critical for scan performance)
CREATE INDEX idx_gtin ON product_gtins(gtin);

-- Expiration date queries (for notifications)
CREATE INDEX idx_expiration ON fridge_items(expiration_date);

-- Fridge items by fridge
CREATE INDEX idx_fridge_items_fridge ON fridge_items(fridge_id);

-- Notification queue timing
CREATE INDEX idx_notification_time ON notification_queue(notify_at);

-- User by telegram_id
CREATE INDEX idx_users_telegram ON users(telegram_id);

-- Products by category
CREATE INDEX idx_products_category ON products(category_id);

-- Recipe ingredients by recipe
CREATE INDEX idx_recipe_ingredients_recipe ON recipe_ingredients(recipe_id);

-- Shopping list items
CREATE INDEX idx_shopping_items_list ON shopping_list_items(shopping_list_id);

-- ============================================
-- VIEWS
-- ============================================

-- View: Expiring items with user info
CREATE VIEW expiring_items_view AS
SELECT 
    fi.id as item_id,
    fi.expiration_date,
    fi.quantity,
    p.name as product_name,
    c.name as category_name,
    u.telegram_id,
    u.timezone
FROM fridge_items fi
JOIN products p ON fi.product_id = p.id
JOIN categories c ON p.category_id = c.id
JOIN fridges f ON fi.fridge_id = f.id
JOIN users u ON f.user_id = u.id
WHERE fi.expiration_date IS NOT NULL;

-- View: Fridge contents with details
CREATE VIEW fridge_contents_view AS
SELECT 
    fi.id as item_id,
    fi.quantity,
    fi.expiration_date,
    fi.added_at,
    fi.opened,
    p.name as product_name,
    p.default_shelf_life_days,
    c.name as category_name,
    c.icon as category_icon,
    b.name as brand_name,
    f.name as fridge_name,
    fz.name as zone_name
FROM fridge_items fi
JOIN products p ON fi.product_id = p.id
LEFT JOIN categories c ON p.category_id = c.id
LEFT JOIN brands b ON p.brand_id = b.id
JOIN fridges f ON fi.fridge_id = f.id
LEFT JOIN fridge_zones fz ON fi.zone_id = fz.id;

-- ============================================
-- FUNCTIONS
-- ============================================

-- Function: Calculate days until expiration
CREATE OR REPLACE FUNCTION days_until_expiry(exp_date DATE)
RETURNS INTEGER AS $$
BEGIN
    IF exp_date IS NULL THEN
        RETURN NULL;
    END IF;
    RETURN exp_date - CURRENT_DATE;
END;
$$ LANGUAGE plpgsql;

-- Function: Auto-create user fridge
CREATE OR REPLACE FUNCTION create_user_fridge()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO fridges (user_id, name)
    VALUES (NEW.id, 'Основной холодильник');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Create fridge for new user
CREATE TRIGGER trigger_create_fridge
    AFTER INSERT ON users
    FOR EACH ROW
    EXECUTE FUNCTION create_user_fridge();

-- Function: Update product usage stats
CREATE OR REPLACE FUNCTION update_product_stats()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO product_usage_stats (user_id, product_id, times_added, last_updated)
    SELECT f.user_id, NEW.product_id, 1, NOW()
    FROM fridges f WHERE f.id = NEW.fridge_id
    ON CONFLICT (user_id, product_id) 
    DO UPDATE SET 
        times_added = product_usage_stats.times_added + 1,
        last_updated = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Track product additions
CREATE TRIGGER trigger_product_stats
    AFTER INSERT ON fridge_items
    FOR EACH ROW
    EXECUTE FUNCTION update_product_stats();

-- ============================================
-- SAMPLE DATA
-- ============================================

-- Sample brands
INSERT INTO brands (name, country) VALUES
    ('Danone', 'France'),
    ('Простоквашино', 'Russia'),
    ('Coca-Cola', 'USA'),
    ('Домик в деревне', 'Russia'),
    ('Savushkin', 'Belarus'),
    ('Valio', 'Finland');

-- Sample products
INSERT INTO products (name, category_id, brand_id, default_shelf_life_days) VALUES
    ('Молоко 3.2%', 1, 2, 7),
    ('Йогурт клубничный', 1, 1, 14),
    ('Сыр гауда', 1, 6, 30),
    ('Куриное филе', 2, NULL, 3),
    ('Свиной стейк', 2, NULL, 2),
    ('Кола', 6, 3, 365),
    ('Творог 5%', 1, 2, 10),
    ('Сметана 20%', 1, 4, 14);

-- Sample GTINs
INSERT INTO product_gtins (product_id, gtin) VALUES
    (1, '04607062446630'),
    (2, '04005593999999'),
    (7, '04600012345678');