import sys


def send_sms(phone, message):
    print(f"[SMS to {phone}] {message}", file=sys.stderr, flush=True)
    return True