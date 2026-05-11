-- users
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT DEFAULT 'member'
);

-- bible_progress
CREATE TABLE IF NOT EXISTS bible_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    book TEXT,
    chapter INTEGER,
    verse INTEGER,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS bible_progress_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    book TEXT NOT NULL,
    chapter INTEGER NOT NULL,
    verse INTEGER NOT NULL,
    saved_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

-- devotionals
CREATE TABLE IF NOT EXISTS devotionals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    created_by INTEGER NOT NULL,
    group_id INTEGER,
    is_active INTEGER DEFAULT 1,
    FOREIGN KEY(created_by) REFERENCES users(id)
);

-- discussion_threads
CREATE TABLE IF NOT EXISTS discussion_threads (
    thread_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    created_by INTEGER NOT NULL,
    group_id INTEGER,
    is_approved INTEGER DEFAULT 1,
    FOREIGN KEY(created_by) REFERENCES users(id)
);

-- discussion_messages
CREATE TABLE IF NOT EXISTS discussion_messages (
    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
    thread_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    message_text TEXT NOT NULL,
    is_approved INTEGER DEFAULT 1,
    FOREIGN KEY(thread_id) REFERENCES discussion_threads(thread_id),
    FOREIGN KEY(user_id) REFERENCES users(id)
);

-- gatherings
CREATE TABLE IF NOT EXISTS gatherings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    date TEXT,
    time TEXT,
    created_by INTEGER NOT NULL,
    group_id INTEGER,
    FOREIGN KEY(created_by) REFERENCES users(id)
);

-- groups
CREATE TABLE IF NOT EXISTS groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_name TEXT NOT NULL,
    description TEXT,
    leader_id INTEGER,
    FOREIGN KEY(leader_id) REFERENCES users(id)
);

-- group_members
CREATE TABLE IF NOT EXISTS group_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    group_id INTEGER NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(group_id) REFERENCES groups(id)
);

-- prayer_requests
CREATE TABLE IF NOT EXISTS prayer_requests (
    request_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    request_text TEXT NOT NULL,
    is_approved INTEGER DEFAULT 0,
    submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);