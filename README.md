# ShareRide

A community ride-sharing web app for Dhaka. Drivers fill their empty seats, passengers travel for less, and every member is NID verified.

**Live demo:** https://upoma.pythonanywhere.com

Built for **CSE 314 Software Engineering Lab** (Section C1), University of Asia Pacific, under **Md Ashraful Alam**.

## Team

| Member | ID | GitHub | Role |
|---|---|---|---|
| Jannatul Ferdaus Khusbu Upoma | 23201125 | [Upoma26](https://github.com/Upoma26) | Team Leader |
| Md. Mehedi Hassan | 23201114 | [23201114-dot](https://github.com/23201114-dot) | Project Manager |
| Fariya Rahman | 23201136 | [23201136-fariyarahman](https://github.com/23201136-fariyarahman) | Reporting Lead |

## Features

**Passengers**
- Register with phone OTP and NID upload, then wait for admin verification
- Search rides by route, date, time and seats, right from the dashboard
- Request seats, track the booking on a timeline, cancel while pending
- Trip PIN check-in, so the right passenger gets into the right car
- Pay by cash, bKash, Nagad or card, with a printable receipt
- Rate the driver, see trip history and total spent
- Filter bookings by status (including Missed) and date

**Drivers**
- Add vehicles, post, edit and cancel rides
- Accept or reject seat requests, check passengers in with their Trip PIN
- Start and complete trips, rate passengers
- Dashboard with earnings, status and date filters, and mobile ride cards
- Ride history page with passengers, payments, chat history and reviews

**Safety and communication**
- Group chat for each ride, closes 24 hours after the trip
- One-tap SOS with GPS location and live location updates every 30 seconds
- Complaints with categories, admin replies and outcomes

**Admins**
- NID review with access logging, account suspend, block and reinstate
- User search, ride monitoring with status tabs, complaint handling
- SOS detail page with live map, quick call actions and resolve notes
- Audit log of every admin action with filters and CSV export

**General**
- Light and dark mode, responsive layout for phones
- Bangladesh time (Asia/Dhaka) across the app
- Rides not started within 2 hours of their time are marked Missed automatically
- Demo mode that shows the OTP on screen for presentations

## Tech stack

| Layer | Technology |
|---|---|
| Language | Python 3.12+ |
| Web framework | Flask (Blueprints) |
| Templates | Jinja2, HTML, CSS, JavaScript |
| Database | SQLite with Flask-SQLAlchemy |
| Authentication | Flask-Login, Werkzeug password hashing (PBKDF2) |
| Configuration | python-dotenv |
| Hosting | PythonAnywhere |
| Project management | Jira (one task = one branch = one pull request) |

## Run it locally (Windows)

```
git clone https://github.com/Upoma26/ShareRide.git
cd ShareRide
py -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
flask --app app init-db
flask --app app seed-demo
flask --app app run --debug
```

Open http://127.0.0.1:5000

On macOS or Linux use `python3 -m venv venv`, `source venv/bin/activate` and `cp .env.example .env`.

## Configuration (`.env`)

| Variable | Purpose | Local | Live |
|---|---|---|---|
| `SECRET_KEY` | Signs session cookies | any long string | long random string |
| `DATABASE_URL` | Database location (optional) | default SQLite file | default SQLite file |
| `SESSION_COOKIE_SECURE` | Send cookies only over HTTPS | `0` | `1` |
| `DEMO_MODE` | Show the OTP on screen | `1` | `1` for demos, `0` with real SMS |

`.env` is ignored by Git. Never commit real keys.

## Command line

| Command | What it does |
|---|---|
| `flask --app app init-db` | Creates all database tables (safe to run again) |
| `flask --app app create-admin` | Creates an admin account interactively |
| `flask --app app seed-demo` | Adds demo users, rides, payments, chat, complaints and SOS |
| `flask --app app seed-demo --fresh` | Deletes all data, then adds the demo data |

## Demo accounts

Password for every demo account: `demo1234`

| Role | Name | Phone |
|---|---|---|
| Admin | Demo Admin | 01700000000 |
| Driver | Rahim Uddin | 01700000001 |
| Driver | Nusrat Jahan | 01700000002 |
| Driver (NID pending) | Karim Mia | 01700000003 |
| Passenger | Ayesha Siddiqua | 01700000011 |
| Passenger | Tanvir Ahmed | 01700000012 |
| Passenger | Mim Akter | 01700000013 |
| Passenger (NID pending) | Rafi Islam | 01700000014 |
| Passenger (suspended) | Sabbir Hossain | 01700000015 |

## Project structure

```
ShareRide/
├── app.py              App factory, blueprints, CLI commands, request hooks
├── config.py           Settings and Asia/Dhaka time zone
├── extensions.py       Database and login manager
├── seed.py             Demo data command
├── wsgi.py             Entry point for PythonAnywhere
├── models/             Database tables (user, ride, booking, payment, rating,
│                       message, sos, complaint, audit, nid, otp, vehicle)
├── routes/             Pages and actions (auth, main, rides, bookings, provider,
│                       payments, ratings, chat, complaints, admin)
├── utils/              Helpers (decorators, OTP, Trip PIN, seats, uploads,
│                       audit logging, missed rides)
├── templates/          Jinja2 pages
├── static/css/         Stylesheet
├── docs/               Manual test cases and user guide
└── uploads/nid/        NID images (ignored by Git, not public)
```

## Deployment (PythonAnywhere)

1. Bash console: `git clone`, create `venv`, `pip install -r requirements.txt`
2. Create `.env` with `SECRET_KEY`, `SESSION_COOKIE_SECURE=1`, `DEMO_MODE=1`
3. `mkdir -p uploads/nid`, then `flask --app app init-db` and `flask --app app seed-demo`
4. Web tab: manual configuration, Python 3.13, source `/home/<user>/ShareRide`, virtualenv `/home/<user>/ShareRide/venv`
5. WSGI file: add the project folder to `sys.path` and `from wsgi import application`
6. Static files: `/static/` → `/home/<user>/ShareRide/static`, Force HTTPS on, Reload

To update: `cd ~/ShareRide && git pull`, run `flask --app app init-db` if a new table was added, then Reload.

## Security

- Passwords, OTPs and Trip PINs are stored only as hashes
- Role checks and ownership checks on every protected route
- NID images live outside `static/`, are served only to admins, and every view is logged
- Session timeout (30 minutes, 20 for admins), HttpOnly and SameSite cookies, HTTPS on the live site
- OTP resend limit and attempt lock, Trip PIN lock after 5 wrong tries
- Chat and SOS data is visible only to people on that ride and to admins

## Testing

64 manual test cases covering every role and feature, all passed on the live site. See [docs/MANUAL_TEST_CASES.md](docs/MANUAL_TEST_CASES.md).

## User guide

Step-by-step help for passengers, drivers and admins: [docs/USER_GUIDE.md](docs/USER_GUIDE.md).

## Workflow

Every Jira task (SR-1 to SR-55) was built on its own branch named `feature/SR-XX-short-name`, committed with a message starting with `SR-XX:`, and merged through its own pull request by the member who owned the task.
