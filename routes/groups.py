# routes/groups.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlite_db import (
    get_all_groups_with_leader,
    get_user_groups,
    get_group_members,
    add_group,
    add_group_member,
    is_group_member,
    get_devotionals_by_group,
    get_user_by_id,
    get_group_by_id,
    can_manage_group,
    get_users_not_in_group,
    remove_group_member
)

groups_bp = Blueprint('groups', __name__, url_prefix='/groups')


# List all groups
@groups_bp.route('/')
def list_groups():
    user_id = session.get('user_id')
    user_role = session.get('user_role')

    if not user_id:
        return redirect(url_for('auth.login'))

    # All groups with leader
    groups = get_all_groups_with_leader()

    # Groups current user belongs to
    user_groups = get_user_groups(user_id)
    user_group_ids = [g[0] for g in user_groups]

    # Can create group if admin or leader
    can_create = user_role in ['admin', 'leader']

    return render_template(
        'groups.html',
        groups=groups,
        user_group_ids=user_group_ids,
        can_create=can_create
    )


# Join a group
@groups_bp.route('/join/<int:group_id>')
def join_group(group_id):
    user_id = session.get('user_id')
    if not user_id:
        flash("Please log in first.", "danger")
        return redirect(url_for('auth.login'))

    if not is_group_member(user_id, group_id):
        add_group_member(user_id, group_id)
        flash("Joined group successfully!", "success")
    else:
        flash("You are already a member of this group.", "info")

    return redirect(url_for('groups.list_groups'))


# Create a new group (Admin or Leader only)
@groups_bp.route('/create', methods=['GET', 'POST'])
def create_group():
    user_id = session.get('user_id')
    user_role = session.get('user_role')

    if not user_id:
        return redirect(url_for('auth.login'))

    if user_role not in ['admin', 'leader']:
        return "Unauthorized", 403

    if request.method == 'POST':
        group_name = request.form['group_name']
        description = request.form['description']

        add_group(group_name, description, user_id)
        flash('Group created successfully!', 'success')
        return redirect(url_for('groups.list_groups'))

    return render_template('new_group.html')


# View members of a specific group (only for members)
@groups_bp.route('/<int:group_id>/members')
def group_members(group_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login'))

    # Make sure user belongs to this group
    user_groups = get_user_groups(user_id)
    user_group_ids = [g[0] for g in user_groups]
    if group_id not in user_group_ids:
        flash("You are not a member of this group.", "danger")
        return redirect(url_for('groups.list_groups'))

    members = get_group_members(group_id)
    return render_template('group_members.html', members=members)

@groups_bp.route('/<int:group_id>')
def group_detail(group_id):
    user_id = session.get('user_id')
    user_role = session.get('user_role')

    if not user_id:
        return redirect(url_for('auth.login'))

    # Get all groups
    groups = get_all_groups_with_leader()

    # Find this group
    group = next((g for g in groups if g[0] == group_id), None)

    if not group:
        flash("Group not found.", "danger")
        return redirect(url_for('groups.list_groups'))

    # Check if user belongs
    user_groups = get_user_groups(user_id)
    user_group_ids = [g[0] for g in user_groups]

    if session.get('user_role') != 'admin' and group_id not in user_group_ids:
        flash("You must join the group first.", "danger")
        return redirect(url_for('groups.list_groups'))

    # Get members
    members = get_group_members(group_id)

    #  Get devotionals for this group
    devotionals_rows = get_devotionals_by_group(group_id)

    devotionals = []
    for d in devotionals_rows:
        author = get_user_by_id(d[3])

        devotionals.append({
            "id": d[0],
            "title": d[1],
            "content": d[2],
            "author_name": author[1] if author else "Unknown",
            "created_by": d[3],
            "created_at": d[6]
        })

    can_manage_members = can_manage_group(
        user_id,
        user_role,
        group_id
    )

    return render_template(
        'group_detail.html',
        group=group,
        members=members,
        devotionals=devotionals,
        can_manage_members=can_manage_members 
    )

@groups_bp.route('/<int:group_id>/manage-members')
def manage_group_members(group_id):
    user_id = session.get('user_id')
    user_role = session.get('user_role')

    if not user_id:
        return redirect(url_for('auth.login'))

    if not can_manage_group(user_id, user_role, group_id):
        flash("You do not have permission to manage this group.", "danger")
        return redirect(url_for('groups.list_groups'))

    group = get_group_by_id(group_id)
    members = get_group_members(group_id)
    available_users = get_users_not_in_group(group_id)

    return render_template(
        'manage_group_members.html',
        group=group,
        members=members,
        available_users=available_users
    )


@groups_bp.route('/<int:group_id>/add-member', methods=['POST'])
def add_member_to_group(group_id):
    user_id = session.get('user_id')
    user_role = session.get('user_role')

    if not user_id:
        return redirect(url_for('auth.login'))

    if not can_manage_group(user_id, user_role, group_id):
        flash("You do not have permission to manage this group.", "danger")
        return redirect(url_for('groups.list_groups'))

    new_member_id = request.form.get('user_id')

    if new_member_id:
        if not is_group_member(new_member_id, group_id):
            add_group_member(new_member_id, group_id)
            flash("Member added successfully.", "success")
        else:
            flash("User is already a member of this group.", "info")

    return redirect(url_for('groups.manage_group_members', group_id=group_id))


@groups_bp.route('/<int:group_id>/remove-member/<int:member_id>', methods=['POST'])
def remove_member_from_group(group_id, member_id):
    user_id = session.get('user_id')
    user_role = session.get('user_role')

    if not user_id:
        return redirect(url_for('auth.login'))

    if not can_manage_group(user_id, user_role, group_id):
        flash("You do not have permission to manage this group.", "danger")
        return redirect(url_for('groups.list_groups'))

    remove_group_member(member_id, group_id)
    flash("Member removed successfully.", "success")

    return redirect(url_for('groups.manage_group_members', group_id=group_id))