from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from sqlite_db import add_user, get_user_by_email, get_user_by_id

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# ---------------------
# Register
# ---------------------
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form["full_name"]
        email = request.form["email"]
        password = request.form["password"]

        existing_user = get_user_by_email(email)

        if existing_user:
            flash("This email is already registered. Please use another email or log in.", "danger")
            return redirect(url_for("auth.register"))

        hashed_pw = generate_password_hash(password)
        add_user(full_name, email, hashed_pw)

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


# ---------------------
# Login
# ---------------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = get_user_by_email(email)
        if user and check_password_hash(user[3], password):
            # Save to session
            session["user_id"] = user[0]
            session["user_role"] = user[4]

            flash("Logged in successfully!", "success")
            return redirect(url_for("dashboard.dashboard"))
        else:
            flash("Invalid email or password.", "danger")
            return redirect(url_for("auth.login"))

    return render_template("login.html")


# ---------------------
# Logout
# ---------------------
@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully!", "success")
    return redirect(url_for("auth.login"))