# secret-place/routes/dashboard.py

from flask import Blueprint, render_template, session, redirect, url_for, flash
import sys
import os

# Allow this file to import modules from the project root folder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import database helper functions used by the dashboard
from sqlite_db import (
    get_user_by_id,
    get_user_group_ids,
    get_all_groups,
    get_latest_user_devotional,
    get_upcoming_gatherings,
    get_recent_prayer_requests
)

# Create Blueprint for dashboard routes
dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


# ---------------------------------------------------
# Dashboard
# Main page displayed after user login
# ---------------------------------------------------
@dashboard_bp.route("/")
def dashboard():

    # Get logged-in user ID from session
    user_id = session.get("user_id")

    # Redirect user if not logged in
    if not user_id:
        flash("Please log in first.", "danger")
        return redirect(url_for("auth.login"))

    # Get user information from database
    user_tuple = get_user_by_id(user_id)

    # Check if user exists
    if not user_tuple:
        flash("User not found.", "danger")
        return redirect(url_for("auth.login"))

    # Convert database row into dictionary
    user = {
        "id": user_tuple[0],
        "full_name": user_tuple[1],
        "email": user_tuple[2],
        "role": user_tuple[4]
    }

    # ---------------------------------------------------
    # Latest Devotional
    # Get the most recent devotional available
    # ---------------------------------------------------
    latest_devotional_row = get_latest_user_devotional(user_id)

    latest_devotional = None

    # Convert devotional row into dictionary
    if latest_devotional_row:
        latest_devotional = {
            "id": latest_devotional_row[0],
            "title": latest_devotional_row[1],
            "content": latest_devotional_row[2],
            "author_name": latest_devotional_row[5],
            "created_at": latest_devotional_row[4]
        }

    # ---------------------------------------------------
    # Upcoming Gatherings
    # Display the next two gatherings on dashboard
    # ---------------------------------------------------
    upcoming_gatherings = get_upcoming_gatherings(2)

    # ---------------------------------------------------
    # Recent Prayer Requests
    # Display the latest approved prayer requests
    # ---------------------------------------------------
    recent_requests = get_recent_prayer_requests(3)

    # ---------------------------------------------------
    # User Groups
    # Get groups the current user belongs to
    # ---------------------------------------------------
    user_group_ids = get_user_group_ids(user_id)

    all_groups = get_all_groups()

    # Filter only groups joined by the user
    user_groups = [group for group in all_groups if group[0] in user_group_ids]

    # Only admin and leader users can create groups
    can_create = user["role"] in ["admin", "leader"]

    # Render dashboard template
    return render_template(
        "dashboard.html",
        user=user,
        user_groups=user_groups,
        can_create=can_create,
        latest_devotional=latest_devotional,
        upcoming_gatherings=upcoming_gatherings,
        recent_requests=recent_requests
    )