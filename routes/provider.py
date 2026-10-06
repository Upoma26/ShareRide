from datetime import date

from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import current_user

from models.ride import Ride
from models.vehicle import Vehicle, VEHICLE_TYPES
from utils.decorators import role_required

provider_bp = Blueprint("provider", __name__, url_prefix="/provider")


@provider_bp.route("/dashboard")
@role_required("provider")
def dashboard():
    rides = (
        Ride.query.filter_by(provider_id=current_user.id)
        .order_by(Ride.ride_date.desc(), Ride.ride_time.desc())
        .all()
    )
    today = date.today()
    upcoming = [r for r in rides if r.status == "scheduled" and r.ride_date >= today]
    completed = [r for r in rides if r.status == "completed"]
    earnings = sum(r.booked_seats * r.fare_per_seat for r in completed)

    return render_template(
        "provider/dashboard.html",
        rides=rides,
        total_count=len(rides),
        upcoming_count=len(upcoming),
        earnings=earnings,
    )


@provider_bp.route("/rides/new", methods=["GET", "POST"])
@role_required("provider")
def post_ride():
    if request.method == "POST":
        flash("Saving rides will be added in SR-16.", "warning")
        return redirect(url_for("provider.post_ride"))

    vehicles = Vehicle.query.filter_by(owner_id=current_user.id).all()
    return render_template(
        "provider/post_ride.html",
        vehicles=vehicles,
        vehicle_types=VEHICLE_TYPES,
        today=date.today().isoformat(),
    )