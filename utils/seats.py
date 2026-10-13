from sqlalchemy import update

from extensions import db
from models.ride import Ride


def reserve_seats(ride_id, seats):
    result = db.session.execute(
        update(Ride)
        .where(
            Ride.id == ride_id,
            Ride.status == "scheduled",
            Ride.available_seats >= seats,
        )
        .values(available_seats=Ride.available_seats - seats)
    )
    return result.rowcount == 1


def release_seats(ride_id, seats):
    db.session.execute(
        update(Ride)
        .where(
            Ride.id == ride_id,
            Ride.available_seats + seats <= Ride.total_seats,
        )
        .values(available_seats=Ride.available_seats + seats)
    )