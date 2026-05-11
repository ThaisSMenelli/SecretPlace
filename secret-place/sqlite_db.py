# sqlite_db.py
# This file contains all SQLite database helper functions used by the Flask app.

import sqlite3
from config import Config


# -----------------------
# Database Connection
# -----------------------
def connect_db():
    """Open a connection to the SQLite database."""
    return sqlite3.connect(Config.DATABASE)


# -----------------------
# Users
# -----------------------
def add_user(name, email, password, role="member"):
    """Create a new active user account."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO users (name, email, password, role)
        VALUES (?, ?, ?, ?)
        """,
        (name, email, password, role)
    )

    conn.commit()
    conn.close()


def get_user_by_email(email):
    """Return an active user by email address."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE email = ? AND is_active = 1
        """,
        (email,)
    )

    user = cursor.fetchone()
    conn.close()
    return user


def get_user_by_id(user_id):
    """Return one user by id."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE id = ?",
        (user_id,)
    )

    user = cursor.fetchone()
    conn.close()
    return user


def deactivate_user(user_id):
    """Soft delete a user by setting is_active to 0."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE users
        SET is_active = 0
        WHERE id = ?
        """,
        (user_id,)
    )

    conn.commit()
    conn.close()


def update_user(user_id, name, email, role):
    """Update basic user details."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE users
        SET name = ?, email = ?, role = ?
        WHERE id = ?
        """,
        (name, email, role, user_id)
    )

    conn.commit()
    conn.close()


# -----------------------
# Bible Progress
# -----------------------
def get_bible_progress(user_id):
    """Return the latest Bible progress for a user."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT book, chapter, verse, updated_at
        FROM bible_progress
        WHERE user_id = ?
        """,
        (user_id,)
    )

    progress = cursor.fetchone()
    conn.close()
    return progress


def save_bible_progress(user_id, book, chapter, verse):
    """Save current Bible progress and add a history record."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM bible_progress WHERE user_id = ?",
        (user_id,)
    )
    existing_progress = cursor.fetchone()

    if existing_progress:
        cursor.execute(
            """
            UPDATE bible_progress
            SET book = ?, chapter = ?, verse = ?, updated_at = datetime('now')
            WHERE user_id = ?
            """,
            (book, chapter, verse, user_id)
        )
    else:
        cursor.execute(
            """
            INSERT INTO bible_progress (user_id, book, chapter, verse, updated_at)
            VALUES (?, ?, ?, ?, datetime('now'))
            """,
            (user_id, book, chapter, verse)
        )

    # Keep a record of each update for the reading history page.
    cursor.execute(
        """
        INSERT INTO bible_progress_history (user_id, book, chapter, verse, saved_at)
        VALUES (?, ?, ?, ?, datetime('now'))
        """,
        (user_id, book, chapter, verse)
    )

    conn.commit()
    conn.close()


def get_bible_progress_history(user_id, limit=5):
    """Return the most recent Bible progress history records."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT book, chapter, verse, saved_at
        FROM bible_progress_history
        WHERE user_id = ?
        ORDER BY saved_at DESC
        LIMIT ?
        """,
        (user_id, limit)
    )

    history_records = cursor.fetchall()
    conn.close()
    return history_records


