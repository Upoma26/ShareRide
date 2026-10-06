from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route("/dashboard")
@login_required
def dashboard():
    if current_user.role == "provider":
        return redirect(url_for("provider.dashboard"))
    if current_user.role == "admin":
        return redirect(url_for("admin.overview"))
    return render_template("dashboard.html")