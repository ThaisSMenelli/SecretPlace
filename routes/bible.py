# secret-place/routes/bible.py

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from sqlite_db import (
    get_bible_progress,
    save_bible_progress,
    get_bible_books,
    validate_bible_reference,
    get_bible_progress_history,
    get_total_verses,
    get_bible_history_paginated
)

bible_bp = Blueprint("bible", __name__, url_prefix="/bible")


@bible_bp.route("/progress", methods=["GET", "POST"])
def view_progress():
    user_id = session.get("user_id")

    if not user_id:
        return redirect(url_for("auth.login"))

    books = get_bible_books()

    if request.method == "POST":
        book = request.form.get("book")
        chapter_raw = request.form.get("chapter")
        verse_raw = request.form.get("verse")

        try:
            chapter = int(chapter_raw)
            verse = int(verse_raw)

            if not book:
                flash("Please select a Bible book.", "danger")
                return redirect(url_for("bible.view_progress"))

            is_valid, message = validate_bible_reference(book, chapter, verse)

            if not is_valid:
                flash(message, "danger")
                return redirect(url_for("bible.view_progress"))

            save_bible_progress(user_id, book, chapter, verse)
            flash("Bible progress updated successfully!", "success")

        except ValueError:
            flash("Chapter and verse must be valid numbers.", "danger")

        return redirect(url_for("bible.view_progress"))

    row = get_bible_progress(user_id)

    progress = None
    if row:
        progress = {
            "book": row[0],
            "chapter": row[1],
            "verse": row[2],
            "updated_at": row[3]
        }

    history = get_bible_progress_history(user_id, limit=5)

    return render_template(
        "bible_progress.html",
        progress=progress,
        books=books,
        history=history
    )

@bible_bp.route("/chapter-info")
def chapter_info():
    book = request.args.get("book")
    chapter = request.args.get("chapter")

    try:
        chapter = int(chapter)
    except (TypeError, ValueError):
        return jsonify({
            "valid": False,
            "message": "Chapter must be a valid number."
        })

    total_verses = get_total_verses(book, chapter)

    if total_verses is None:
        return jsonify({
            "valid": False,
            "message": "This chapter does not exist for the selected book."
        })

    return jsonify({
        "valid": True,
        "total_verses": total_verses
    })

@bible_bp.route("/history")
def bible_history():
    user_id = session.get("user_id")

    if not user_id:
        return redirect(url_for("auth.login"))

    page = request.args.get("page", 1, type=int)
    per_page = 10

    history, total = get_bible_history_paginated(user_id, page, per_page)

    total_pages = (total + per_page - 1) // per_page

    return render_template(
        "bible_history.html",
        history=history,
        page=page,
        total_pages=total_pages
    )