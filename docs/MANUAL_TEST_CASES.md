# ShareRide – Manual Test Case Document

| Item | Detail |
|---|---|
| Project | ShareRide – community ride-sharing web app |
| Course | CSE 314 Software Engineering Lab, Section C1, UAP |
| Jira task | SR-53 |
| Tester | Jannatul Ferdaus Khusbu Upoma |
| Environment | Live site `https://upoma.pythonanywhere.com` (Chrome on laptop and Android phone) |
| Build | `main` branch after SR-52 |
| Test date |05-11-2026|

## How to use this document

1. Before testing, reset the demo data on the server: `flask --app app seed-demo --fresh`, then **Reload** the web app.
2. Run each case in order. Write **Pass** or **Fail** in the Result column.
3. For every **Fail**, write a short note in the Notes column. All failures are fixed in **SR-55 (Bug fixing)**.

## Test accounts (password for all: `demo1234`)

| Role | Name | Phone | State |
|---|---|---|---|
| Admin | Demo Admin | 01700000000 | Active |
| Driver | Rahim Uddin | 01700000001 | NID verified |
| Driver | Nusrat Jahan | 01700000002 | NID verified |
| Driver | Karim Mia | 01700000003 | NID pending |
| Passenger | Ayesha Siddiqua | 01700000011 | NID verified |
| Passenger | Tanvir Ahmed | 01700000012 | NID verified |
| Passenger | Mim Akter | 01700000013 | NID verified |
| Passenger | Rafi Islam | 01700000014 | NID pending |
| Passenger | Sabbir Hossain | 01700000015 | Suspended |

---

## A. Public pages and accounts

| ID | Test case | Account | Steps | Expected result | Result | Notes |
|---|---|---|---|---|---|---|
| TC-01 | Home page loads | Guest | Open the site | Hero text, Join/Sign in buttons, ride search box and Upcoming rides are shown. No stat boxes. |Pass| |
| TC-02 | About page | Guest | Click **About** in the navbar | How it works, Features and Your safety are shown in compact cards. |Pass | |
| TC-03 | Dark mode | Guest | Click 🌙, reload the page, then click ☀️ | Site turns dark, stays dark after reload, turns light again. Images and emoji are not inverted. |Pass | |
| TC-04 | Mobile menu | Guest (phone) | Tap ☰, tap a link, tap outside | Menu opens, closes on link tap and on outside tap. |Pass | |
| TC-05 | Register with demo OTP | New user | Register as a passenger with a new phone | Verify page shows a yellow box with the demo code. |Pass | |
| TC-06 | Wrong OTP | New user | Enter a wrong 6-digit code | "Wrong code" message, attempts counted. |Pass | |
| TC-07 | Correct OTP | New user | Enter the demo code | Phone verified, redirected to Sign in. | Pass| |
| TC-08 | Resend OTP limit | New user | Press **Send a new code** twice quickly | Second press shows "Please wait a minute". |Pass | |
| TC-09 | Wrong password | Ayesha | Sign in with a wrong password | Generic "phone or password is incorrect" message. |Pass | |
| TC-10 | Suspended account | Sabbir | Sign in | Login is blocked with an account suspended message. |Pass | |
| TC-11 | Role protection | Ayesha | Open `/admin` and `/provider/dashboard` in the address bar | Access is refused (not found or redirected). |Pass | |

## B. Passenger

