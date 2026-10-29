from datetime import date, datetime

from flask import Blueprint, render_template, request, flash, redirect, url_for, abort
from flask_login import current_user

from extensions import db
from models.booking import Booking
from models.ride import Ride
from models.vehicle import Vehicle, VEHICLE_TYPES
from utils.decorators import role_required
from utils.seats import release_seats
from utils.trip_pin import check_pin, clear_pin, MAX_PIN_ATTEMPTS

provider_bp = Blueprint("provider", __name__, url_prefix="/provider")

MAX_SEATS = 14
MAX_FARE = 5000


def to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def validate_ride_fields(form):
    errors = []

    pickup = form.get("pickup", "").strip()
    destination = form.get("destination", "").strip()
    if len(pickup) < 2:
        errors.append("Please enter the pickup point.")
    if len(destination) < 2:
        errors.append("Please enter the destination.")
    if pickup and pickup.lower() == destination.lower():
        errors.append("Pickup and destination cannot be the same.")

    try:
        ride_date = datetime.strptime(form.get("ride_date", ""), "%Y-%m-%d").date()
    except ValueError:
        ride_date = None
        errors.append("Please choose a valid date.")

    try:
        ride_time = datetime.strptime(form.get("ride_time", ""), "%H:%M").time()
    except ValueError:
        ride_time = None
        errors.append("Please choose a valid time.")

    if ride_date and ride_time and datetime.combine(ride_date, ride_time) <= datetime.now():
        errors.append("The ride must be in the future.")

    total_seats = to_int(form.get("total_seats"))
    if total_seats is None or not 1 <= total_seats <= MAX_SEATS:
        errors.append(f"Seats must be between 1 and {MAX_SEATS}.")

    fare = to_int(form.get("fare_per_seat"))
    if fare is None or not 0 <= fare <= MAX_FARE:
        errors.append(f"Fare must be between 0 and {MAX_FARE} taka.")

    data = {
        "pickup": pickup,
        "destination": destination,
        "ride_date": ride_date,
        "ride_time": ride_time,
        "total_seats": total_seats,
        "fare_per_seat": fare,
        "notes": form.get("notes", "").strip()[:300] or None,
    }
    return data, errors


def get_vehicle_from_form(form):
    vehicle_id = form.get("vehicle_id")
    if vehicle_id:
        vehicle = Vehicle.query.filter_by(id=to_int(vehicle_id), owner_id=current_user.id).first()
        if vehicle is None:
            return None, ["Please choose one of your own vehicles."]
        return vehicle, []

    errors = []
    vehicle_type = form.get("vehicle_type", "")
    plate = form.get("plate_number", "").strip().upper()
    brand = form.get("brand", "").strip()
    model = form.get("model", "").strip()
    color = form.get("color", "").strip() or None
    capacity = to_int(form.get("seat_capacity"))

    if vehicle_type not in VEHICLE_TYPES:
        errors.append("Please choose a vehicle type.")
    if len(plate) < 4:
        errors.append("Please enter the number plate.")
    elif Vehicle.query.filter_by(plate_number=plate).first():
        errors.append("A vehicle with this number plate is already registered.")
    if not brand:
        errors.append("Please enter the vehicle brand.")
    if not model:
        errors.append("Please enter the vehicle model.")
    if capacity is None or not 1 <= capacity <= MAX_SEATS:
        errors.append(f"Seat capacity must be between 1 and {MAX_SEATS}.")

    if errors:
        return None, errors

    vehicle = Vehicle(
        owner_id=current_user.id,
        vehicle_type=vehicle_type,
        plate_number=plate,
        brand=brand,
        model=model,
        color=color,
        seat_capacity=capacity,
    )
    return vehicle, []


def get_own_ride_or_404(ride_id):
    ride = db.get_or_404(Ride, ride_id)
    if ride.provider_id != current_user.id:
        abort(404)
    return ride


def render_post_form():
    vehicles = Vehicle.query.filter_by(owner_id=current_user.id).all()
    return render_template(
        "provider/post_ride.html",
        vehicles=vehicles,
        vehicle_types=VEHICLE_TYPES,
        today=date.today().isoformat(),
    )


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
        if not current_user.is_verified:
            flash("You can post rides after an admin verifies your NID.", "warning")
            return redirect(url_for("provider.dashboard"))

        vehicle, vehicle_errors = get_vehicle_from_form(request.form)
        data, ride_errors = validate_ride_fields(request.form)
        errors = vehicle_errors + ride_errors

        if vehicle and data["total_seats"] and data["total_seats"] > vehicle.seat_capacity:
            errors.append(f"This vehicle has only {vehicle.seat_capacity} seats.")

        if errors:
            for error in errors:
                flash(error, "danger")
            return render_post_form()

        ride = Ride(
            provider_id=current_user.id,
            vehicle=vehicle,
            available_seats=data["total_seats"],
            **data,
        )
        db.session.add(ride)
        db.session.commit()

        flash("Your ride has been posted.", "success")
        return redirect(url_for("provider.dashboard"))

    return render_post_form()


