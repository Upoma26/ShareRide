import re

from flask import Blueprint, render_template, request, flash, redirect, url_for

from extensions import db
from models.user import User
from utils.uploads import save_nid_file

auth_bp = Blueprint("auth", __name__)

PHONE_PATTERN = re.compile(r"^01[3-9][0-9]{8}$")
NID_PATTERN = re.compile(r"^([0-9]{10}|[0-9]{13}|[0-9]{17})$")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip().lower()
        nid_number = request.form.get("nid_number", "").strip()
        role = request.form.get("role", "seeker")
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        errors = []

        if len(full_name) < 3:
            errors.append("Full name must be at least 3 letters.")
        if not PHONE_PATTERN.match(phone):
            errors.append("Enter a valid 11-digit Bangladeshi phone number.")
        if "@" not in email or "." not in email:
            errors.append("Enter a valid email address.")
        if not NID_PATTERN.match(nid_number):
            errors.append("NID must be 10, 13 or 17 digits.")
        if role not in ("seeker", "provider"):
            errors.append("Please choose a valid role.")
        if len(password) < 8:
            errors.append("Password must be at least 8 characters.")
        if password != confirm_password:
            errors.append("Passwords do not match.")

        if not errors:
            if User.query.filter_by(phone=phone).first():
                errors.append("An account with this phone number already exists.")
            if User.query.filter_by(email=email).first():
                errors.append("An account with this email already exists.")
            if User.query.filter_by(nid_number=nid_number).first():
                errors.append("An account with this NID already exists.")

        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("register.html")

        nid_front = save_nid_file(request.files.get("nid_front"), "front")
        nid_back = save_nid_file(request.files.get("nid_back"), "back")

        if not nid_front or not nid_back:
            flash("Please upload both sides of your NID as JPG, PNG or PDF.", "danger")
            return render_template("register.html")

        user = User(
            full_name=full_name,
            phone=phone,
            email=email,
            role=role,
            nid_number=nid_number,
            nid_front=nid_front,
            nid_back=nid_back,
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        flash("Account created! Please verify your phone number to activate it.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        flash("Login will be available soon.", "warning")
    return render_template("login.html")