| ID | Test case | Account | Steps | Expected result | Result | Notes |
|---|---|---|---|---|---|---|
| TC-12 | Dashboard search box | Ayesha | Sign in | Hello card and "Where are you going?" box with From, To, Date, Time, Seats. |Pass | |
| TC-13 | Search from dashboard | Ayesha | Fill To = "Savar", clear date, press **Search** | Find a ride page shows matching rides. |Pass | |
| TC-14 | Time label | Ayesha | Open **Find a ride** | Field is labelled **Time (from this time on)**. |Pass | |
| TC-15 | Time filter | Ayesha | Search with a time after 9:00 AM | Only rides leaving at or after that time are shown. |Pass | |
| TC-16 | Request a seat | Tanvir | Open Mohakhali → Savar, request 1 seat | Booking page opens with status Pending, timeline at step 1. |Pass | |
| TC-17 | Pending hides contact | Tanvir | View the pending booking | Plate and phone hidden, message says they are shared after acceptance. |Pass | |
| TC-18 | Cancel booking | Tanvir | Cancel the pending booking | Status Cancelled, seats released on the ride. |Pass | |
| TC-19 | My bookings filters | Ayesha | Click each status tab, then **This week**, then **Clear filters** | Lists change correctly, counts match, Clear shows Upcoming and Past again. |Pass | |
| TC-20 | Date range filter | Ayesha | Set From/To around 2 days ago and Apply | Only bookings for rides in that range are shown. |Pass | |
| TC-21 | Driver contact after trip | Ayesha | Open Farmgate → Uttara booking | Plate, phone link and **Call driver** button are shown for a completed trip. | Pass| |
| TC-22 | Trip PIN | Mim | Open Dhanmondi 27 → Gulshan 1 booking, press **Show my Trip PIN** | A 4-digit PIN is shown on its own page. |Pass | |
| TC-23 | Receipt | Ayesha | Open Farmgate → Uttara booking, **View receipt**, print preview | Receipt shows number, amount and method. Print view hides the navbar and is light. | Pass| |
| TC-24 | Pay for a trip | Mim | On a completed unpaid trip choose bKash, enter a transaction ID | Payment saved, receipt opens. Duplicate transaction ID is rejected. |Pass | |
| TC-25 | Rate the driver | Tanvir | Rate a completed trip that is not rated yet | Rating saved, driver's average updates, button changes to "You rated". | Pass| |
| TC-26 | Trip history | Ayesha | My bookings → **Trip history** | Completed trips, total spent and unpaid count are correct. |Pass | |
| TC-27 | Missed booking | Any passenger | Open a booking on a ride that passed its time by 2+ hours without starting | Status Missed (grey), note "The driver did not start this ride". | Pass| |
| TC-28 | Complaint | Mim | Report a problem on Mirpur 10 → Motijheel | Complaint saved, listed under Complaints with status Open. |Pass | |

## C. Ride chat and SOS

| ID | Test case | Account | Steps | Expected result | Result | Notes |
|---|---|---|---|---|---|---|
| TC-29 | Send chat message | Mim | Open ride chat on Mirpur 10 → Motijheel, type and press Enter | Message appears on the right in blue. | Pass| |
| TC-30 | Live chat update | Mim + Nusrat (2 browsers) | Keep both chats open, send from one | Message appears in the other within about 5 seconds without refresh. |Pass | |
| TC-31 | Closed chat | Ayesha | Open chat on Farmgate → Uttara (ended over 24 hours ago) | Red "closed" bar, no message box. |Pass | |
| TC-32 | Chat access control | Tanvir | Open `/chat/ride/<id>` of a ride he is not on | Page not found. |Pass | |
| TC-33 | SOS with location | Ayesha (phone) | Active ride → SOS → allow location | SOS sent, page shows "Sharing your live location". |Pass | |
| TC-34 | Live location | Ayesha (phone) | Keep the active ride page open for 1 minute | "last sent" time updates about every 30 seconds. |Pass | |
| TC-35 | SOS stops after resolve | Ayesha (phone) | Admin resolves the alert while page is open | Page shows "Your SOS has been resolved by an admin". | Pass| |

## D. Driver

| ID | Test case | Account | Steps | Expected result | Result | Notes |
|---|---|---|---|---|---|---|
| TC-36 | Dashboard stats | Rahim | Sign in | Total rides, Upcoming and Earnings boxes are correct. |Pass | |
| TC-37 | Dashboard on phone | Rahim (phone) | Open dashboard | Three small boxes side by side, rides shown as cards, nothing cut off. |Pass | |
| TC-38 | Dashboard on laptop | Rahim | Open dashboard | Rides shown as a table only, no duplicate cards. |Pass | |
| TC-39 | Ride filters | Rahim | Click each status tab, This month, From/To, Clear | Correct rides and counts, Missed tab included. | Pass| |
| TC-40 | Post a ride | Rahim | **+ Post a ride** with valid data | Ride appears as Scheduled. Seats above vehicle capacity are rejected. |Pass | |
| TC-41 | Edit and cancel ride | Rahim | Edit the new ride, then cancel it | Changes saved, then status Cancelled and bookings cancelled. |Pass | |
| TC-42 | Unverified driver | Karim | Try to post a ride | Blocked with "after an admin verifies your NID". |Pass | |
| TC-43 | Accept and reject | Nusrat | Open Banani → Bashundhara requests, accept or reject a pending request | Status updates, seats change only on accept. | Pass| |
| TC-44 | Trip PIN check-in | Rahim | Start trip, enter a wrong PIN, then Mim's correct PIN | Wrong PIN shows attempts left. Correct PIN marks Mim On board. |Pass | |
| TC-45 | Complete trip | Rahim | Press **Complete trip** | Ride Completed, on-board passengers Completed, others cancelled, PINs cleared. | Pass| |
| TC-46 | History button | Rahim | Look at completed, cancelled and missed rides | They show **History** instead of Requests. |Pass | |
| TC-47 | History page | Rahim | Open History on Farmgate → Uttara | Ride details, passengers with phone and payment, receipts, chat history, reviews, earnings. | Pass| |
| TC-48 | Rate passenger | Rahim | Rate Tanvir from the History page | Rating saved, stars shown instead of the Rate button. |Pass | |

