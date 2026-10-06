from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

from utils.decorators import role_required

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route("/dashboard")
@login_required
def dashboard():
    if current_user.role == "provider":
        return redirect(url_for("provider.dashboard"))
    return render_template("dashboard.html")


@main_bp.route("/admin")
@role_required("admin")
def admin_home():
    return render_template("dashboard.html", admin_area=True)