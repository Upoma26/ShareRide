from flask import Blueprint, render_template, request, flash

from utils.uploads import save_nid_file

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nid_front = save_nid_file(request.files.get("nid_front"), "front")
        nid_back = save_nid_file(request.files.get("nid_back"), "back")

        if not nid_front or not nid_back:
            flash("Please upload both sides of your NID as JPG, PNG or PDF.", "danger")
        else:
            flash("NID uploaded successfully. Account creation will be added in SR-8.", "success")

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        flash("Login will be available soon.", "warning")
    return render_template("login.html")