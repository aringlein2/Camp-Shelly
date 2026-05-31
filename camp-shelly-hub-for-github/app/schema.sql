-- Camp Shelly Hub schema (SQLite)

CREATE TABLE IF NOT EXISTS households (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    household_name TEXT NOT NULL,
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    household_id INTEGER REFERENCES households(id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    display_name TEXT NOT NULL,
    phone_normalized TEXT UNIQUE NOT NULL,
    role TEXT NOT NULL DEFAULT 'participant',
    access_enabled INTEGER NOT NULL DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    last_access_at TEXT
);

CREATE TABLE IF NOT EXISTS announcements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    priority TEXT NOT NULL DEFAULT 'normal',
    pinned INTEGER NOT NULL DEFAULT 0,
    created_by INTEGER REFERENCES participants(id) ON DELETE SET NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    category TEXT NOT NULL,
    tags TEXT,
    author_id INTEGER REFERENCES participants(id) ON DELETE SET NULL,
    status TEXT NOT NULL DEFAULT 'open',
    pinned INTEGER NOT NULL DEFAULT 0,
    image_path TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS replies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    body TEXT NOT NULL,
    author_id INTEGER REFERENCES participants(id) ON DELETE SET NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS gear_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    item_name TEXT NOT NULL,
    category TEXT NOT NULL,
    quantity TEXT,
    description TEXT,
    pickup_return_notes TEXT,
    contact_preference TEXT,
    status TEXT NOT NULL DEFAULT 'available',
    author_id INTEGER REFERENCES participants(id) ON DELETE SET NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS meal_ideas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    meal_type TEXT NOT NULL,
    serves TEXT,
    description TEXT,
    prep_ahead_notes TEXT,
    cooking_instructions TEXT,
    equipment_needed TEXT,
    dietary_tags TEXT,
    cleanup_level TEXT,
    author_id INTEGER REFERENCES participants(id) ON DELETE SET NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ride_shares (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    leaving_from TEXT,
    departure_datetime TEXT,
    return_datetime TEXT,
    seats_available TEXT,
    gear_space TEXT,
    contact_preference TEXT,
    notes TEXT,
    status TEXT NOT NULL DEFAULT 'open',
    author_id INTEGER REFERENCES participants(id) ON DELETE SET NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    age_group TEXT,
    supplies_needed TEXT,
    willing_to_lead INTEGER NOT NULL DEFAULT 0,
    preferred_time TEXT,
    notes TEXT,
    author_id INTEGER REFERENCES participants(id) ON DELETE SET NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS faq_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    category TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS lost_found_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    description TEXT NOT NULL,
    photo_url TEXT,
    contact_preference TEXT,
    status TEXT NOT NULL DEFAULT 'open',
    author_id INTEGER REFERENCES participants(id) ON DELETE SET NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS section_views (
    participant_id INTEGER NOT NULL REFERENCES participants(id) ON DELETE CASCADE,
    section TEXT NOT NULL,
    last_viewed_at TEXT NOT NULL,
    PRIMARY KEY (participant_id, section)
);

CREATE INDEX IF NOT EXISTS idx_posts_category ON posts(category);
CREATE INDEX IF NOT EXISTS idx_posts_created ON posts(created_at);
CREATE INDEX IF NOT EXISTS idx_replies_post ON replies(post_id);
CREATE INDEX IF NOT EXISTS idx_gear_type ON gear_items(type);
CREATE INDEX IF NOT EXISTS idx_gear_category ON gear_items(category);
CREATE INDEX IF NOT EXISTS idx_meals_type ON meal_ideas(meal_type);
CREATE INDEX IF NOT EXISTS idx_rides_type ON ride_shares(type);
CREATE INDEX IF NOT EXISTS idx_faq_category ON faq_items(category);
