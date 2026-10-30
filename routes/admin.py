import csv
import io
from datetime import datetime, timedelta


from flask import (
    Blueprint, render_template, request, flash, redirect, url_for,
    abort, send_from_directory, current_app, Response,
)
from flask_login import current_user
from sqlalchemy import or_

from extensions import db
from models.user import User
from models.ride import Ride, RIDE_STATUSES
from models.nid import NidReview, NidAccessLog
from models.sos import SosAlert
from models.complaint import Complaint, COMPLAINT_CATEGORIES, COMPLAINT_STATUSES
from models.audit import AuditLog
from utils.decorators import role_required
from utils.audit import log_action

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

NID_STATUSES = ("pending", "verified", "rejected")

ACCOUNT_ACTIONS = {
    "suspend": "suspended",
    "block": "blocked",
    "reinstate": "active",
}

COMPLAINT_ACTIONS = {
    "none": "No action needed",
    "warned": "Warning given",
    "suspended": "Account suspended",
    "blocked": "Account blocked",
}

COMPLAINT_ACCOUNT_ACTIONS = {
    "suspended": "suspend",
    "blocked": "block",
}

OPEN_COMPLAINT_STATUSES = ("open", "investigating")


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
        "open_complaints": Complaint.query.filter(Complaint.status.in_(OPEN_COMPLAINT_STATUSES)).count(),
    }

    pending_users = (
        members.filter(User.verification_status == "pending")
        .order_by(User.created_at.asc())
        .limit(5)
        .all()
    )
    recent_users = members.order_by(User.created_at.desc()).limit(5).all()
    open_sos = SosAlert.query.filter_by(status="open").order_by(SosAlert.created_at.desc()).all()

    return render_template(
        "admin/overview.html",
        stats=stats,
        pending_users=pending_users,
        recent_users=recent_users,
        open_sos=open_sos,
    )


@admin_bp.route("/users")
@role_required("admin")
def users():
    q = request.args.get("q", "").strip()[:100]
    role = request.args.get("role", "")
    status = request.args.get("status", "")

    query = User.query.filter(User.role != "admin")

    if q:
        like = f"%{q}%"
        query = query.filter(or_(
            User.full_name.ilike(like),
            User.phone.ilike(like),
            User.email.ilike(like),
        ))
    if role in ("seeker", "provider"):
        query = query.filter(User.role == role)
    if status in ("active", "suspended", "blocked"):
        query = query.filter(User.account_status == status)

    members = query.order_by(User.created_at.desc()).limit(200).all()

    return render_template(
        "admin/users.html",
        members=members,
        q=q,
        role=role,
        status=status,
    )


@admin_bp.route("/rides")
@role_required("admin")
def rides():
    status = request.args.get("status", "")
    date_text = request.args.get("date", "").strip()
    q = request.args.get("q", "").strip()[:100]

    query = Ride.query

    if status in RIDE_STATUSES:
        query = query.filter(Ride.status == status)

    if date_text:
        try:
            ride_date = datetime.strptime(date_text, "%Y-%m-%d").date()
            query = query.filter(Ride.ride_date == ride_date)
        except ValueError:
            flash("Please choose a valid date.", "danger")

    if q:
        like = f"%{q}%"
        query = query.filter(or_(Ride.pickup.ilike(like), Ride.destination.ilike(like)))

    ride_list = (
        query.order_by(Ride.ride_date.desc(), Ride.ride_time.desc())
        .limit(200)
        .all()
    )
    counts = {s: Ride.query.filter_by(status=s).count() for s in RIDE_STATUSES}

    return render_template(
        "admin/rides.html",
        ride_list=ride_list,
        counts=counts,
        status=status,
        date_text=date_text,
        q=q,
    )


@admin_bp.route("/complaints")
@role_required("admin")
def complaints():
    status = request.args.get("status", "open")
    category = request.args.get("category", "")
    q = request.args.get("q", "").strip()[:100]

    query = Complaint.query

    if status in COMPLAINT_STATUSES:
        query = query.filter(Complaint.status == status)
    else:
        status = ""

    if category in COMPLAINT_CATEGORIES:
        query = query.filter(Complaint.category == category)
    else:
        category = ""

    if q:
        query = query.filter(Complaint.subject.ilike(f"%{q}%"))

    complaint_list = query.order_by(Complaint.created_at.desc()).limit(200).all()
    counts = {s: Complaint.query.filter_by(status=s).count() for s in COMPLAINT_STATUSES}

    return render_template(
        "admin/complaints.html",
        complaint_list=complaint_list,
        counts=counts,
        status=status,
        category=category,
        q=q,
        categories=COMPLAINT_CATEGORIES,
    )


