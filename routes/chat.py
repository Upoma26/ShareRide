from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, flash, redirect, url_for, abort, jsonify
from flask_login import current_user, login_required

from extensions import db
from models.message import Message, CHAT_OPEN_HOURS, MAX_MESSAGE_LENGTH
from models.ride import Ride

chat_bp = Blueprint("chat", __name__, url_prefix="/chat")

MEMBER_STATUSES = ("accepted", "onboard", "completed")
PAGE_SIZE = 100


def to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def chat_members(ride):
    members = [ride.provider]
    for booking in ride.bookings:
        if booking.status in MEMBER_STATUSES:
            members.append(booking.seeker)
    return members


def chat_role(ride):
    if ride.provider_id == current_user.id:
        return "driver"
    for booking in ride.bookings:
        if booking.seeker_id == current_user.id and booking.status in MEMBER_STATUSES:
            return "passenger"
    if current_user.role == "admin":
        return "admin"
    return None


def closes_at(ride):
    if ride.status == "completed" and ride.completed_at:
        return ride.completed_at + timedelta(hours=CHAT_OPEN_HOURS)
    return None


def is_open(ride):
    if ride.status == "cancelled":
        return False
    end = closes_at(ride)
    return end is None or datetime.utcnow() < end


def closed_reason(ride):
    if ride.status == "cancelled":
        return "This ride was cancelled, so the chat is closed."
    return f"This chat closed {CHAT_OPEN_HOURS} hours after the trip ended."


def get_chat_or_404(ride_id):
    ride = db.get_or_404(Ride, ride_id)
    role = chat_role(ride)
    if role is None:
        abort(404)
    return ride, role


@chat_bp.route("/ride/<int:ride_id>", methods=["GET", "POST"])
@login_required
def room(ride_id):
    ride, role = get_chat_or_404(ride_id)
    chat_open = is_open(ride)
    can_send = chat_open and role != "admin"

    if request.method == "POST":
        if not can_send:
            flash("You cannot send messages in this chat.", "warning")
            return redirect(url_for("chat.room", ride_id=ride.id))

        body = request.form.get("body", "").strip()
        if not body:
            flash("Please type a message.", "danger")
        elif len(body) > MAX_MESSAGE_LENGTH:
            flash(f"A message can be at most {MAX_MESSAGE_LENGTH} characters.", "danger")
        else:
            db.session.add(Message(ride_id=ride.id, sender_id=current_user.id, body=body))
            db.session.commit()
        return redirect(url_for("chat.room", ride_id=ride.id, _anchor="latest"))

    messages = (
        ride.messages.order_by(Message.id.desc())
        .limit(PAGE_SIZE)
        .all()
    )
    messages.reverse()

    return render_template(
        "chat/room.html",
        ride=ride,
        role=role,
        messages=messages,
        members=chat_members(ride),
        chat_open=chat_open,
        can_send=can_send,
        closes_at=closes_at(ride),
        closed_reason=None if chat_open else closed_reason(ride),
        max_length=MAX_MESSAGE_LENGTH,
    )


@chat_bp.route("/ride/<int:ride_id>/messages")
@login_required
def poll(ride_id):
    ride, role = get_chat_or_404(ride_id)
    after = to_int(request.args.get("after")) or 0

    new_messages = (
        ride.messages.filter(Message.id > after)
        .order_by(Message.id.asc())
        .limit(PAGE_SIZE)
        .all()
    )

    return jsonify(
        open=is_open(ride),
        messages=[m.to_dict(current_user.id) for m in new_messages],
    )