from datetime import date, datetime

from flask import Blueprint, render_template, request, abort
from flask_login import current_user
from sqlalchemy import or_

from extensions import db
from models.booking import Booking
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


def search_rides(pickup, destination, ride_date, seats, after_time=None):
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

    if after_time:
        query = query.filter(Ride.ride_time >= after_time)

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
    time_text = request.args.get("time", "").strip()

    seats = to_int(request.args.get("seats")) or 1
    seats = max(1, min(seats, MAX_SEATS))

    errors = []

    ride_date = None
    if date_text:
        try:
            ride_date = datetime.strptime(date_text, "%Y-%m-%d").date()
        except ValueError:
            errors.append("Please choose a valid date.")

    after_time = None
    if time_text:
        try:
            after_time = datetime.strptime(time_text, "%H:%M").time()
        except ValueError:
            errors.append("Please choose a valid time.")

    searched = bool(pickup or destination or date_text or time_text)
    rides = []
    if searched and not errors:
        rides = search_rides(pickup, destination, ride_date, seats, after_time)

    return render_template(
        "rides/search.html",
        rides=rides,
        searched=searched,
        errors=errors,
        pickup=pickup,
        destination=destination,
        date_text=date_text,
        time_text=time_text,
        seats=seats,
        today=date.today().isoformat(),
    )


@rides_bp.route("/<int:ride_id>")
def detail(ride_id):
    ride = db.get_or_404(Ride, ride_id)
    provider = ride.provider

    if provider.account_status != "active":
        abort(404)

    is_owner = current_user.is_authenticated and current_user.id == ride.provider_id
    is_past = datetime.combine(ride.ride_date, ride.ride_time) <= datetime.now()

    my_booking = None
    if current_user.is_authenticated:
        my_booking = (
            Booking.query.filter(
                Booking.ride_id == ride.id,
                Booking.seeker_id == current_user.id,
                Booking.status.in_(["pending", "accepted"]),
            )
            .first()
        )

    can_book = (
        ride.status == "scheduled"
        and not is_past
        and ride.available_seats > 0
        and provider.is_verified
        and not is_owner
        and my_booking is None
    )

    return render_template(
        "rides/detail.html",
        ride=ride,
        provider=provider,
        is_owner=is_owner,
        is_past=is_past,
        can_book=can_book,
        my_booking=my_booking,
    )