@provider_bp.route("/rides/<int:ride_id>/edit", methods=["GET", "POST"])
@role_required("provider")
def edit_ride(ride_id):
    ride = get_own_ride_or_404(ride_id)

    if ride.status != "scheduled":
        flash("Only scheduled rides can be edited.", "warning")
        return redirect(url_for("provider.dashboard"))

    if request.method == "POST":
        data, errors = validate_ride_fields(request.form)
        booked = ride.booked_seats

        if data["total_seats"] is not None:
            if data["total_seats"] < booked:
                errors.append(f"{booked} seats are already booked. You cannot offer fewer seats than that.")
            if data["total_seats"] > ride.vehicle.seat_capacity:
                errors.append(f"This vehicle has only {ride.vehicle.seat_capacity} seats.")

        if errors:
            for error in errors:
                flash(error, "danger")
        else:
            for key, value in data.items():
                setattr(ride, key, value)
            ride.available_seats = data["total_seats"] - booked
            db.session.commit()
            flash("Ride updated.", "success")
            return redirect(url_for("provider.dashboard"))

    return render_template(
        "provider/edit_ride.html",
        ride=ride,
        today=date.today().isoformat(),
    )


@provider_bp.route("/rides/<int:ride_id>/cancel", methods=["POST"])
@role_required("provider")
def cancel_ride(ride_id):
    ride = get_own_ride_or_404(ride_id)

    if ride.status != "scheduled":
        flash("Only scheduled rides can be cancelled.", "warning")
        return redirect(url_for("provider.dashboard"))

    now = datetime.utcnow()
    affected = 0
    for booking in ride.bookings:
        if booking.is_active:
            booking.status = "cancelled"
            booking.cancelled_at = now
            affected += 1

    ride.status = "cancelled"
    db.session.commit()

    if affected:
        flash(f"Ride cancelled. {affected} passenger booking(s) were cancelled too.", "warning")
    else:
        flash("Ride cancelled.", "warning")
    return redirect(url_for("provider.dashboard"))


@provider_bp.route("/rides/<int:ride_id>/requests")
@role_required("provider")
def ride_requests(ride_id):
    ride = get_own_ride_or_404(ride_id)
    bookings = (
        Booking.query.filter_by(ride_id=ride.id)
        .order_by(Booking.created_at.asc())
        .all()
    )
    pending = [b for b in bookings if b.status == "pending"]
    handled = [b for b in bookings if b.status != "pending"]

    return render_template(
        "provider/requests.html",
        ride=ride,
        pending=pending,
        handled=handled,
    )


@provider_bp.route("/bookings/<int:booking_id>/decide", methods=["POST"])
@role_required("provider")
def decide_booking(booking_id):
    booking = db.get_or_404(Booking, booking_id)
    ride = booking.ride
    if ride.provider_id != current_user.id:
        abort(404)

    back = redirect(url_for("provider.ride_requests", ride_id=ride.id))
    decision = request.form.get("decision", "")

    if booking.status != "pending":
        flash("This request has already been handled.", "warning")
        return back

    if ride.status != "scheduled" or datetime.combine(ride.ride_date, ride.ride_time) <= datetime.now():
        flash("This ride has already left, so requests cannot be changed.", "warning")
        return back

    if decision == "accept":
        booking.status = "accepted"
        message = f"Accepted {booking.seeker.full_name}'s request for {booking.seats} seat(s)."
        category = "success"
    elif decision == "reject":
        release_seats(ride.id, booking.seats)
        booking.status = "rejected"
        message = f"Rejected {booking.seeker.full_name}'s request. The seats are open again."
        category = "warning"
    else:
        flash("Please choose accept or reject.", "danger")
        return back

    booking.decided_at = datetime.utcnow()
    db.session.commit()
    flash(message, category)
    return back


@provider_bp.route("/bookings/<int:booking_id>/verify-pin", methods=["POST"])
@role_required("provider")
def verify_pin(booking_id):
    booking = db.get_or_404(Booking, booking_id)
    ride = booking.ride
    if ride.provider_id != current_user.id:
        abort(404)

    back = redirect(url_for("provider.ride_requests", ride_id=ride.id))

    if booking.status != "accepted" or ride.status not in ("scheduled", "started"):
        flash("This passenger cannot be checked in.", "warning")
        return back

    pin = request.form.get("pin", "").strip()
    if not (pin.isdigit() and len(pin) == 4):
        flash("Please enter the 4-digit Trip PIN.", "danger")
        return back

    result = check_pin(booking, pin)

    if result == "ok":
        clear_pin(booking)
        booking.status = "onboard"
        if ride.status == "scheduled":
            ride.status = "started"
            ride.started_at = datetime.utcnow()
        db.session.commit()
        flash(f"PIN correct. {booking.seeker.full_name} is on board.", "success")
        return back

    db.session.commit()
    messages = {
        "missing": "The passenger has not opened their Trip PIN yet.",
        "wrong": f"Wrong PIN. {MAX_PIN_ATTEMPTS - (booking.pin_attempts or 0)} attempt(s) left.",
        "locked": "Too many wrong attempts. Ask the passenger to open a new Trip PIN.",
    }
    flash(messages[result], "danger")
    return back