from flask import Blueprint, render_template, request, flash

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        flash("Registration will be available soon.", "warning")
    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        flash("Login will be available soon.", "warning")
    return render_template("login.html")