def get_bible_history_paginated(user_id, page=1, per_page=10):
    """Return Bible history records using pagination."""
    conn = connect_db()
    cursor = conn.cursor()

    offset = (page - 1) * per_page

    cursor.execute(
        """
        SELECT book, chapter, verse, saved_at
        FROM bible_progress_history
        WHERE user_id = ?
        ORDER BY saved_at DESC
        LIMIT ? OFFSET ?
        """,
        (user_id, per_page, offset)
    )
    history_records = cursor.fetchall()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM bible_progress_history
        WHERE user_id = ?
        """,
        (user_id,)
    )
    total_records = cursor.fetchone()[0]

    conn.close()
    return history_records, total_records


# -----------------------
# Bible Structure
# -----------------------
def get_bible_books():
    """Return all Bible books stored in the bible_structure table."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT DISTINCT book
        FROM bible_structure
        ORDER BY id ASC
        """
    )

    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]


def get_total_verses(book, chapter):
    """Return the total number of verses for a book chapter."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT total_verses
        FROM bible_structure
        WHERE book = ? AND chapter = ?
        """,
        (book, chapter)
    )

    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


def validate_bible_reference(book, chapter, verse):
    """Check if a Bible book, chapter and verse are valid."""
    total_verses = get_total_verses(book, chapter)

    if total_verses is None:
        return False, "This chapter does not exist for the selected book."

    if verse < 1 or verse > total_verses:
        return False, f"{book} chapter {chapter} only has {total_verses} verses."

    return True, "Valid reference."


# -----------------------
# Devotionals
# -----------------------
def get_global_devotionals():
    """Return active devotionals that are visible to all users."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT d.*, u.name
        FROM devotionals d
        JOIN users u ON d.created_by = u.id
        WHERE d.group_id IS NULL
        AND d.is_active = 1
        ORDER BY d.created_at DESC
        """
    )

    devotionals = cursor.fetchall()
    conn.close()
    return devotionals


def get_group_devotionals_for_user(user_id):
    """Return active group devotionals for groups the user belongs to."""
    group_ids = get_user_group_ids(user_id)

    if not group_ids:
        return []

    conn = connect_db()
    cursor = conn.cursor()
    placeholders = ",".join("?" for _ in group_ids)

    query = f"""
        SELECT d.*, u.name
        FROM devotionals d
        JOIN users u ON d.created_by = u.id
        WHERE d.group_id IN ({placeholders})
        AND d.is_active = 1
        ORDER BY d.created_at DESC
    """

    cursor.execute(query, group_ids)
    devotionals = cursor.fetchall()
    conn.close()
    return devotionals


def add_devotional(title, content, created_by, group_id=None):
    """Create a new devotional."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO devotionals
        (title, content, created_by, group_id, is_active, created_at)
        VALUES (?, ?, ?, ?, 1, datetime('now'))
        """,
        (title, content, created_by, group_id)
    )

    conn.commit()
    conn.close()


def get_devotional_by_id(devotional_id):
    """Return one active devotional by id."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM devotionals
        WHERE id = ? AND is_active = 1
        """,
        (devotional_id,)
    )

    devotional = cursor.fetchone()
    conn.close()
    return devotional


def get_latest_devotional():
    """Return the most recently created active devotional."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            d.id,
            d.title,
            d.content,
            d.created_by,
            d.created_at,
            u.name AS author_name
        FROM devotionals d
        JOIN users u ON d.created_by = u.id
        WHERE d.is_active = 1
        ORDER BY d.created_at DESC
        LIMIT 1
        """
    )

    devotional = cursor.fetchone()
    conn.close()
    return devotional


def get_devotionals_by_group(group_id):
    """Return active devotionals for one group."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM devotionals
        WHERE group_id = ? AND is_active = 1
        ORDER BY created_at DESC
        """,
        (group_id,)
    )

    devotionals = cursor.fetchall()
    conn.close()
    return devotionals


def update_devotional(devotional_id, title, content, group_id=None):
    """Update devotional details."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE devotionals
        SET title = ?, content = ?, group_id = ?
        WHERE id = ?
        """,
        (title, content, group_id, devotional_id)
    )

    conn.commit()
    conn.close()


def delete_devotional(devotional_id):
    """Soft delete a devotional by setting is_active to 0."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE devotionals SET is_active = 0 WHERE id = ?",
        (devotional_id,)
    )

    conn.commit()
    conn.close()