## E. Admin

| ID | Test case | Account | Steps | Expected result | Result | Notes |
|---|---|---|---|---|---|---|
| TC-49 | Overview | Admin | Sign in | Buttons for Users, Rides, Complaints, Audit log, Review NIDs, and the red SOS box. | Pass| |
| TC-50 | NID approve and reject | Admin | Approve Karim, reject Rafi with a reason | Statuses change, entries added to the audit log. Reject without reason is refused. |Pass | |
| TC-51 | Suspend and reinstate | Admin | Suspend Tanvir with a reason, then reinstate | Tanvir cannot sign in while suspended, can after reinstating. |Pass | |
| TC-52 | Users search | Admin | Search "Rahim", filter by role and status | Matching users only. |Pass | |
| TC-53 | Rides monitoring | Admin | Open Rides, check each tab including Missed | Counts and lists are correct, SOS rides are highlighted. |Pass | |
| TC-54 | Handle complaint | Admin | Open "AC was not working", set Investigating, then Resolved with a reply | Complainant sees the reply. Reply under 5 characters is refused. |Pass | |
| TC-55 | SOS detail page | Admin | Overview → SOS **Open** | Map, Google Maps link, ride, driver with plate, passengers with Call buttons, quick actions. | Pass| |
| TC-56 | SOS live map | Admin | Keep the SOS page open while TC-34 runs | Map and "Last update" refresh about every 15 seconds. | Pass| |
| TC-57 | Resolve SOS with note | Admin | Resolve with a note | Status Resolved, resolver and time shown, note in audit log. |Pass | |
| TC-58 | Audit log filters | Admin | Filter by action type, admin, From date and To date | Date fields are labelled. Results match the filters. |Pass | |
| TC-59 | Audit CSV | Admin | **Download CSV** and open in Excel | File opens with the filtered rows and readable text. |Pass | |
| TC-60 | Admin reads chat | Admin | From a complaint, open **Read ride chat** | Messages visible, read-only note, no message box. | Pass| |

## F. System behaviour

| ID | Test case | Account | Steps | Expected result | Result | Notes |
|---|---|---|---|---|---|---|
| TC-61 | Bangladesh time | Any | Send a chat message or SOS and note the shown time | Time matches the phone clock (Bangladesh time), no "UTC" labels. |Pass | |
| TC-62 | Missed rides | Admin | After a scheduled ride passes its time by 2 hours, open any page | Ride and its pending/accepted bookings become Missed automatically. |Pass | |
| TC-63 | HTTPS | Any | Open `http://upoma.pythonanywhere.com` | Redirected to `https://`, padlock shown. |Pass | |
| TC-64 | Session timeout | Ayesha | Stay idle for 30 minutes, then click a link | Asked to sign in again. |Pass | |

---

## Summary

| Section | Total | Pass | Fail |
|---|---|---|---|
| A. Public pages and accounts | 11 | 11|0 |
| B. Passenger | 17 | 17|0 |
| C. Ride chat and SOS | 7 |7 |0 |
| D. Driver | 13 | 13|0 |
| E. Admin | 12 | 12|0 |
| F. System behaviour | 4 |4 |0 |
| **Total** | **64** |**64** |**0** |

**Failed cases moved to SR-55:** None