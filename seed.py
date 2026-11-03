from datetime import datetime, timedelta, time

import click
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash

from extensions import db
from models.user import User
from models.vehicle import Vehicle
from models.ride import Ride
from models.booking import Booking
from models.payment import Payment
from models.rating import Rating
from models.message import Message
from models.sos import SosAlert
from models.complaint import Complaint
from models.audit import AuditLog

DEMO_PASSWORD = "demo1234"
DEMO_EMAIL_DOMAIN = "demo.shareride.app"
SEAT_TAKING_STATUSES = ("accepted", "onboard", "completed")

USERS = [
    ("admin", "Demo Admin", "01700000000", "admin", "verified", "active"),
    ("rahim", "Rahim Uddin", "01700000001", "provider", "verified", "active"),
    ("nusrat", "Nusrat Jahan", "01700000002", "provider", "verified", "active"),
    ("karim", "Karim Mia", "01700000003", "provider", "pending", "active"),
    ("ayesha", "Ayesha Siddiqua", "01700000011", "seeker", "verified", "active"),
    ("tanvir", "Tanvir Ahmed", "01700000012", "seeker", "verified", "active"),
    ("mim", "Mim Akter", "01700000013", "seeker", "verified", "active"),
    ("rafi", "Rafi Islam", "01700000014", "seeker", "pending", "active"),
    ("sabbir", "Sabbir Hossain", "01700000015", "seeker", "verified", "suspended"),
]


def clock(moment):
    return moment.time().replace(second=0, microsecond=0)


def make_users():
    password_hash = generate_password_hash(DEMO_PASSWORD)
    users = {}
    for key, name, phone, role, verification, account in USERS:
        user = User(
            full_name=name,
            phone=phone,
            email=f"{key}@{DEMO_EMAIL_DOMAIN}",
            password_hash=password_hash,
            role=role,
            nid_number=f"DEMO{phone[1:]}",
            phone_verified=True,
            verification_status=verification,
            account_status=account,
            created_at=datetime.utcnow() - timedelta(days=20),
        )
        db.session.add(user)
        users[key] = user
    db.session.flush()
    return users


def make_vehicle(owner, brand, model, color, plate, seats):
    vehicle = Vehicle(
        owner_id=owner.id,
        vehicle_type="car",
        brand=brand,
        model=model,
        color=color,
        plate_number=plate,
        seat_capacity=seats,
        is_approved=True,
    )
    db.session.add(vehicle)
    db.session.flush()
    return vehicle


def make_ride(provider, vehicle, pickup, destination, start, seats, fare, status, notes=None):
    ride = Ride(
        provider_id=provider.id,
        vehicle_id=vehicle.id,
        pickup=pickup,
        destination=destination,
        ride_date=start.date(),
        ride_time=clock(start),
        total_seats=seats,
        available_seats=seats,
        fare_per_seat=fare,
        notes=notes,
        status=status,
    )
    db.session.add(ride)
    db.session.flush()
    return ride


def book(ride, seeker, seats, status):
    booking = Booking(
        ride_id=ride.id,
        seeker_id=seeker.id,
        seats=seats,
        total_fare=seats * ride.fare_per_seat,
        status=status,
        decided_at=None if status == "pending" else datetime.utcnow(),
    )
    if status in SEAT_TAKING_STATUSES:
        ride.available_seats -= seats
    db.session.add(booking)
    db.session.flush()
    return booking


def pay(booking, method, ref, paid_at):
    payment = Payment(
        booking_id=booking.id,
        amount=booking.total_fare,
        method=method,
        status="paid",
        transaction_ref=ref,
        created_at=paid_at,
        paid_at=paid_at,
    )
    db.session.add(payment)
    db.session.flush()
    payment.receipt_number = f"SR-{paid_at:%Y%m%d}-{payment.id:05d}"
    return payment


def rate(booking, rater, ratee, stars, comment, created):
    db.session.add(Rating(
        booking_id=booking.id,
        rater_id=rater.id,
        ratee_id=ratee.id,
        stars=stars,
        comment=comment,
        created_at=created,
    ))


def say(ride, sender, body, created):
    db.session.add(Message(ride_id=ride.id, sender_id=sender.id, body=body, created_at=created))


def audit(admin, action, target_type, target_id, details, created):
    db.session.add(AuditLog(
        admin_id=admin.id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
        ip_address="127.0.0.1",
        created_at=created,
    ))