def can_user_edit_delete(user_id, devotional_id):
    """Check if a user can edit or delete a devotional."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT created_by, group_id FROM devotionals WHERE id = ?",
        (devotional_id,)
    )
    devotional = cursor.fetchone()

    if not devotional:
        conn.close()
        return False

    devotional_creator = devotional[0]

    cursor.execute(
        "SELECT role FROM users WHERE id = ?",
        (user_id,)
    )
    user_role = cursor.fetchone()
    conn.close()

    if not user_role:
        return False

    role = user_role[0]

    if role == "admin":
        return True

    if role == "leader" and devotional_creator == user_id:
        return True

    return False


# -----------------------
# Discussion Threads and Messages
# -----------------------
def create_thread(title, user_id, group_id=None):
    """Create a new discussion thread pending approval."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO discussion_threads
        (title, created_by, group_id, is_approved, created_at)
        VALUES (?, ?, ?, 0, datetime('now'))
        """,
        (title, user_id, group_id)
    )

    conn.commit()
    conn.close()


def get_approved_threads(user_id):
    """Return approved global threads and threads from the user's groups."""
    conn = connect_db()
    cursor = conn.cursor()
    group_ids = get_user_group_ids(user_id)

    if group_ids:
        placeholders = ",".join("?" for _ in group_ids)
        query = f"""
            SELECT *
            FROM discussion_threads
            WHERE is_approved = 1
            AND (group_id IS NULL OR group_id IN ({placeholders}))
            ORDER BY created_at DESC
        """
        cursor.execute(query, group_ids)
    else:
        cursor.execute(
            """
            SELECT *
            FROM discussion_threads
            WHERE is_approved = 1 AND group_id IS NULL
            ORDER BY created_at DESC
            """
        )

    threads = cursor.fetchall()
    conn.close()
    return threads


def get_all_approved_threads():
    """Return all approved threads for admin users."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM discussion_threads
        WHERE is_approved = 1
        ORDER BY created_at DESC
        """
    )

    threads = cursor.fetchall()
    conn.close()
    return threads


def get_pending_threads():
    """Return discussion threads waiting for approval."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM discussion_threads
        WHERE is_approved = 0
        ORDER BY created_at DESC
        """
    )

    threads = cursor.fetchall()
    conn.close()
    return threads


def approve_thread(thread_id):
    """Approve a pending discussion thread."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE discussion_threads
        SET is_approved = 1
        WHERE thread_id = ?
        """,
        (thread_id,)
    )

    conn.commit()
    conn.close()


def get_thread_by_id(thread_id):
    """Return one discussion thread by id."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT thread_id, title, created_by, group_id, created_at
        FROM discussion_threads
        WHERE thread_id = ?
        """,
        (thread_id,)
    )

    thread = cursor.fetchone()
    conn.close()
    return thread


def add_message(thread_id, user_id, message_text):
    """Add a message to a discussion thread."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO discussion_messages (thread_id, user_id, message_text, is_approved)
        VALUES (?, ?, ?, 1)
        """,
        (thread_id, user_id, message_text)
    )

    conn.commit()
    conn.close()


def get_messages(thread_id):
    """Return approved messages for one thread."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM discussion_messages
        WHERE thread_id = ? AND is_approved = 1
        ORDER BY created_at ASC
        """,
        (thread_id,)
    )

    messages = cursor.fetchall()
    conn.close()
    return messages


def delete_thread(thread_id):
    """Delete a discussion thread."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM discussion_threads WHERE thread_id = ?",
        (thread_id,)
    )

    conn.commit()
    conn.close()


def delete_message(message_id):
    """Soft delete a message by marking it as not approved."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE discussion_messages
        SET is_approved = 0
        WHERE message_id = ?
        """,
        (message_id,)
    )

    conn.commit()
    conn.close()


# -----------------------
# Gatherings
# -----------------------
def add_gathering(title, description, date, time, created_by, group_id=None):
    """Create a new gathering."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO gatherings (title, description, date, time, created_by, group_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (title, description, date, time, created_by, group_id)
    )

    conn.commit()
    conn.close()


def get_all_gatherings():
    """Return all gatherings."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM gatherings ORDER BY date ASC")

    gatherings = cursor.fetchall()
    conn.close()
    return gatherings


def get_gathering_by_id(gathering_id):
    """Return one gathering by id."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM gatherings WHERE gathering_id = ?",
        (gathering_id,)
    )

    gathering = cursor.fetchone()
    conn.close()
    return gathering


def can_edit_gathering(user_role, user_id, gathering_creator_id):
    """Check if the user can edit or delete a gathering."""
    if user_role == "admin":
        return True

    if user_role == "leader" and user_id == gathering_creator_id:
        return True

    return False


