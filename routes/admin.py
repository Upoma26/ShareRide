from flask import (
    Blueprint, render_template, request, flash, redirect, url_for,
    abort, send_from_directory, current_app,
)
from flask_login import current_user

from extensions import db
from models.user import User
from models.ride import Ride
from models.nid import NidReview, NidAccessLog
from utils.decorators import role_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

NID_STATUSES = ("pending", "verified", "rejected")


def get_member_or_404(user_id):
    user = db.get_or_404(User, user_id)
    if user.role == "admin":
        abort(404)
    return user


@admin_bp.route("/")
@role_required("admin")
def overview():
    members = User.query.filter(User.role != "admin")

    stats = {
        "total_users": members.count(),
        "seekers": members.filter(User.role == "seeker").count(),
        "providers": members.filter(User.role == "provider").count(),
        "pending_nid": members.filter(User.verification_status == "pending").count(),
        "restricted": members.filter(User.account_status.in_(["suspended", "blocked"])).count(),
        "total_rides": Ride.query.count(),
        "active_rides": Ride.query.filter(Ride.status.in_(["scheduled", "started"])).count(),
        "completed_rides": Ride.query.filter_by(status="completed").count(),
    }

    pending_users = (
        members.filter(User.verification_status == "pending")
        .order_by(User.created_at.asc())
        .limit(5)
        .all()
    )
    recent_users = members.order_by(User.created_at.desc()).limit(5).all()

    return render_template(
        "admin/overview.html",
        stats=stats,
        pending_users=pending_users,
        recent_users=recent_users,
    )


@admin_bp.route("/nid")
@role_required("admin")
def nid_list():
    status = request.args.get("status", "pending")
    if status not in NID_STATUSES:
        status = "pending"

    members = User.query.filter(User.role != "admin")
    users = (
        members.filter(User.verification_status == status)
        .order_by(User.created_at.asc())
        .all()
    )
    counts = {s: members.filter(User.verification_status == s).count() for s in NID_STATUSES}

    return render_template("admin/nid_list.html", users=users, status=status, counts=counts)


@admin_bp.route("/nid/<int:user_id>")
@role_required("admin")
def nid_review(user_id):
    user = get_member_or_404(user_id)
    reviews = (
        NidReview.query.filter_by(user_id=user.id)
        .order_by(NidReview.created_at.desc())
        .all()
    )
    access_logs = (
        NidAccessLog.query.filter_by(user_id=user.id)
        .order_by(NidAccessLog.accessed_at.desc())
        .limit(10)
        .all()
    )
    return render_template(
        "admin/nid_review.html",
        user=user,
        reviews=reviews,
        access_logs=access_logs,
    )


@admin_bp.route("/nid/<int:user_id>/file/<side>")
@role_required("admin")
def nid_file(user_id, side):
    if side not in ("front", "back"):
        abort(404)

    user = get_member_or_404(user_id)
    filename = user.nid_front if side == "front" else user.nid_back
    if not filename:
        abort(404)

    db.session.add(NidAccessLog(
        user_id=user.id,
        admin_id=current_user.id,
        side=side,
        ip_address=request.remote_addr,
    ))
    db.session.commit()

    response = send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)
    response.headers["Cache-Control"] = "no-store"
    return response


@admin_bp.route("/nid/<int:user_id>/decide", methods=["POST"])
@role_required("admin")
def nid_decide(user_id):
    user = get_member_or_404(user_id)
    decision = request.form.get("decision", "")
    reason = request.form.get("reason", "").strip()

    if decision not in ("verified", "rejected"):
        flash("Please choose approve or reject.", "danger")
        return redirect(url_for("admin.nid_review", user_id=user.id))

    if decision == "rejected" and len(reason) < 5:
        flash("Please write a reason for rejecting (at least 5 characters).", "danger")
        return redirect(url_for("admin.nid_review", user_id=user.id))

    user.verification_status = decision
    db.session.add(NidReview(
        user_id=user.id,
        admin_id=current_user.id,
        decision=decision,
        reason=reason or None,
    ))
    db.session.commit()

    if decision == "verified":
        flash(f"{user.full_name}'s NID has been approved.", "success")
    else:
        flash(f"{user.full_name}'s NID has been rejected.", "warning")
    return redirect(url_for("admin.nid_list"))