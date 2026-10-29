from flask import Blueprint, render_template, request, flash, redirect, url_for, abort
from flask_login import current_user, login_required
from sqlalchemy import func

from extensions import db
from models.booking import Booking
from models.rating import Rating

ratings_bp = Blueprint("ratings", __name__, url_prefix="/ratings")


def to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def refresh_average(user):
    average = (
        db.session.query(func.avg(Rating.stars))
        .filter(Rating.ratee_id == user.id)
        .scalar()
    )
    user.rating = round(float(average), 2) if average else 0.0


@ratings_bp.route("/booking/<int:booking_id>", methods=["GET", "POST"])
@login_required
def rate(booking_id):
    booking = db.get_or_404(Booking, booking_id)
    ride = booking.ride

    if current_user.id == booking.seeker_id:
        ratee = ride.provider
        role = "passenger"
        back = url_for("bookings.detail", booking_id=booking.id)
    elif current_user.id == ride.provider_id:
        ratee = booking.seeker
        role = "driver"
        back = url_for("provider.ride_requests", ride_id=ride.id)
    else:
        abort(404)

    if booking.status != "completed":
        flash("You can rate only after the trip is completed.", "warning")
        return redirect(back)

    if Rating.query.filter_by(booking_id=booking.id, rater_id=current_user.id).first():
        flash("You have already rated this trip.", "warning")
        return redirect(back)

    if request.method == "POST":
        stars = to_int(request.form.get("stars"))
        comment = request.form.get("comment", "").strip()[:300] or None

        if stars is None or not 1 <= stars <= 5:
            flash("Please choose from 1 to 5 stars.", "danger")
        else:
            db.session.add(Rating(
                booking_id=booking.id,
                rater_id=current_user.id,
                ratee_id=ratee.id,
                stars=stars,
                comment=comment,
            ))
            db.session.flush()
            refresh_average(ratee)
            db.session.commit()
            flash("Thank you! Your rating has been saved.", "success")
            return redirect(back)

    return render_template(
        "ratings/rate.html",
        booking=booking,
        ride=ride,
        ratee=ratee,
        role=role,
        back=back,
    )