from flask import Blueprint, render_template

from models.user import User
from models.ride import Ride
from utils.decorators import role_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


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