from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from sqlite_db import connect_db, deactivate_user, update_user

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required():
    return session.get("user_role") == "admin"


@admin_bp.route("/users")
def admin_users():
    if not admin_required():
        flash("Access denied. Admin only.", "danger")
        return redirect(url_for("dashboard.dashboard"))

    conn = connect_db()
    c = conn.cursor()

    c.execute("""
        SELECT id, name, email, role
        FROM users
        WHERE is_active = 1
        ORDER BY name ASC
    """)

    users = c.fetchall()
    conn.close()

    return render_template("admin_users.html", users=users)


@admin_bp.route("/users/<int:user_id>/role", methods=["POST"])
def update_user_role(user_id):
    if not admin_required():
        flash("Access denied. Admin only.", "danger")
        return redirect(url_for("dashboard.dashboard"))

    new_role = request.form.get("role")

    allowed_roles = ["member", "leader", "admin"]

    if new_role not in allowed_roles:
        flash("Invalid role selected.", "danger")
        return redirect(url_for("admin.admin_users"))

    conn = connect_db()
    c = conn.cursor()

    c.execute("""
        UPDATE users
        SET role = ?
        WHERE id = ?
    """, (new_role, user_id))

    conn.commit()
    conn.close()

    flash("User role updated successfully.", "success")
    return redirect(url_for("admin.admin_users"))

@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
def delete_user(user_id):
    if not admin_required():
        flash("Access denied.", "danger")
        return redirect(url_for("dashboard.dashboard"))

    # evitar admin apagar a si mesmo
    if user_id == session.get("user_id"):
        flash("You cannot delete your own account.", "danger")
        return redirect(url_for("admin.admin_users"))

    deactivate_user(user_id)

    flash("User deactivated successfully.", "success")
    return redirect(url_for("admin.admin_users"))


@admin_bp.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
def edit_user(user_id):
    if not admin_required():
        flash("Access denied.", "danger")
        return redirect(url_for("dashboard.dashboard"))

    conn = connect_db()
    c = conn.cursor()

    # GET user
    c.execute("""
        SELECT id, name, email, role
        FROM users
        WHERE id = ?
    """, (user_id,))
    user = c.fetchone()

    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("admin.admin_users"))

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        role = request.form.get("role")

        update_user(user_id, name, email, role)

        flash("User updated successfully.", "success")
        return redirect(url_for("admin.admin_users"))

    return render_template("edit_user.html", user=user)