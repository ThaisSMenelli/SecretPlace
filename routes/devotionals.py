from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlite_db import (
    get_global_devotionals,
    get_group_devotionals_for_user,
    add_devotional,
    get_devotional_by_id,
    get_user_by_id,
    get_user_notes,
    add_user_note,
    get_user_group_ids,
    get_groups_led_by_user,
    can_user_edit_delete,
    update_devotional,
    delete_devotional
)

devotionals_bp = Blueprint('devotionals', __name__, url_prefix='/devotionals')


# -----------------------
# List devotionals
# -----------------------
@devotionals_bp.route('/')
def list_devotionals():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login'))

    #Get current page from URL
    page = request.args.get('page', 1, type=int)
    per_page = 5

    user_group_ids = get_user_group_ids(user_id)

    devotionals = get_global_devotionals()

    if user_group_ids:
        devotionals += get_group_devotionals_for_user(user_id)

    # Build structure
    devotionals_data = []
    for d in devotionals:
        group_id = d[4]
        if group_id and group_id not in user_group_ids:
            continue

        author = get_user_by_id(d[3])
        devotionals_data.append({
            "id": d[0],
            "title": d[1],
            "content": d[2],
            "author_id": d[3],
            "group_id": group_id,
            "created_at": d[6],
            "author_name": d[7]
        })

    
    devotionals_data.sort(key=lambda x: x['created_at'], reverse=True)

    
    total = len(devotionals_data)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_devotionals = devotionals_data[start:end]

    has_next = end < total
    has_prev = start > 0

    user_role = session.get('user_role')
    can_create = user_role in ['admin', 'leader']

    return render_template(
        'devotional_list.html',
        devotionals=paginated_devotionals,
        page=page,
        has_next=has_next,
        has_prev=has_prev,
        can_create=can_create
    )


# -----------------------
# Devotional detail + notes
# -----------------------
@devotionals_bp.route('/<int:id>', methods=['GET', 'POST'])
def devotional_detail(id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login'))

    row = get_devotional_by_id(id)
    if not row:
        flash("Devotional not found.", "danger")
        return redirect(url_for('devotionals.list_devotionals'))

    group_id = row[4]

    if group_id:
        user_groups = get_user_group_ids(user_id)
        if group_id not in user_groups:
            flash("You do not have access.", "danger")
            return redirect(url_for('devotionals.list_devotionals'))

    author = get_user_by_id(row[3])

    devotional = {
        "id": row[0],
        "title": row[1],
        "content": row[2],
        "author_name": author[1] if author else "Unknown",
        "author_id": row[3], 
        "group_id": group_id,
        "created_at": row[6]
    }

    # Add note
    if request.method == 'POST':
        note_text = request.form.get('note_text')
        if note_text and note_text.strip():
            add_user_note(user_id, id, note_text)
            flash("Note added!", "success")
        return redirect(url_for('devotionals.devotional_detail', id=id))

    notes_raw = get_user_notes(user_id, id)
    notes = [{"text": n[1], "created_at": n[2]} for n in notes_raw]

    can_edit_delete = can_user_edit_delete(user_id, id)

    return render_template(
        'devotional_detail.html',
        devotional=devotional,
        notes=notes,
        can_edit_delete=can_edit_delete
    )


# -----------------------
# Create devotional
# -----------------------
@devotionals_bp.route('/create', methods=['GET', 'POST'])
def create_devotional():
    user_id = session.get('user_id')
    role = session.get('user_role')

    if role not in ['admin', 'leader']:
        return "Unauthorized", 403

    groups = get_groups_led_by_user(user_id)

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        group_id = request.form.get('group_id') or None

        add_devotional(title, content, user_id, group_id)

        flash("Devotional created!", "success")
        return redirect(url_for('devotionals.list_devotionals'))

    return render_template('new_devotional.html', groups=groups)


# -----------------------
# Edit devotional
# -----------------------
@devotionals_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
def edit_devotional(id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login'))

    if not can_user_edit_delete(user_id, id):
        return "Unauthorized", 403

    row = get_devotional_by_id(id)
    if not row:
        flash("Not found.", "danger")
        return redirect(url_for('devotionals.list_devotionals'))

    devotional = {
        "id": row[0],
        "title": row[1],
        "content": row[2],
        "group_id": row[4]
    }

    groups = get_groups_led_by_user(user_id)

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        group_id = request.form.get('group_id') or None

        # Security check for leaders
        if session.get('user_role') == 'leader':
            allowed_groups = [g[0] for g in get_groups_led_by_user(user_id)]

            if group_id and int(group_id) not in allowed_groups:
                flash("Unauthorized group selection.", "danger")
                return redirect(url_for('devotionals.edit_devotional', id=id))

        update_devotional(id, title, content, group_id)

        flash("Updated successfully!", "success")
        return redirect(url_for('devotionals.devotional_detail', id=id))

    return render_template('new_devotional.html', devotional=devotional, groups=groups)


# -----------------------
# Delete devotional
# -----------------------
@devotionals_bp.route('/<int:id>/delete', methods=['POST'])
def delete_devotional_route(id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login'))

    if not can_user_edit_delete(user_id, id):
        return "Unauthorized", 403

    delete_devotional(id)

    flash("Devotional deleted!", "success")
    return redirect(url_for('devotionals.list_devotionals'))