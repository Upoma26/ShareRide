import secrets
from datetime import datetime

from werkzeug.security import generate_password_hash, check_password_hash

MAX_PIN_ATTEMPTS = 5


def issue_pin(booking):
    pin = f"{secrets.randbelow(10000):04d}"
    booking.trip_pin_hash = generate_password_hash(pin)
    booking.pin_generated_at = datetime.utcnow()
    booking.pin_attempts = 0
    return pin


def check_pin(booking, pin):
    if not booking.trip_pin_hash:
        return "missing"
    if (booking.pin_attempts or 0) >= MAX_PIN_ATTEMPTS:
        return "locked"
    if check_password_hash(booking.trip_pin_hash, pin):
        return "ok"
    booking.pin_attempts = (booking.pin_attempts or 0) + 1
    return "locked" if booking.pin_attempts >= MAX_PIN_ATTEMPTS else "wrong"


def clear_pin(booking):
    booking.trip_pin_hash = None
    