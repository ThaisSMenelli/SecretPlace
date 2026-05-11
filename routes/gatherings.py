# secret-place/routes/gatherings.py

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import sys, os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlite_db import (
    add_gathering,
    get_all_gatherings,
    get_gathering_by_id,
    get_user_groups,
    get_all_groups,
    can_edit_gathering,
    delete_gathering,
    update_gathering   
)

gatherings_bp = Blueprint('gatherings', __name__, url_prefix='/gatherings')


# -------------------------
# LIST GATHERINGS
# -------------------------
@gatherings_bp.route('/')
def list_gatherings():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login'))

    user_role = session.get('user_role')
    user_group_ids = [g[0] for g in get_user_groups(user_id)]

    rows = get_all_gatherings()

    gatherings = []

    for g in rows:
        group_id = g[6]

        is_global = group_id is None
        is_allowed_group = group_id in user_group_ids

        if user_role != "admin" and not is_global and not is_allowed_group:
            continue

        gatherings.append({
            "id": g[0],
            "title": g[1],
            "description": g[2],
            "date": g[3],
            "time": g[4],
            "created_by": g[5],
            "group_id": group_id
        })

    return render_template(
        'gatherings.html',
        gatherings=gatherings,
        user_role=user_role,
        user_id=user_id
    )


# -------------------------
# CREATE
# -------------------------
@gatherings_bp.route('/create', methods=['GET', 'POST'])
def create_gathering():
    user_id = session.get('user_id')
    role = session.get('user_role')

    if not user_id:
        return redirect(url_for('auth.login'))

    if role not in ['admin', 'leader']:
        return "Unauthorized", 403

    if request.method == 'POST':
        add_gathering(
            request.form.get('title'),
            request.form.get('description'),
            request.form.get('date'),
            request.form.get('time'),
            user_id,
            request.form.get('group_id') or None
        )

        flash("Gathering created successfully!", "success")
        return redirect(url_for('gatherings.list_gatherings'))

    if role == "admin":
        user_groups = get_all_groups()
    else:
        user_groups = get_user_groups(user_id)

    return render_template(
        'new_gathering.html',
        user_groups=user_groups
    )


# -------------------------
# DETAIL
# -------------------------
@gatherings_bp.route('/<int:gathering_id>')
def gathering_detail(gathering_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login'))

    row = get_gathering_by_id(gathering_id)

    if not row:
        flash("Gathering not found.", "danger")
        return redirect(url_for('gatherings.list_gatherings'))

    gathering = {
        "id": row[0],
        "title": row[1],
        "description": row[2],
        "date": row[3],
        "time": row[4],
        "created_by": row[5],
        "group_id": row[6]
    }

    return render_template('gathering_detail.html', gathering=gathering)


# -------------------------
# EDIT
# -------------------------
@gatherings_bp.route('/<int:gathering_id>/edit', methods=['GET', 'POST'])
def edit_gathering(gathering_id):
    user_id = session.get('user_id')
    user_role = session.get('user_role')

    if not user_id:
        return redirect(url_for('auth.login'))

    row = get_gathering_by_id(gathering_id)

    if not row:
        return "Not found", 404

    if not can_edit_gathering(user_role, user_id, row[5]):
        return "Unauthorized", 403

    if request.method == 'POST':
        update_gathering(
            gathering_id,
            request.form.get('title'),
            request.form.get('description'),
            request.form.get('date'),
            request.form.get('time'),
            request.form.get('group_id') or None
        )

        flash("Gathering updated!", "success")
        return redirect(url_for('gatherings.list_gatherings'))

    if user_role == "admin":
        user_groups = get_all_groups()
    else:
        user_groups = get_user_groups(user_id)

    return render_template(
        "edit_gathering.html",
        gathering={
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "date": row[3],
            "time": row[4],
            "group_id": row[6]
        },
        user_groups=user_groups
    )


# -------------------------
# DELETE
# -------------------------
@gatherings_bp.route('/<int:gathering_id>/delete', methods=['POST'])
def delete_gathering_route(gathering_id):
    user_id = session.get('user_id')
    user_role = session.get('user_role')

    if not user_id:
        return redirect(url_for('auth.login'))

    row = get_gathering_by_id(gathering_id)

    if not row:
        return "Not found", 404

    if not can_edit_gathering(user_role, user_id, row[5]):
        return "Unauthorized", 403

    delete_gathering(gathering_id)

    flash("Gathering deleted!", "info")
    return redirect(url_for('gatherings.list_gatherings'))