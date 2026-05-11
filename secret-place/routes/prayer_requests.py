# secret-place/routes/prayer_requests_routes.py

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlite_db import (
    get_approved_prayer_requests,
    add_prayer_request,
    approve_prayer_request,
    get_pending_prayer_requests,
    delete_prayer_request,
    get_prayer_requests_paginated
)

prayer_requests_bp = Blueprint('prayer_requests', __name__, url_prefix='/prayer_requests')


# List approved prayer requests
@prayer_requests_bp.route('/')
def list_requests():
    page = request.args.get('page', 1, type=int)

    per_page = 5

    rows, total = get_prayer_requests_paginated(page, per_page)

    requests = []
    for r in rows:
        requests.append({
            "id": r[0],
            "text": r[1],
            "date": r[2]
        })

    total_pages = (total + per_page - 1) // per_page

    return render_template(
        "prayer_requests.html",
        requests=requests,
        page=page,
        total_pages=total_pages
    )

# Submit prayer request
@prayer_requests_bp.route('/create', methods=['GET', 'POST'])
def create_request():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        text = request.form.get('request_text')

        if text and text.strip():
            add_prayer_request(user_id, text)
            flash('Prayer request submitted! Awaiting approval.', 'success')

        return redirect(url_for('prayer_requests.list_requests'))

    return render_template('new_prayer_request.html')

# Approve request (admin/leader)
@prayer_requests_bp.route('/approve/<int:request_id>', methods=['POST'])
def approve_request(request_id):
    user_id = session.get('user_id')

    if session.get('user_role') not in ['admin', 'leader']:
        return "Unauthorized", 403

    approve_prayer_request(request_id, user_id)

    flash('Prayer request approved!', 'success')
    return redirect(url_for('prayer_requests.pending_requests'))

@prayer_requests_bp.route('/pending')
def pending_requests():
    user_id = session.get('user_id')

    if not user_id:
        return redirect(url_for('auth.login'))

    if session.get('user_role') not in ['admin', 'leader']:
        return "Unauthorized", 403

    rows = get_pending_prayer_requests()

    requests_data = []
    for r in rows:
        requests_data.append({
            "id": r[0],
            "text": r[2],
            "date": r[4]
        })

    return render_template('pending_prayer_requests.html', requests=requests_data)

@prayer_requests_bp.route('/delete/<int:request_id>', methods=['POST'])
def delete_request(request_id):
    if session.get('user_role') not in ['admin', 'leader']:
        return "Unauthorized", 403

    delete_prayer_request(request_id)

    flash("Prayer request deleted.", "info")
    return redirect(url_for('prayer_requests.pending_requests'))