import os
import unittest
from datetime import datetime, timedelta

TEST_DB_PATH = os.path.abspath("test_shareride.sqlite3")

from app import create_app
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
from models.otp import OTP
from utils.trip_pin import issue_pin, check_pin, clear_pin
from utils.otp_service import verify_otp
from werkzeug.security import generate_password_hash


class ShareRideComprehensiveTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.path.exists(TEST_DB_PATH):
            try:
                os.remove(TEST_DB_PATH)
            except Exception:
                pass

        test_config = {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{TEST_DB_PATH}",
            "WTF_CSRF_ENABLED": False,
            "SERVER_NAME": "localhost",
            "DEMO_MODE": True,
            "SECRET_KEY": "test-secret-key-12345",
        }
        cls.app = create_app(test_config=test_config)
        cls.client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(TEST_DB_PATH):
            try:
                os.remove(TEST_DB_PATH)
            except Exception:
                pass

    def setUp(self):
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.drop_all()
        db.create_all()
        self.seed_test_data()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def seed_test_data(self):
        pw_hash = generate_password_hash("demo1234")
        
        # Admin
        self.admin = User(
            full_name="Demo Admin",
            phone="01700000000",
            email="admin@test.app",
            password_hash=pw_hash,
            role="admin",
            nid_number="DEMO1700000000",
            phone_verified=True,
            verification_status="verified",
            account_status="active",
        )
        # Driver 1: Verified
        self.driver_rahim = User(
            full_name="Rahim Uddin",
            phone="01700000001",
            email="rahim@test.app",
            password_hash=pw_hash,
            role="provider",
            nid_number="DEMO1700000001",
            phone_verified=True,
            verification_status="verified",
            account_status="active",
        )
        # Driver 2: Pending NID
        self.driver_karim = User(
            full_name="Karim Mia",
            phone="01700000003",
            email="karim@test.app",
            password_hash=pw_hash,
            role="provider",
            nid_number="DEMO1700000003",
            phone_verified=True,
            verification_status="pending",
            account_status="active",
        )
        # Passenger 1: Verified
        self.passenger_ayesha = User(
            full_name="Ayesha Siddiqua",
            phone="01700000011",
            email="ayesha@test.app",
            password_hash=pw_hash,
            role="seeker",
            nid_number="DEMO1700000011",
            phone_verified=True,
            verification_status="verified",
            account_status="active",
        )
        # Passenger 2: Verified
        self.passenger_tanvir = User(
            full_name="Tanvir Ahmed",
            phone="01700000012",
            email="tanvir@test.app",
            password_hash=pw_hash,
            role="seeker",
            nid_number="DEMO1700000012",
            phone_verified=True,
            verification_status="verified",
            account_status="active",
        )
        # Passenger 3: Suspended
        self.passenger_sabbir = User(
            full_name="Sabbir Hossain",
            phone="01700000015",
            email="sabbir@test.app",
            password_hash=pw_hash,
            role="seeker",
            nid_number="DEMO1700000015",
            phone_verified=True,
            verification_status="verified",
            account_status="suspended",
        )
        db.session.add_all([
            self.admin, self.driver_rahim, self.driver_karim,
            self.passenger_ayesha, self.passenger_tanvir, self.passenger_sabbir
        ])
        db.session.commit()

        # Vehicle for Rahim
        self.vehicle_rahim = Vehicle(
            owner_id=self.driver_rahim.id,
            vehicle_type="car",
            brand="Toyota",
            model="Corolla",
            color="Silver",
            plate_number="DHK-MET-GA-112233",
            seat_capacity=4,
            is_approved=True,
        )
        db.session.add(self.vehicle_rahim)
        db.session.commit()

        # Active ride (scheduled)
        tomorrow = datetime.now() + timedelta(days=1)
        self.ride_scheduled = Ride(
            provider_id=self.driver_rahim.id,
            vehicle_id=self.vehicle_rahim.id,
            pickup="Mohakhali",
            destination="Savar",
            ride_date=tomorrow.date(),
            ride_time=tomorrow.time().replace(second=0, microsecond=0),
            total_seats=3,
            available_seats=3,
            fare_per_seat=120,
            status="scheduled",
        )
        # Completed ride
        yesterday = datetime.now() - timedelta(days=1)
        self.ride_completed = Ride(
            provider_id=self.driver_rahim.id,
            vehicle_id=self.vehicle_rahim.id,
            pickup="Farmgate",
            destination="Uttara",
            ride_date=yesterday.date(),
            ride_time=yesterday.time().replace(second=0, microsecond=0),
            total_seats=3,
            available_seats=1,
            fare_per_seat=150,
            status="completed",
            completed_at=yesterday,
        )
        # In-progress ride (started)
        self.ride_started = Ride(
            provider_id=self.driver_rahim.id,
            vehicle_id=self.vehicle_rahim.id,
            pickup="Banani",
            destination="Bashundhara",
            ride_date=datetime.now().date(),
            ride_time=datetime.now().time().replace(second=0, microsecond=0),
            total_seats=3,
            available_seats=2,
            fare_per_seat=130,
            status="started",
            started_at=datetime.now(),
        )
        db.session.add_all([self.ride_scheduled, self.ride_completed, self.ride_started])
        db.session.commit()

        # Completed booking for Ayesha on completed ride
        self.booking_completed = Booking(
            ride_id=self.ride_completed.id,
            seeker_id=self.passenger_ayesha.id,
            seats=1,
            total_fare=150,
            status="completed",
        )
        # Onboard booking for Ayesha on started ride (for SOS)
        self.booking_onboard = Booking(
            ride_id=self.ride_started.id,
            seeker_id=self.passenger_ayesha.id,
            seats=1,
            total_fare=130,
            status="onboard",
        )
        db.session.add_all([self.booking_completed, self.booking_onboard])
        db.session.commit()

    def login_user(self, phone, password="demo1234"):
        return self.client.post("/auth/login", data={"phone": phone, "password": password}, follow_redirects=True)

    def logout_user(self):
        return self.client.get("/auth/logout", follow_redirects=True)

    # ==========================================
    # SECTION 1: PUBLIC & GENERAL ROUTE TESTS
    # ==========================================
    def test_tc01_home_page_loads_success(self):
        """TC-01: Verify home page loads with 200 OK and expected branding."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"ShareRide", res.data)

    def test_tc02_about_page_loads_success(self):
        """TC-02: Verify about page loads with 200 OK and feature info."""
        res = self.client.get("/about")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"About ShareRide", res.data)

    def test_tc03_find_rides_page_loads_success(self):
        """TC-03: Verify ride search / listing page loads successfully."""
        res = self.client.get("/rides")
        self.assertEqual(res.status_code, 200)

    # ==========================================
    # SECTION 2: AUTHENTICATION & SECURITY (SUCCESS)
    # ==========================================
    def test_tc04_login_driver_success(self):
        """TC-04: Successful driver login with valid credentials."""
        res = self.login_user(phone="01700000001", password="demo1234")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Rahim Uddin", res.data)

    def test_tc05_login_passenger_success(self):
        """TC-05: Successful passenger login with valid credentials."""
        res = self.login_user(phone="01700000011", password="demo1234")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Ayesha", res.data)

    def test_tc06_login_admin_success(self):
        """TC-06: Successful admin login with valid credentials."""
        res = self.login_user(phone="01700000000", password="demo1234")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Admin", res.data)

    def test_tc07_logout_success(self):
        """TC-07: Successful logout terminates authenticated session."""
        self.login_user(phone="01700000011")
        res = self.logout_user()
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Sign in", res.data)

    # ==========================================
    # SECTION 3: AUTHENTICATION & ACCESS (FAILURES / NEGATIVE TESTS)
    # ==========================================
    def test_tc08_login_wrong_password_failure(self):
        """TC-08 [FAILURE TEST]: Login rejection when submitting incorrect password."""
        res = self.login_user(phone="01700000011", password="WrongPassword999!")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Phone or password is incorrect", res.data)

    def test_tc09_login_nonexistent_user_failure(self):
        """TC-09 [FAILURE TEST]: Login rejection when phone is not in database."""
        res = self.login_user(phone="01999999999", password="demo1234")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Phone or password is incorrect", res.data)

    def test_tc10_login_suspended_account_failure(self):
        """TC-10 [FAILURE TEST]: Block login when user account status is suspended."""
        res = self.login_user(phone="01700000015", password="demo1234")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"suspended", res.data.lower())

    def test_tc11_register_invalid_phone_format_failure(self):
        """TC-11 [FAILURE TEST]: Reject registration with invalid Bangladeshi phone format."""
        data = {
            "full_name": "Test User",
            "phone": "012345",  # Invalid format
            "email": "test@example.com",
            "nid_number": "1234567890",
            "role": "seeker",
            "password": "Password123!",
            "confirm_password": "Password123!",
        }
        res = self.client.post("/auth/register", data=data, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Enter a valid 11-digit Bangladeshi phone number", res.data)

    def test_tc12_register_password_mismatch_failure(self):
        """TC-12 [FAILURE TEST]: Reject registration when passwords do not match."""
        data = {
            "full_name": "Test User",
            "phone": "01711223344",
            "email": "mismatch@example.com",
            "nid_number": "1234567890",
            "role": "seeker",
            "password": "Password123!",
            "confirm_password": "DifferentPassword123!",
        }
        res = self.client.post("/auth/register", data=data, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Passwords do not match", res.data)

    def test_tc13_register_duplicate_phone_failure(self):
        """TC-13 [FAILURE TEST]: Reject registration with already registered phone."""
        data = {
            "full_name": "Duplicate Phone User",
            "phone": "01700000001",  # Existing phone of Rahim
            "email": "newunique@example.com",
            "nid_number": "9876543210",
            "role": "seeker",
            "password": "Password123!",
            "confirm_password": "Password123!",
        }
        res = self.client.post("/auth/register", data=data, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"An account with this phone number already exists", res.data)

    def test_tc14_register_short_password_failure(self):
        """TC-14 [FAILURE TEST]: Reject registration with password shorter than 8 chars."""
        data = {
            "full_name": "Short Password User",
            "phone": "01799887766",
            "email": "short@example.com",
            "nid_number": "9876543210",
            "role": "seeker",
            "password": "short",
            "confirm_password": "short",
        }
        res = self.client.post("/auth/register", data=data, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Password must be at least 8 characters", res.data)

    def test_tc15_rbac_unauthenticated_admin_access_failure(self):
        """TC-15 [SECURITY FAILURE TEST]: Anonymous user blocked from accessing /admin/."""
        res = self.client.get("/admin/", follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Please sign in first", res.data)

    def test_tc16_rbac_passenger_admin_access_failure(self):
        """TC-16 [SECURITY FAILURE TEST]: Passenger role blocked from accessing /admin/."""
        self.login_user(phone="01700000011")  # Ayesha (seeker)
        res = self.client.get("/admin/", follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"You do not have permission to open that page", res.data)

    def test_tc17_rbac_passenger_provider_dashboard_failure(self):
        """TC-17 [SECURITY FAILURE TEST]: Passenger blocked from accessing driver dashboard."""
        self.login_user(phone="01700000011")  # Ayesha (seeker)
        res = self.client.get("/provider/dashboard", follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"You do not have permission to open that page", res.data)

    # ==========================================
    # SECTION 4: DRIVER RIDE CREATION & VALIDATION
    # ==========================================
    def test_tc18_driver_post_ride_success(self):
        """TC-18: Verified driver successfully posts a new scheduled ride."""
        self.login_user(phone="01700000001")  # Rahim
        ride_data = {
            "vehicle_id": self.vehicle_rahim.id,
            "pickup": "Dhanmondi 27",
            "destination": "Gulshan 1",
            "ride_date": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
            "ride_time": "10:30",
            "total_seats": 3,
            "fare_per_seat": 140,
            "notes": "AC car, luggage space available",
        }
        res = self.client.post("/provider/rides/new", data=ride_data, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        ride = Ride.query.filter_by(pickup="Dhanmondi 27", destination="Gulshan 1").first()
        self.assertIsNotNone(ride)
        self.assertEqual(ride.total_seats, 3)

    def test_tc19_unverified_driver_post_ride_failure(self):
        """TC-19 [FAILURE TEST]: Unverified driver blocked from posting rides."""
        self.login_user(phone="01700000003")  # Karim (pending NID)
        ride_data = {
            "vehicle_type": "car",
            "plate_number": "DHK-MET-HA-9988",
            "brand": "Toyota",
            "model": "Allion",
            "seat_capacity": 4,
            "pickup": "Mirpur 10",
            "destination": "Motijheel",
            "ride_date": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
            "ride_time": "08:00",
            "total_seats": 2,
            "fare_per_seat": 100,
        }
        res = self.client.post("/provider/rides/new", data=ride_data, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"verifies your NID", res.data)

    def test_tc20_driver_post_ride_exceeding_seats_failure(self):
        """TC-20 [FAILURE TEST]: Reject ride when seats exceed vehicle capacity."""
        self.login_user(phone="01700000001")  # Rahim (vehicle seat capacity is 4)
        ride_data = {
            "vehicle_id": self.vehicle_rahim.id,
            "pickup": "Uttara",
            "destination": "Motijheel",
            "ride_date": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
            "ride_time": "09:00",
            "total_seats": 10,  # Exceeds capacity of 4
            "fare_per_seat": 150,
        }
        res = self.client.post("/provider/rides/new", data=ride_data, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"seats", res.data.lower())

    def test_tc21_driver_post_ride_past_date_failure(self):
        """TC-21 [FAILURE TEST]: Reject ride creation with past date."""
        self.login_user(phone="01700000001")
        ride_data = {
            "vehicle_id": self.vehicle_rahim.id,
            "pickup": "Uttara",
            "destination": "Motijheel",
            "ride_date": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
            "ride_time": "09:00",
            "total_seats": 2,
            "fare_per_seat": 150,
        }
        res = self.client.post("/provider/rides/new", data=ride_data, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"future", res.data.lower())

    # ==========================================
    # SECTION 5: PASSENGER BOOKING & WORKFLOW
    # ==========================================
    def test_tc22_passenger_book_ride_success(self):
        """TC-22: Passenger successfully requests a seat on a scheduled ride."""
        self.login_user(phone="01700000012")  # Tanvir
        res = self.client.post(
            f"/bookings/ride/{self.ride_scheduled.id}",
            data={"seats": 1},
            follow_redirects=True,
        )
        self.assertEqual(res.status_code, 200)
        booking = Booking.query.filter_by(ride_id=self.ride_scheduled.id, seeker_id=self.passenger_tanvir.id).first()
        self.assertIsNotNone(booking)
        self.assertEqual(booking.status, "pending")
        self.assertEqual(booking.seats, 1)

    def test_tc23_passenger_book_exceeding_seats_failure(self):
        """TC-23 [FAILURE TEST]: Reject booking when requested seats exceed available seats."""
        self.login_user(phone="01700000012")  # Tanvir
        res = self.client.post(
            f"/bookings/ride/{self.ride_scheduled.id}",
            data={"seats": 99},  # Only 3 seats available
            follow_redirects=True,
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"not enough seats", res.data.lower())

    def test_tc24_passenger_cancel_pending_booking_success(self):
        """TC-24: Passenger cancels pending booking successfully."""
        # Create pending booking
        booking = Booking(
            ride_id=self.ride_scheduled.id,
            seeker_id=self.passenger_tanvir.id,
            seats=1,
            total_fare=120,
            status="pending",
        )
        db.session.add(booking)
        db.session.commit()

        self.login_user(phone="01700000012")  # Tanvir
        res = self.client.post(f"/bookings/{booking.id}/cancel", follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        b = db.session.get(Booking, booking.id)
        self.assertEqual(b.status, "cancelled")

    # ==========================================
    # SECTION 6: TRIP PIN VERIFICATION & CHECK-IN
    # ==========================================
    def test_tc25_trip_pin_verification_success(self):
        """TC-25: Valid Trip PIN check-in succeeds."""
        booking = Booking(
            ride_id=self.ride_scheduled.id,
            seeker_id=self.passenger_ayesha.id,
            seats=1,
            total_fare=120,
            status="accepted",
        )
        db.session.add(booking)
        db.session.commit()
        pin = issue_pin(booking)
        db.session.commit()

        result = check_pin(booking, pin)
        self.assertEqual(result, "ok")

    def test_tc26_trip_pin_wrong_code_failure(self):
        """TC-26 [FAILURE TEST]: Incorrect Trip PIN check-in is rejected."""
        booking = Booking(
            ride_id=self.ride_scheduled.id,
            seeker_id=self.passenger_ayesha.id,
            seats=1,
            total_fare=120,
            status="accepted",
        )
        db.session.add(booking)
        db.session.commit()
        issue_pin(booking)
        db.session.commit()

        result = check_pin(booking, "0000")  # Wrong PIN
        self.assertIn(result, ["wrong", "locked"])
        self.assertEqual(booking.pin_attempts, 1)

    def test_tc27_trip_pin_lockout_after_max_attempts_failure(self):
        """TC-27 [FAILURE TEST]: Trip PIN locked after 5 consecutive failed attempts."""
        booking = Booking(
            ride_id=self.ride_scheduled.id,
            seeker_id=self.passenger_ayesha.id,
            seats=1,
            total_fare=120,
            status="accepted",
        )
        db.session.add(booking)
        db.session.commit()
        issue_pin(booking)
        db.session.commit()

        # Try 5 wrong pins
        for i in range(5):
            res = check_pin(booking, f"999{i}")
        self.assertEqual(res, "locked")
        self.assertEqual(booking.pin_attempts, 5)

    # ==========================================
    # SECTION 7: PAYMENTS & RATINGS
    # ==========================================
    def test_tc28_payment_submission_success(self):
        """TC-28: Passenger submits valid payment for completed trip."""
        self.login_user(phone="01700000011")  # Ayesha
        pay_data = {
            "method": "bkash",
            "transaction_ref": "TXN987654321",
        }
        res = self.client.post(f"/payments/booking/{self.booking_completed.id}", data=pay_data, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        payment = Payment.query.filter_by(booking_id=self.booking_completed.id).first()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.method, "bkash")
        self.assertEqual(payment.transaction_ref, "TXN987654321")

    def test_tc29_payment_duplicate_transaction_id_failure(self):
        """TC-29 [FAILURE TEST]: Reject duplicate transaction ID for digital payment."""
        # First payment
        payment1 = Payment(
            booking_id=self.booking_completed.id,
            amount=150,
            method="bkash",
            transaction_ref="DUPLICATETXN123",
            status="paid",
        )
        db.session.add(payment1)
        db.session.commit()

        # Create another completed booking for Tanvir
        booking2 = Booking(
            ride_id=self.ride_completed.id,
            seeker_id=self.passenger_tanvir.id,
            seats=1,
            total_fare=150,
            status="completed",
        )
        db.session.add(booking2)
        db.session.commit()

        self.login_user(phone="01700000012")  # Tanvir
        pay_data = {
            "method": "bkash",
            "transaction_ref": "DUPLICATETXN123",  # Duplicate
        }
        res = self.client.post(f"/payments/booking/{booking2.id}", data=pay_data, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"already been used", res.data)

    def test_tc30_rating_submission_success(self):
        """TC-30: Passenger submits valid rating (5 stars) for completed trip."""
        self.login_user(phone="01700000011")  # Ayesha
        rating_data = {
            "stars": 5,
            "comment": "Smooth driving and polite behavior!",
        }
        res = self.client.post(f"/ratings/booking/{self.booking_completed.id}", data=rating_data, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        rating = Rating.query.filter_by(booking_id=self.booking_completed.id, rater_id=self.passenger_ayesha.id).first()
        self.assertIsNotNone(rating)
        self.assertEqual(rating.stars, 5)

    def test_tc31_rating_out_of_range_failure(self):
        """TC-31 [FAILURE TEST]: Reject rating score above maximum allowed (e.g. 7 stars)."""
        self.login_user(phone="01700000011")
        rating_data = {
            "stars": 7,  # Invalid rating score
            "comment": "Impossible score",
        }
        res = self.client.post(f"/ratings/booking/{self.booking_completed.id}", data=rating_data, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"1 to 5 stars", res.data)

    # ==========================================
    # SECTION 8: CHAT & SOS EMERGENCY ALERTS
    # ==========================================
    def test_tc32_chat_send_message_success(self):
        """TC-32: Ride participant successfully sends a message in ride group chat."""
        # Booking Ayesha on scheduled ride
        b = Booking(
            ride_id=self.ride_scheduled.id,
            seeker_id=self.passenger_ayesha.id,
            seats=1,
            total_fare=120,
            status="accepted",
        )
        db.session.add(b)
        db.session.commit()

        self.login_user(phone="01700000011")
        msg_data = {"body": "Hello driver, I am on my way."}
        res = self.client.post(f"/chat/ride/{self.ride_scheduled.id}", data=msg_data, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        msg = Message.query.filter_by(ride_id=self.ride_scheduled.id, sender_id=self.passenger_ayesha.id).first()
        self.assertIsNotNone(msg)
        self.assertEqual(msg.body, "Hello driver, I am on my way.")

    def test_tc33_chat_unauthorized_user_access_failure(self):
        """TC-33 [SECURITY FAILURE TEST]: User not on ride cannot view or post to ride chat."""
        # Tanvir is NOT booked on scheduled ride
        self.login_user(phone="01700000012")  # Tanvir
        res = self.client.get(f"/chat/ride/{self.ride_scheduled.id}")
        self.assertEqual(res.status_code, 404)

    def test_tc34_sos_creation_success(self):
        """TC-34: Passenger triggers emergency SOS alert on active ride."""
        self.login_user(phone="01700000011")
        sos_data = {
            "latitude": 23.777176,
            "longitude": 90.399452,
            "accuracy": 12.5,
        }
        res = self.client.post(f"/rides/{self.ride_started.id}/sos", data=sos_data, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        sos = SosAlert.query.filter_by(ride_id=self.ride_started.id, user_id=self.passenger_ayesha.id).first()
        self.assertIsNotNone(sos)
        self.assertEqual(sos.status, "open")

    # ==========================================
    # SECTION 9: ADMIN ACTIONS & AUDIT TRAIL
    # ==========================================
    def test_tc35_admin_approve_nid_success(self):
        """TC-35: Admin approves pending NID verification for driver."""
        self.login_user(phone="01700000000")  # Admin
        res = self.client.post(f"/admin/nid/{self.driver_karim.id}/approve", follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        user = db.session.get(User, self.driver_karim.id)
        self.assertEqual(user.verification_status, "verified")

        # Verify audit log recorded
        log = AuditLog.query.filter_by(target_user_id=self.driver_karim.id, action_type="nid_approved").first()
        self.assertIsNotNone(log)

    def test_tc36_admin_reject_nid_without_reason_failure(self):
        """TC-36 [FAILURE TEST]: Admin cannot reject NID without providing a reason."""
        self.login_user(phone="01700000000")  # Admin
        res = self.client.post(f"/admin/nid/{self.driver_karim.id}/reject", data={"reason": ""}, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Please provide a reason", res.data)
        user = db.session.get(User, self.driver_karim.id)
        self.assertEqual(user.verification_status, "pending")

    def test_tc37_admin_suspend_and_reinstate_user_success(self):
        """TC-37: Admin suspends an active user and subsequently reinstates them."""
        self.login_user(phone="01700000000")  # Admin
        # Suspend
        res_suspend = self.client.post(
            f"/admin/users/{self.passenger_tanvir.id}/status",
            data={"action": "suspend", "reason": "Violated community policy"},
            follow_redirects=True,
        )
        self.assertEqual(res_suspend.status_code, 200)
        tanvir = db.session.get(User, self.passenger_tanvir.id)
        self.assertEqual(tanvir.account_status, "suspended")

        # Reinstate
        res_reinstate = self.client.post(
            f"/admin/users/{self.passenger_tanvir.id}/status",
            data={"action": "reinstate", "reason": "Issue resolved"},
            follow_redirects=True,
        )
        self.assertEqual(res_reinstate.status_code, 200)
        tanvir = db.session.get(User, self.passenger_tanvir.id)
        self.assertEqual(tanvir.account_status, "active")

    def test_tc38_admin_export_audit_csv_success(self):
        """TC-38: Admin successfully exports audit logs in CSV format."""
        self.login_user(phone="01700000000")  # Admin
        res = self.client.get("/admin/audit/export")
        self.assertEqual(res.status_code, 200)
        self.assertIn("text/csv", res.headers.get("Content-Type", ""))
        self.assertIn(b"Timestamp,Admin,Action,Target User,Details", res.data)

    # ==========================================
    # SECTION 10: AUTOMATIC EXPIRATION & SYSTEM LOGIC
    # ==========================================
    def test_tc39_missed_ride_auto_expiration_success(self):
        """TC-39: Rides older than 2 hours without starting are marked 'missed'."""
        three_hours_ago = datetime.now() - timedelta(hours=3)
        stale_ride = Ride(
            provider_id=self.driver_rahim.id,
            vehicle_id=self.vehicle_rahim.id,
            pickup="Shahbagh",
            destination="Mirpur",
            ride_date=three_hours_ago.date(),
            ride_time=three_hours_ago.time().replace(second=0, microsecond=0),
            total_seats=3,
            available_seats=3,
            fare_per_seat=100,
            status="scheduled",
        )
        db.session.add(stale_ride)
        db.session.commit()

        # Making any request triggers the before_request hook expire_missed_rides
        self.client.get("/")
        updated = db.session.get(Ride, stale_ride.id)
        self.assertEqual(updated.status, "missed")

    def test_tc40_otp_verification_failure_on_wrong_code(self):
        """TC-40 [FAILURE TEST]: OTP verification rejects incorrect code."""
        otp = OTP(user_id=self.passenger_ayesha.id)
        otp.set_code("123456")
        db.session.add(otp)
        db.session.commit()

        result = verify_otp(self.passenger_ayesha, "654321")
        self.assertEqual(result, "wrong")


if __name__ == "__main__":
    unittest.main()
