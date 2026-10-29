from flask import Blueprint, render_template, request, flash, redirect, url_for, abort
from flask_login import current_user, login_required

from extensions import db
from models.complaint import Complaint, COMPLAINT_CATEGORIES
from models.ride import Ride

complaints_bp = Blueprint("complaints", __name__, url_prefix="/complaints")

MAX_OPEN_COMPLAINTS = 5
OPEN_STATUSES = ("open", "investigating")


def to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def passengers_of(ride):
    return [
        b.seeker for b in ride.bookings
        if b.status in ("accepted", "onboard", "completed")
    ]


def ride_role(ride):
    if ride.provider_id == current_user.id:
        return "driver"
    if any(p.id == current_user.id for p in passengers_of(ride)):
        return "passenger"
    return None


@complaints_bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    if current_user.role == "admin":
        abort(404)

    ride = None
    role = None
    people = []

    ride_id = to_int(request.values.get("ride_id"))
    if ride_id:
        ride = db.get_or_404(Ride, ride_id)
        role = ride_role(ride)
        if role is None:
            abort(404)
        people = [ride.provider] if role == "passenger" else passengers_of(ride)

    if request.method == "POST":
        category = request.form.get("category", "")
        subject = request.form.get("subject", "").strip()
        description = request.form.get("description", "").strip()
        against_id = to_int(request.form.get("against_id"))

        errors = []
        if category not in COMPLAINT_CATEGORIES:
            errors.append("Please choose what the problem is about.")
        if not 5 <= len(subject) <= 120:
            errors.append("Subject must be 5 to 120 characters.")
        if not 20 <= len(description) <= 2000:
            errors.append("Please describe the problem in 20 to 2000 characters.")
        if against_id and against_id not in [p.id for p in people]:
            errors.append("Please choose a person from this ride.")

        open_count = Complaint.query.filter(
            Complaint.complainant_id == current_user.id,
            Complaint.status.in_(OPEN_STATUSES),
        ).count()
        if open_count >= MAX_OPEN_COMPLAINTS:
            errors.append("You already have 5 open complaints. Please wait for them to be reviewed.")

        if errors:
            for error in errors:
                flash(error, "danger")
        else:
            complaint = Complaint(
                complainant_id=current_user.id,
                against_id=against_id,
                ride_id=ride.id if ride else None,
                category=category,
                subject=subject,
                description=description,
            )
            db.session.add(complaint)
            db.session.commit()
            flash(f"Complaint #{complaint.id} submitted. Our team will review it soon.", "success")
            return redirect(url_for("complaints.detail", complaint_id=complaint.id))

    return render_template(
        "complaints/new.html",
        ride=ride,
        role=role,
        people=people,
        categories=COMPLAINT_CATEGORIES,
    )


@complaints_bp.route("/mine")
@login_required
def mine():
    complaints = (
        Complaint.query.filter_by(complainant_id=current_user.id)
        .order_by(Complaint.created_at.desc())
        .all()
    )
    return render_template("complaints/mine.html", complaints=complaints)


@complaints_bp.route("/<int:complaint_id>")
@login_required
def detail(complaint_id):
    complaint = db.get_or_404(Complaint, complaint_id)
    if complaint.complainant_id != current_user.id:
        abort(404)
    return render_template("complaints/detail.html", c=complaint)