def refresh_user_stats(users):
    for user in users.values():
        stars = [r.stars for r in Rating.query.filter_by(ratee_id=user.id).all()]
        user.rating = round(sum(stars) / len(stars), 1) if stars else 0.0
        if user.role == "provider":
            user.total_trips = Ride.query.filter_by(provider_id=user.id, status="completed").count()
        elif user.role == "seeker":
            user.total_trips = Booking.query.filter_by(seeker_id=user.id, status="completed").count()


def seed_everything():
    now = datetime.now()
    utc_now = datetime.utcnow()
    u = make_users()
    admin = u["admin"]

    axio = make_vehicle(u["rahim"], "Toyota", "Axio", "White", "DHAKA METRO-GA 11-1001", 4)
    grace = make_vehicle(u["nusrat"], "Honda", "Grace", "Silver", "DHAKA METRO-GA 22-2002", 4)

    old_start = (now - timedelta(days=2)).replace(hour=8, minute=30)
    old_ride = make_ride(u["rahim"], axio, "Farmgate", "Uttara Sector 7", old_start, 3, 150, "completed")
    old_ride.started_at = utc_now - timedelta(days=2, hours=1)
    old_ride.completed_at = utc_now - timedelta(days=2)
    b1 = book(old_ride, u["ayesha"], 1, "completed")
    b2 = book(old_ride, u["tanvir"], 1, "completed")
    pay(b1, "bkash", "BK8F3K2L9Q", utc_now - timedelta(days=2))
    pay(b2, "cash", None, utc_now - timedelta(days=2))
    rate(b1, u["ayesha"], u["rahim"], 5, "Very punctual and drove carefully.", utc_now - timedelta(days=2))
    rate(b1, u["rahim"], u["ayesha"], 5, "Was ready on time. Great passenger.", utc_now - timedelta(days=2))
    rate(b2, u["tanvir"], u["rahim"], 4, "Good ride, a little late at pickup.", utc_now - timedelta(days=2))
    say(old_ride, u["rahim"], "Assalamu alaikum, I will reach Farmgate in 10 minutes.", utc_now - timedelta(days=2, hours=1, minutes=20))
    say(old_ride, u["ayesha"], "Okay, I am waiting near the foot over bridge.", utc_now - timedelta(days=2, hours=1, minutes=18))
    say(old_ride, u["tanvir"], "I am at the bus stand, white shirt.", utc_now - timedelta(days=2, hours=1, minutes=15))

    recent_start = now - timedelta(hours=4)
    recent_ride = make_ride(u["nusrat"], grace, "Mirpur 10", "Motijheel", recent_start, 3, 120, "completed")
    recent_ride.started_at = utc_now - timedelta(hours=4)
    recent_ride.completed_at = utc_now - timedelta(hours=3)
    b3 = book(recent_ride, u["mim"], 1, "completed")
    pay(b3, "nagad", "NG77Q1Z4XT", utc_now - timedelta(hours=3))
    rate(b3, u["mim"], u["nusrat"], 4, "Safe driver, but the AC was off.", utc_now - timedelta(hours=2))
    say(recent_ride, u["nusrat"], "I have reached Mirpur 10 roundabout.", utc_now - timedelta(hours=4, minutes=5))
    say(recent_ride, u["mim"], "Coming in 2 minutes!", utc_now - timedelta(hours=4, minutes=3))
    say(recent_ride, u["mim"], "Thank you, apu. I think I left my umbrella in the back seat.", utc_now - timedelta(hours=2, minutes=40))

    live_start = now - timedelta(minutes=20)
    live_ride = make_ride(u["rahim"], axio, "Dhanmondi 27", "Gulshan 1", live_start, 3, 140, "started")
    live_ride.started_at = utc_now - timedelta(minutes=20)
    b4 = book(live_ride, u["ayesha"], 1, "onboard")
    book(live_ride, u["mim"], 1, "accepted")
    say(live_ride, u["rahim"], "We are leaving Dhanmondi now.", utc_now - timedelta(minutes=19))
    say(live_ride, u["mim"], "Bhaiya, I am a bit late, please wait 5 minutes at Kakoli.", utc_now - timedelta(minutes=12))
    db.session.add(SosAlert(
        ride_id=live_ride.id,
        user_id=u["ayesha"].id,
        latitude=23.7806,
        longitude=90.4074,
        message="Driver took an unknown road, please check.",
        status="open",
        created_at=utc_now - timedelta(minutes=5),
    ))

    tomorrow = (now + timedelta(days=1)).replace(hour=9, minute=0)
    next_ride = make_ride(u["nusrat"], grace, "Banani", "Bashundhara R/A", tomorrow, 3, 100, "scheduled", "AC car. Please be on time.")
    book(next_ride, u["ayesha"], 1, "accepted")
    book(next_ride, u["tanvir"], 1, "pending")

    later = (now + timedelta(days=2)).replace(hour=7, minute=30)
    make_ride(u["rahim"], axio, "Mohakhali", "Savar", later, 4, 180, "scheduled", "Highway trip, one stop at Gabtoli.")

    weekend = (now + timedelta(days=3)).replace(hour=17, minute=0)
    make_ride(u["nusrat"], grace, "Uttara Sector 10", "Shahbag", weekend, 2, 130, "scheduled")

    cancelled_start = (now - timedelta(days=1)).replace(hour=18, minute=0)
    make_ride(u["rahim"], axio, "Mohammadpur", "Badda", cancelled_start, 3, 110, "cancelled")

    open_complaint = Complaint(
        complainant_id=u["mim"].id,
        against_id=u["nusrat"].id,
        ride_id=recent_ride.id,
        category="vehicle",
        subject="AC was not working",
        description="The ride was listed as an AC car but the AC was off for the whole trip and it was very hot.",
        status="open",
        created_at=utc_now - timedelta(hours=2),
    )

    resolved_complaint = Complaint(
        complainant_id=u["tanvir"].id,
        against_id=u["sabbir"].id,
        category="behaviour",
        subject="Abusive messages after a booking",
        description="This user sent me rude and threatening messages after I could not share a ride with him.",
        status="resolved",
        admin_note="We checked the messages and suspended this account. Thank you for reporting.",
        action_taken="suspended",
        handled_by=admin.id,
        created_at=utc_now - timedelta(days=5),
        resolved_at=utc_now - timedelta(days=4),
    )

    dismissed_complaint = Complaint(
        complainant_id=u["ayesha"].id,
        category="payment",
        subject="Charged twice on bKash",
        description="I think my bKash account was charged two times for the Farmgate to Uttara trip.",
        status="dismissed",
        admin_note="We checked the transaction ID and only one payment was made. Please check your bKash statement again.",
        action_taken="none",
        handled_by=admin.id,
        created_at=utc_now - timedelta(days=1, hours=6),
        resolved_at=utc_now - timedelta(days=1),
    )

    db.session.add_all([open_complaint, resolved_complaint, dismissed_complaint])
    db.session.flush()

    for key in ("rahim", "nusrat", "ayesha", "tanvir", "mim", "sabbir"):
        audit(admin, "nid_verified", "user", u[key].id, None, utc_now - timedelta(days=15))
    audit(admin, "account_suspend", "user", u["sabbir"].id,
          f"active -> suspended: complaint #{resolved_complaint.id}", utc_now - timedelta(days=4))
    audit(admin, "complaint_resolved", "complaint", resolved_complaint.id,
          "action: suspended | We checked the messages and suspended this account.", utc_now - timedelta(days=4))
    audit(admin, "complaint_dismissed", "complaint", dismissed_complaint.id,
          "action: none | Only one payment was made.", utc_now - timedelta(days=1))

    db.session.flush()
    refresh_user_stats(u)
    db.session.commit()
    return u


@click.command("seed-demo")
@click.option("--fresh", is_flag=True, help="Delete ALL data first, then add the demo data.")
@with_appcontext
def seed_demo(fresh):
    if fresh:
        click.confirm("This deletes ALL data in the database. Continue?", abort=True)
        db.drop_all()
        db.create_all()
    else:
        demo_phones = [row[2] for row in USERS]
        if User.query.filter(User.phone.in_(demo_phones)).first():
            click.echo("Demo data already exists. Run with --fresh to start over.")
            return

    users = seed_everything()

    click.echo("")
    click.echo("Demo data added. Every demo account uses the password: " + DEMO_PASSWORD)
    click.echo("")
    for key, name, phone, role, verification, account in USERS:
        click.echo(f"  {phone}  {role:<9} {name:<17} NID {verification:<9} account {account}")
    click.echo("")
    click.echo(f"  Rides: {Ride.query.count()}  Bookings: {Booking.query.count()}  Complaints: {Complaint.query.count()}")