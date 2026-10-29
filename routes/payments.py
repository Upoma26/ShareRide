import re
from datetime import datetime

from flask import Blueprint, render_template, request, flash, redirect, url_for, abort
from flask_login import current_user, login_required

from extensions import db
from models.booking import Booking
from models.payment import Payment, PAYMENT_METHODS
from utils.decorators import role_required

payments_bp = Blueprint("payments", __name__, url_prefix="/payments")

TXN_PATTERN = re.compile(r"^[A-Z0-9]{6,30}$")
PAYABLE_STATUSES = ("onboard", "completed")


def make_receipt_number(payment):
    return f"SR-{payment.paid_at:%Y%m%d}-{payment.id:05d}"


@payments_bp.route("/booking/<int:booking_id>", methods=["GET", "POST"])
@role_required("seeker")
def pay(booking_id):
    booking = db.get_or_404(Booking, booking_id)
    if booking.seeker_id != current_user.id:
        abort(404)

    if booking.payment:
        flash("This booking is already paid.", "warning")
        return redirect(url_for("payments.receipt", payment_id=booking.payment.id))

    if booking.status not in PAYABLE_STATUSES:
        flash("You can pay after your trip starts.", "warning")
        return redirect(url_for("bookings.detail", booking_id=booking.id))

    if request.method == "POST":
        method = request.form.get("method", "")
        ref = request.form.get("transaction_ref", "").strip().upper()
        errors = []

        if method not in PAYMENT_METHODS:
            errors.append("Please choose a payment method.")
        elif method != "cash":
            if not TXN_PATTERN.match(ref):
                errors.append("Please enter a valid transaction ID (6 to 30 letters or numbers).")
            elif Payment.query.filter_by(transaction_ref=ref).first():
                errors.append("This transaction ID has already been used.")

        if errors:
            for error in errors:
                flash(error, "danger")
        else:
            payment = Payment(
                booking_id=booking.id,
                amount=booking.total_fare,
                method=method,
                status="paid",
                transaction_ref=ref if method != "cash" else None,
                paid_at=datetime.utcnow(),
            )
            db.session.add(payment)
            db.session.flush()
            payment.receipt_number = make_receipt_number(payment)
            db.session.commit()

            flash("Payment recorded. Here is your receipt.", "success")
            return redirect(url_for("payments.receipt", payment_id=payment.id))

    return render_template("payments/pay.html", booking=booking, methods=PAYMENT_METHODS)


@payments_bp.route("/<int:payment_id>/receipt")
@login_required
def receipt(payment_id):
    payment = db.get_or_404(Payment, payment_id)
    booking = payment.booking
    ride = booking.ride

    allowed = (
        current_user.id in (booking.seeker_id, ride.provider_id)
        or current_user.role == "admin"
    )
    if not allowed:
        abort(404)

    return render_template("payments/receipt.html", payment=payment, booking=booking, ride=ride)