def update_gathering(gathering_id, title, description, date, time, group_id):
    """Update gathering details."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE gatherings
        SET title = ?, description = ?, date = ?, time = ?, group_id = ?
        WHERE gathering_id = ?
        """,
        (title, description, date, time, group_id, gathering_id)
    )

    conn.commit()
    conn.close()


def delete_gathering(gathering_id):
    """Delete a gathering."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM gatherings WHERE gathering_id = ?",
        (gathering_id,)
    )

    conn.commit()
    conn.close()


def get_upcoming_gatherings(limit=2):
    """Return the next upcoming gatherings for the dashboard."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT gathering_id, title, date, time
        FROM gatherings
        ORDER BY date ASC, time ASC
        LIMIT ?
        """,
        (limit,)
    )

    gatherings = cursor.fetchall()
    conn.close()
    return gatherings


# -----------------------
# Groups and Memberships
# -----------------------
def get_all_groups():
    """Return all groups."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM groups ORDER BY group_name ASC")

    groups = cursor.fetchall()
    conn.close()
    return groups


def add_group(name, description, leader_id):
    """Create a new group."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO groups (group_name, description, leader_id)
        VALUES (?, ?, ?)
        """,
        (name, description, leader_id)
    )

    conn.commit()
    conn.close()


def add_group_member(user_id, group_id):
    """Add a user to a group."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO group_members (user_id, group_id)
        VALUES (?, ?)
        """,
        (user_id, group_id)
    )

    conn.commit()
    conn.close()


def is_group_member(user_id, group_id):
    """Check if a user is already a group member."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM group_members
        WHERE user_id = ? AND group_id = ?
        """,
        (user_id, group_id)
    )

    membership = cursor.fetchone()
    conn.close()
    return membership is not None


def get_all_groups_with_leader():
    """Return all groups with leader name."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT g.id, g.group_name, g.description, u.name
        FROM groups g
        LEFT JOIN users u ON g.leader_id = u.id
        ORDER BY g.group_name
        """
    )

    groups = cursor.fetchall()
    conn.close()
    return groups


def get_user_groups(user_id):
    """Return groups where the user is a member."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT g.id, g.group_name, g.description, u.name
        FROM groups g
        INNER JOIN group_members gm ON g.id = gm.group_id
        LEFT JOIN users u ON g.leader_id = u.id
        WHERE gm.user_id = ?
        ORDER BY g.group_name
        """,
        (user_id,)
    )

    groups = cursor.fetchall()
    conn.close()
    return groups


def get_user_group_ids(user_id):
    """Return only the group ids for a user."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT group_id FROM group_members WHERE user_id = ?",
        (user_id,)
    )

    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]


def get_group_members(group_id):
    """Return active members of a group."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT u.id, u.name
        FROM users u
        JOIN group_members gm ON gm.user_id = u.id
        WHERE gm.group_id = ?
        AND u.is_active = 1
        """,
        (group_id,)
    )

    members = cursor.fetchall()
    conn.close()
    return members


def get_groups_led_by_user(user_id):
    """Return groups where the user is the leader."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, group_name FROM groups WHERE leader_id = ?",
        (user_id,)
    )

    groups = cursor.fetchall()
    conn.close()
    return groups


def get_group_by_id(group_id):
    """Return one group with leader name."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT g.id, g.group_name, g.description, g.leader_id, u.name
        FROM groups g
        LEFT JOIN users u ON g.leader_id = u.id
        WHERE g.id = ?
        """,
        (group_id,)
    )

    group = cursor.fetchone()
    conn.close()
    return group


