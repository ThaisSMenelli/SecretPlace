from flask import Flask, render_template 
from config import Config

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = Config.SECRET_KEY



# Directly import your blueprints
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.devotionals import devotionals_bp
from routes.discussions import discussions_bp
from routes.prayer_requests import prayer_requests_bp
from routes.groups import groups_bp
from routes.gatherings import gatherings_bp
from routes.bible import bible_bp
from routes.admin import admin_bp

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(devotionals_bp)
app.register_blueprint(discussions_bp)
app.register_blueprint(prayer_requests_bp)
app.register_blueprint(groups_bp)
app.register_blueprint(gatherings_bp)
app.register_blueprint(bible_bp)
app.register_blueprint(admin_bp)

# Home route
from flask import session, redirect, url_for

@app.route("/")
def home():
    if session.get("user_id"):
        return redirect(url_for("dashboard.dashboard"))
    return render_template("home.html")

if __name__ == "__main__":
    app.run(debug=True)