from datetime import datetime, timedelta

from extensions import db
from models.ride import Ride

MISSED_AFTER_HOURS = 2
CHECK_EVERY_SECONDS = 60
_last_check = {"at": None}


def expire_missed_rides():
    now = datetime.now()
    last = _last_check["at"]
    if last and (now - last).total_seconds() < CHECK_EVERY_SECONDS:
        return None
    _last_check["at"] = now

    cutoff = now - timedelta(hours=MISSED_AFTER_HOURS)
    try:
        rides = Ride.query.filter(
            Ride.status == "scheduled",
            Ride.ride_date <= cutoff.date(),
        ).all()

        changed = False
        for ride in rides:
            if datetime.combine(ride.ride_date, ride.ride_time) > cutoff:
                continue
            ride.status = "missed"
            for booking in ride.bookings:
                if booking.status in ("pending", "accepted"):
                    booking.status = "missed"
                    booking.trip_pin_hash = None
            changed = True

        if changed:
            db.session.commit()
    except Exception:
        db.session.rollback()
    return None