def can_manage_group(user_id, user_role, group_id):
    """Check if a user can manage group members."""
    if user_role == "admin":
        return True

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id
        FROM groups
        WHERE id = ? AND leader_id = ?
        """,
        (group_id, user_id)
    )

    group = cursor.fetchone()
    conn.close()
    return group is not None


def get_users_not_in_group(group_id):
    """Return active users who are not already in the selected group."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, name, email, role
        FROM users
        WHERE is_active = 1
        AND id NOT IN (
            SELECT user_id
            FROM group_members
            WHERE group_id = ?
        )
        ORDER BY name ASC
        """,
        (group_id,)
    )

    users = cursor.fetchall()
    conn.close()
    return users


def remove_group_member(user_id, group_id):
    """Remove a user from a group."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM group_members
        WHERE user_id = ? AND group_id = ?
        """,
        (user_id, group_id)
    )

    conn.commit()
    conn.close()


# -----------------------
# Prayer Requests
# -----------------------
def get_approved_prayer_requests():
    """Return approved prayer requests."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM prayer_requests
        WHERE is_approved = 1
        ORDER BY submitted_at DESC
        """
    )

    requests = cursor.fetchall()
    conn.close()
    return requests


def add_prayer_request(user_id, text):
    """Create a new prayer request pending approval."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO prayer_requests (user_id, request_text, is_approved, submitted_at)
        VALUES (?, ?, 0, datetime('now'))
        """,
        (user_id, text)
    )

    conn.commit()
    conn.close()


def approve_prayer_request(request_id, moderator_id):
    """Approve a prayer request."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE prayer_requests
        SET is_approved = 1, moderated_by = ?
        WHERE request_id = ?
        """,
        (moderator_id, request_id)
    )

    conn.commit()
    conn.close()


def get_pending_prayer_requests():
    """Return prayer requests waiting for approval."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM prayer_requests WHERE is_approved = 0"
    )

    requests = cursor.fetchall()
    conn.close()
    return requests


def delete_prayer_request(request_id):
    """Delete a prayer request."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM prayer_requests WHERE request_id = ?",
        (request_id,)
    )

    conn.commit()
    conn.close()


def get_recent_prayer_requests(limit=3):
    """Return recent approved prayer requests for the dashboard."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT request_id, request_text, submitted_at
        FROM prayer_requests
        WHERE is_approved = 1
        ORDER BY submitted_at DESC
        LIMIT ?
        """,
        (limit,)
    )

    requests = cursor.fetchall()
    conn.close()
    return requests


def get_prayer_requests_paginated(page=1, per_page=5):
    """Return approved prayer requests using pagination."""
    conn = connect_db()
    cursor = conn.cursor()

    offset = (page - 1) * per_page

    cursor.execute(
        """
        SELECT request_id, request_text, submitted_at
        FROM prayer_requests
        WHERE is_approved = 1
        ORDER BY submitted_at DESC
        LIMIT ? OFFSET ?
        """,
        (per_page, offset)
    )
    requests = cursor.fetchall()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM prayer_requests
        WHERE is_approved = 1
        """
    )
    total_requests = cursor.fetchone()[0]

    conn.close()
    return requests, total_requests


# -----------------------
# User Notes for Devotionals
# -----------------------
def add_user_note(user_id, devotional_id, note_text):
    """Add a private note to a devotional."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO user_notes (user_id, devotional_id, note_text)
        VALUES (?, ?, ?)
        """,
        (user_id, devotional_id, note_text)
    )

    conn.commit()
    conn.close()


def get_user_notes(user_id, devotional_id):
    """Return private notes for one user and devotional."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT note_id, note_text, updated_at
        FROM user_notes
        WHERE user_id = ? AND devotional_id = ?
        ORDER BY updated_at DESC
        """,
        (user_id, devotional_id)
    )

    notes = cursor.fetchall()
    conn.close()
    return notes


def get_latest_user_devotional(user_id):
    """Return the latest devotional available to a specific user."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT group_id FROM group_members WHERE user_id = ?",
        (user_id,)
    )
    user_group_ids = [row[0] for row in cursor.fetchall()]

    placeholders = ",".join("?" for _ in user_group_ids) if user_group_ids else ""

    query = f"""
        SELECT *
        FROM devotionals
        WHERE is_active = 1 AND (
            group_id IS NULL
            {f' OR group_id IN ({placeholders})' if placeholders else ''}
        )
        ORDER BY created_at DESC
        LIMIT 1
    """

    cursor.execute(query, user_group_ids)
    devotional = cursor.fetchone()
    conn.close()
    return devotional