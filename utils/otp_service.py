from datetime import datetime, timedelta

from extensions import db
from models.otp import OTP, OTP_RESEND_SECONDS, OTP_EXPIRY_MINUTES


def send_sms(phone, message):
    # A real SMS gateway would be called here.
    # For this project the message is printed in the terminal.
    print(f"[SMS to {phone}] {message}", flush=True)


def create_otp(user):
    latest = (
        OTP.query.filter_by(user_id=user.id)
        .order_by(OTP.created_at.desc())
        .first()
    )
    if latest and datetime.utcnow() - latest.created_at < timedelta(seconds=OTP_RESEND_SECONDS):
        return None

    OTP.query.filter_by(user_id=user.id, is_used=False).update({"is_used": True})

    code = OTP.generate_code()
    otp = OTP(user_id=user.id)
    otp.set_code(code)
    db.session.add(otp)
    db.session.commit()

    send_sms(user.phone, f"Your ShareRide code is {code}. It expires in {OTP_EXPIRY_MINUTES} minutes.")
    return code


def verify_otp(user, code):
    otp = (
        OTP.query.filter_by(user_id=user.id, is_used=False)
        .order_by(OTP.created_at.desc())
        .first()
    )
    if otp is None:
        return "missing"
    if otp.is_expired:
        return "expired"
    if otp.is_locked:
        return "locked"

    if not otp.check_code(code):
        otp.attempts += 1
        db.session.commit()
        return "locked" if otp.is_locked else "wrong"

    otp.is_used = True
    user.phone_verified = True
    db.session.commit()
    return "ok"