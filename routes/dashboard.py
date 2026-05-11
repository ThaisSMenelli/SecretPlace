# secret-place/routes/dashboard.py

from flask import Blueprint, render_template, session, redirect, url_for, flash
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlite_db import (
    get_user_by_id,
    get_user_group_ids,
    get_all_groups,
    get_latest_devotional,
    get_upcoming_gatherings,
    get_recent_prayer_requests
)


dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')


@dashboard_bp.route('/')
def dashboard():
    user_id = session.get('user_id')
    if not user_id:
        flash("Please log in first.", "danger")
        return redirect(url_for('auth.login'))

    user_tuple = get_user_by_id(user_id)
    if not user_tuple:
        flash("User not found.", "danger")
        return redirect(url_for('auth.login'))

    user = {
        "id": user_tuple[0],
        "full_name": user_tuple[1],
        "email": user_tuple[2],
        "role": user_tuple[4]
    }

    # -----------------------
    # Latest devotional
    # -----------------------
    latest_devotional_row = get_latest_devotional()
    latest_devotional = None

    if latest_devotional_row:
        latest_devotional = {
            "id": latest_devotional_row[0],
            "title": latest_devotional_row[1],
            "content": latest_devotional_row[2],
            "author_name": latest_devotional_row[5],
            "created_at": latest_devotional_row[4]
        }

    # -----------------------
    # Upcoming gatherings
    # -----------------------
    upcoming_gatherings = get_upcoming_gatherings(2)

    # -----------------------
    # Recent prayer requests
    # -----------------------
    recent_requests = get_recent_prayer_requests(3)

    # -----------------------
    # Groups
    # -----------------------
    user_group_ids = get_user_group_ids(user_id)
    all_groups = get_all_groups()
    user_groups = [g for g in all_groups if g[0] in user_group_ids]

    can_create = user["role"] in ["admin", "leader"]

    return render_template(
        'dashboard.html',
        user=user,
        user_groups=user_groups,
        can_create=can_create,
        latest_devotional=latest_devotional,
        upcoming_gatherings=upcoming_gatherings,
        recent_requests=recent_requests
    )