from datetime import date

from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

from models.ride import Ride
from models.user import User

main_bp = Blueprint("main", __name__)

UPCOMING_LIMIT = 3


@main_bp.route("/")
def index():
    today = date.today()

    candidates = (
        Ride.query.join(User, Ride.provider_id == User.id)
        .filter(
            Ride.status == "scheduled",
            Ride.ride_date >= today,
            User.account_status == "active",
        )
        .order_by(Ride.ride_date.asc(), Ride.ride_time.asc())
        .limit(15)
        .all()
    )
    upcoming = [r for r in candidates if r.booked_seats < r.total_seats][:UPCOMING_LIMIT]

    return render_template("index.html", upcoming=upcoming, today=today.isoformat())


@main_bp.route("/about")
def about():
    return render_template("about.html")


@main_bp.route("/dashboard")
@login_required
def dashboard():
    if current_user.role == "provider":
        return redirect(url_for("provider.dashboard"))
    if current_user.role == "admin":
        return redirect(url_for("admin.overview"))
    return render_template("dashboard.html")