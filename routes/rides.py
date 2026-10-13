from datetime import date, datetime

from flask import Blueprint, render_template, request
from flask_login import current_user
from sqlalchemy import or_

from models.ride import Ride
from models.user import User

rides_bp = Blueprint("rides", __name__, url_prefix="/rides")

MAX_SEATS = 14
MAX_RESULTS = 50


def to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def search_rides(pickup, destination, ride_date, seats):
    now = datetime.now()

    query = (
        Ride.query.join(User, Ride.provider_id == User.id)
        .filter(
            Ride.status == "scheduled",
            Ride.available_seats >= seats,
            User.account_status == "active",
            User.verification_status == "verified",
        )
    )

    if pickup:
        query = query.filter(Ride.pickup.ilike(f"%{pickup}%"))
    if destination:
        query = query.filter(Ride.destination.ilike(f"%{destination}%"))

    if ride_date:
        query = query.filter(Ride.ride_date == ride_date)
    else:
        query = query.filter(Ride.ride_date >= now.date())

    query = query.filter(or_(Ride.ride_date > now.date(), Ride.ride_time > now.time()))

    if current_user.is_authenticated:
        query = query.filter(Ride.provider_id != current_user.id)

    return (
        query.order_by(Ride.ride_date.asc(), Ride.ride_time.asc())
        .limit(MAX_RESULTS)
        .all()
    )


@rides_bp.route("/search")
def search():
    pickup = request.args.get("pickup", "").strip()[:100]
    destination = request.args.get("destination", "").strip()[:100]
    date_text = request.args.get("date", "").strip()

    seats = to_int(request.args.get("seats")) or 1
    seats = max(1, min(seats, MAX_SEATS))

    errors = []
    ride_date = None
    if date_text:
        try:
            ride_date = datetime.strptime(date_text, "%Y-%m-%d").date()
        except ValueError:
            errors.append("Please choose a valid date.")

    searched = bool(pickup or destination or date_text)
    rides = []
    if searched and not errors:
        rides = search_rides(pickup, destination, ride_date, seats)

    return render_template(
        "rides/search.html",
        rides=rides,
        searched=searched,
        errors=errors,
        pickup=pickup,
        destination=destination,
        date_text=date_text,
        seats=seats,
        today=date.today().isoformat(),
    )