@admin_bp.route("/complaints/<int:complaint_id>")
@role_required("admin")
def complaint_detail(complaint_id):
    c = db.get_or_404(Complaint, complaint_id)

    other_complaints = []
    if c.against_id:
        other_complaints = (
            Complaint.query.filter(
                Complaint.against_id == c.against_id,
                Complaint.id != c.id,
            )
            .order_by(Complaint.created_at.desc())
            .limit(10)
            .all()
        )

    return render_template(
        "admin/complaint_detail.html",
        c=c,
        other_complaints=other_complaints,
        actions=COMPLAINT_ACTIONS,
    )


@admin_bp.route("/complaints/<int:complaint_id>/handle", methods=["POST"])
@role_required("admin")
def handle_complaint(complaint_id):
    c = db.get_or_404(Complaint, complaint_id)
    back = redirect(url_for("admin.complaint_detail", complaint_id=c.id))

    if not c.is_open:
        flash("This complaint is already closed.", "warning")
        return back

    new_status = request.form.get("status", "")
    action = request.form.get("action", "none")
    note = request.form.get("admin_note", "").strip()[:500]

    errors = []
    if new_status not in ("investigating", "resolved", "dismissed"):
        errors.append("Please choose a valid status.")
    if action not in COMPLAINT_ACTIONS:
        errors.append("Please choose a valid action.")
    if new_status in ("resolved", "dismissed") and len(note) < 5:
        errors.append("Please write a reply to the user (at least 5 characters).")
    if action != "none":
        if new_status != "resolved":
            errors.append("An action can only be taken when resolving a complaint.")
        if c.against is None or c.against.role == "admin":
            errors.append("This complaint is not about a specific user, so no action can be taken.")

    if errors:
        for error in errors:
            flash(error, "danger")
        return back

    c.status = new_status
    c.handled_by = current_user.id
    if note:
        c.admin_note = note
    if new_status in ("resolved", "dismissed"):
        c.action_taken = action
        c.resolved_at = datetime.utcnow()

    if action in COMPLAINT_ACCOUNT_ACTIONS:
        target = c.against
        new_account_status = ACCOUNT_ACTIONS[COMPLAINT_ACCOUNT_ACTIONS[action]]
        if target.account_status != new_account_status:
            old_account_status = target.account_status
            target.account_status = new_account_status
            log_action(
                f"account_{COMPLAINT_ACCOUNT_ACTIONS[action]}",
                "user",
                target.id,
                f"{old_account_status} -> {new_account_status}: complaint #{c.id}",
            )

    details = f"action: {action}"
    if note:
        details += f" | {note}"
    log_action(f"complaint_{new_status}", "complaint", c.id, details)
    db.session.commit()

    flash(f"Complaint #{c.id} marked as {new_status}.", "success")
    return back

AUDIT_GROUPS = {
    "account": "Account actions",
    "nid": "NID decisions",
    "complaint": "Complaints",
    "sos": "SOS alerts",
}

AUDIT_LABELS = {
    "account_suspend": "Account suspended",
    "account_block": "Account blocked",
    "account_reinstate": "Account reinstated",
    "nid_verified": "NID approved",
    "nid_rejected": "NID rejected",
    "sos_resolved": "SOS resolved",
    "complaint_investigating": "Complaint investigating",
    "complaint_resolved": "Complaint resolved",
    "complaint_dismissed": "Complaint dismissed",
}

AUDIT_PER_PAGE = 50


def parse_date(text):
    try:
        return datetime.strptime(text, "%Y-%m-%d")
    except (TypeError, ValueError):
        return None


