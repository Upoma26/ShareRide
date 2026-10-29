from datetime import datetime

from flask import Blueprint, render_template, request, flash, redirect, url_for, abort
from flask_login import current_user

from extensions import db
from models.booking import Booking
from models.ride import Ride
from utils.decorators import role_required
from utils.seats import reserve_seats, release_seats
from utils.trip_pin import issue_pin

bookings_bp = Blueprint("bookings", __name__, url_prefix="/bookings")


def to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def ride_has_left(ride):
    return datetime.combine(ride.ride_date, ride.ride_time) <= datetime.now()


def find_active_booking(ride_id, seeker_id):
    return Booking.query.filter(
        Booking.ride_id == ride_id,
        Booking.seeker_id == seeker_id,
        Booking.status.in_(["pending", "accepted"]),
    ).first()


@bookings_bp.route("/mine")
@role_required("seeker")
def mine():
    bookings = (
        Booking.query.filter_by(seeker_id=current_user.id)
        .order_by(Booking.created_at.desc())
        .all()
    )

    upcoming = []
    past = []
    for booking in bookings:
        ride = booking.ride
        still_ahead = ride.status == "started" or not ride_has_left(ride)
        if booking.status in ("pending", "accepted", "onboard") and ride.status in ("scheduled", "started") and still_ahead:
            upcoming.append(booking)
        else:
            past.append(booking)

    upcoming.sort(key=lambda b: (b.ride.ride_date, b.ride.ride_time))

    return render_template("bookings/mine.html", upcoming=upcoming, past=past)


@bookings_bp.route("/ride/<int:ride_id>", methods=["POST"])
@role_required("seeker")
def create(ride_id):
    ride = db.get_or_404(Ride, ride_id)
    back = redirect(url_for("rides.detail", ride_id=ride.id))

    if not current_user.is_verified:
        flash("You can book rides after an admin verifies your NID.", "warning")
        return back

    if ride.provider_id == current_user.id:
        flash("You cannot book your own ride.", "danger")
        return back

    if (
        ride.status != "scheduled"
        or ride_has_left(ride)
        or ride.provider.account_status != "active"
    ):
        flash("This ride is no longer available.", "warning")
        return back

    if find_active_booking(ride.id, current_user.id):
        flash("You already have a booking on this ride.", "warning")
        return back

    seats = to_int(request.form.get("seats"))
    if seats is None or seats < 1:
        flash("Please choose how many seats you need.", "danger")
        return back

    if not reserve_seats(ride.id, seats):
        db.session.rollback()
        flash("Sorry, there are not enough seats left on this ride.", "danger")
        return back

    booking = Booking(
        ride_id=ride.id,
        seeker_id=current_user.id,
        seats=seats,
        total_fare=seats * ride.fare_per_seat,
    )
    db.session.add(booking)
    db.session.commit()

    flash("Booking request sent. The driver will accept or reject it soon.", "success")
    return redirect(url_for("bookings.detail", booking_id=booking.id))


@bookings_bp.route("/<int:booking_id>")
@role_required("seeker")
def detail(booking_id):
    booking = db.get_or_404(Booking, booking_id)
    if booking.seeker_id != current_user.id:
        abort(404)

    ride = booking.ride
    can_cancel = booking.is_active and ride.status == "scheduled" and not ride_has_left(ride)
    can_show_pin = booking.status == "accepted" and ride.status in ("scheduled", "started")

    return render_template(
        "bookings/confirmation.html",
        booking=booking,
        ride=ride,
        can_cancel=can_cancel,
        can_show_pin=can_show_pin,
    )


@bookings_bp.route("/<int:booking_id>/pin", methods=["POST"])
@role_required("seeker")
def reveal_pin(booking_id):
    booking = db.get_or_404(Booking, booking_id)
    if booking.seeker_id != current_user.id:
        abort(404)

    if booking.status != "accepted" or booking.ride.status not in ("scheduled", "started"):
        flash("A Trip PIN is only available for accepted bookings.", "warning")
        return redirect(url_for("bookings.detail", booking_id=booking.id))

    pin = issue_pin(booking)
    db.session.commit()
    return render_template("bookings/pin.html", booking=booking, pin=pin)


@bookings_bp.route("/<int:booking_id>/cancel", methods=["POST"])
@role_required("seeker")
def cancel(booking_id):
    booking = db.get_or_404(Booking, booking_id)
    if booking.seeker_id != current_user.id:
        abort(404)

    ride = booking.ride

    if not booking.is_active:
        flash("This booking can no longer be cancelled.", "warning")
    elif ride.status != "scheduled" or ride_has_left(ride):
        flash("The ride has already started, so this booking cannot be cancelled.", "warning")
    else:
        release_seats(ride.id, booking.seats)
        booking.status = "cancelled"
        booking.cancelled_at = datetime.utcnow()
        db.session.commit()
        flash("Your booking has been cancelled and the seats were released.", "success")

    if request.form.get("back") == "mine":
        return redirect(url_for("bookings.mine"))
    return redirect(url_for("rides.detail", ride_id=ride.id))