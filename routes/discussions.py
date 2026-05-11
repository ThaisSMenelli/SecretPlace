# routes/discussions.py

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlite_db import (
    create_thread,
    get_approved_threads,
    get_all_approved_threads,
    get_pending_threads,
    approve_thread,
    get_thread_by_id,
    add_message,
    get_messages,
    get_user_by_id,
    get_user_groups,
    delete_thread,
    delete_message
)

discussions_bp = Blueprint('discussions', __name__, url_prefix='/discussions')

# Main Page - List Threads
@discussions_bp.route('/')
def list_threads():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login'))

    user_role = session.get('user_role')

    if user_role == "admin":
        rows = get_all_approved_threads()
    else:
        rows = get_approved_threads(user_id)

        
    threads = []
    for r in rows:
        author = get_user_by_id(r[2])
        threads.append({
            "id": r[0],
            "title": r[1],
            "author_name": author[1] if author else "Unknown",
            "group_id": r[3],
            "created_at": r[5]
        })

    return render_template('discussion_threads.html', threads=threads)

#Create Thread
@discussions_bp.route('/create', methods=['GET', 'POST'])
def create_new_thread():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        title = request.form.get('title')
        group_id = request.form.get('group_id') or None

        if title and title.strip():
            create_thread(title, user_id, group_id)
            flash("Thread submitted! Awaiting approval.", "info")

        return redirect(url_for('discussions.list_threads'))

    # Optional: restrict group selection
    user_groups = get_user_groups(user_id)

    return render_template('new_thread.html', user_groups=user_groups)

#Thread Detail and Messages
@discussions_bp.route('/<int:thread_id>', methods=['GET', 'POST'])
def thread_detail(thread_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login'))

    # Get thread info
    thread_row = get_thread_by_id(thread_id)

    if not thread_row:
        flash("Thread not found.", "danger")
        return redirect(url_for('discussions.list_threads'))

    author = get_user_by_id(thread_row[2])

    thread = {
        "id": thread_row[0],
        "title": thread_row[1],
        "author_name": author[1] if author else "Unknown",
        "created_at": thread_row[4]
    
    }
    

    # Add message
    if request.method == 'POST':
        message_text = request.form.get('message_text')

        if message_text and message_text.strip():
            add_message(thread_id, user_id, message_text)
            flash("Message sent!", "success")

        return redirect(url_for('discussions.thread_detail', thread_id=thread_id))

    # Messages
    messages_raw = get_messages(thread_id)

    messages = []
    for m in messages_raw:
        author = get_user_by_id(m[2])
        messages.append({
            "id": m[0],
            "text": m[3],
            "author_name": author[1] if author else "Unknown",
            "created_at": m[5]
        })

    return render_template(
        'thread_detail.html',
        thread=thread,
        messages=messages
    )

# Pending Threads (admin/leader)
@discussions_bp.route('/pending')
def pending_threads():
    user_id = session.get('user_id')

    if not user_id:
        return redirect(url_for('auth.login'))

    if session.get('user_role') not in ['admin', 'leader']:
        return "Unauthorized", 403

    rows = get_pending_threads()

    threads = []
    for r in rows:
        threads.append({
            "id": r[0],
            "title": r[1],
            "created_at": r[5]
        })

    return render_template('pending_threads.html', threads=threads)

# Approve thread
@discussions_bp.route('/approve/<int:thread_id>', methods=['POST'])
def approve_thread_route(thread_id):
    user_id = session.get('user_id')

    if session.get('user_role') not in ['admin', 'leader']:
        return "Unauthorized", 403

    approve_thread(thread_id)

    flash("Thread approved!", "success")
    return redirect(url_for('discussions.pending_threads'))

# Delete thread / disapprove
@discussions_bp.route('/delete/<int:thread_id>', methods=['POST'])
def delete_thread_route(thread_id):
    user_id = session.get('user_id')

    if session.get('user_role') not in ['admin', 'leader']:
        return "Unauthorized", 403

    delete_thread(thread_id)

    flash("Thread deleted.", "info")
    return redirect(url_for('discussions.pending_threads'))

# Delete message
@discussions_bp.route('/message/delete/<int:message_id>', methods=['POST'])
def delete_message_route(message_id):
    user_role = session.get('user_role')

    if user_role not in ['admin', 'leader']:
        return "Unauthorized", 403

    delete_message(message_id)

    flash("Message removed.", "info")

    # stay in same thread
    thread_id = request.form.get('thread_id')
    return redirect(url_for('discussions.thread_detail', thread_id=thread_id))