def audit_query(args):
    group = args.get("group", "")
    admin_id = args.get("admin", type=int)
    date_from = parse_date(args.get("from", "").strip())
    date_to = parse_date(args.get("to", "").strip())
    q = args.get("q", "").strip()[:100]

    query = AuditLog.query

    if group in AUDIT_GROUPS:
        query = query.filter(AuditLog.action.like(f"{group}\\_%", escape="\\"))
    else:
        group = ""
    if admin_id:
        query = query.filter(AuditLog.admin_id == admin_id)
    if date_from:
        query = query.filter(AuditLog.created_at >= date_from)
    if date_to:
        query = query.filter(AuditLog.created_at < date_to + timedelta(days=1))
    if q:
        query = query.filter(AuditLog.details.ilike(f"%{q}%"))

    filters = {
        "group": group,
        "admin": admin_id or "",
        "from": date_from.strftime("%Y-%m-%d") if date_from else "",
        "to": date_to.strftime("%Y-%m-%d") if date_to else "",
        "q": q,
    }
    return query.order_by(AuditLog.created_at.desc(), AuditLog.id.desc()), filters


@admin_bp.route("/audit")
@role_required("admin")
def audit():
    query, filters = audit_query(request.args)
    page = max(request.args.get("page", 1, type=int), 1)
    pagination = query.paginate(page=page, per_page=AUDIT_PER_PAGE, error_out=False)
    admins = User.query.filter_by(role="admin").order_by(User.full_name).all()
    link_args = {k: v for k, v in filters.items() if v}

    return render_template(
        "admin/audit.html",
        logs=pagination.items,
        pagination=pagination,
        filters=filters,
        link_args=link_args,
        admins=admins,
        groups=AUDIT_GROUPS,
        labels=AUDIT_LABELS,
    )


@admin_bp.route("/audit/export")
@role_required("admin")
def audit_export():
    query, _ = audit_query(request.args)
    rows = query.limit(5000).all()

    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["Time (UTC)", "Admin", "Action", "Target", "Target ID", "Details", "IP address"])
    for log in rows:
        writer.writerow([
            log.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            log.admin.full_name,
            AUDIT_LABELS.get(log.action, log.action),
            log.target_type,
            log.target_id,
            log.details or "",
            log.ip_address or "",
        ])

    filename = f"shareride-audit-{datetime.utcnow():%Y%m%d}.csv"
    return Response(
        "\ufeff" + out.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )

@admin_bp.route("/nid")
@role_required("admin")
def nid_list():
    status = request.args.get("status", "pending")
    if status not in NID_STATUSES:
        status = "pending"

    members = User.query.filter(User.role != "admin")
    users_list = (
        members.filter(User.verification_status == status)
        .order_by(User.created_at.asc())
        .all()
    )
    counts = {s: members.filter(User.verification_status == s).count() for s in NID_STATUSES}

    return render_template("admin/nid_list.html", users=users_list, status=status, counts=counts)


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
    log_action(f"nid_{decision}", "user", user.id, reason or None)
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


@admin_bp.route("/users/<int:user_id>/status", methods=["POST"])
@role_required("admin")
def change_account_status(user_id):
    user = get_member_or_404(user_id)
    action = request.form.get("action", "")
    reason = request.form.get("reason", "").strip()
    back = redirect(url_for("admin.nid_review", user_id=user.id))

    if action not in ACCOUNT_ACTIONS:
        flash("Please choose a valid action.", "danger")
        return back

    new_status = ACCOUNT_ACTIONS[action]
    if user.account_status == new_status:
        flash(f"This account is already {new_status}.", "warning")
        return back

    if action != "reinstate" and len(reason) < 5:
        flash("Please write a reason (at least 5 characters).", "danger")
        return back

    old_status = user.account_status
    user.account_status = new_status
    details = f"{old_status} -> {new_status}"
    if reason:
        details += f": {reason}"
    log_action(f"account_{action}", "user", user.id, details)
    db.session.commit()

    if action == "reinstate":
        flash(f"{user.full_name}'s account is active again.", "success")
    else:
        flash(f"{user.full_name}'s account has been {new_status}.", "warning")
    return back


@admin_bp.route("/sos/<int:alert_id>/resolve", methods=["POST"])
@role_required("admin")
def resolve_sos(alert_id):
    alert = db.get_or_404(SosAlert, alert_id)
    if alert.status == "open":
        alert.status = "resolved"
        alert.resolved_at = datetime.utcnow()
        alert.resolved_by = current_user.id
        log_action("sos_resolved", "sos", alert.id, f"Ride {alert.ride_id}")
        db.session.commit()
        flash("SOS alert marked as resolved.", "success")
    return redirect(url_for("admin.overview"))