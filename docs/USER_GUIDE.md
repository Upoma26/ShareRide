# ShareRide User Guide

ShareRide connects people going the same way in Dhaka. This guide explains how to use the site as a **passenger**, a **driver** and an **admin**.

Site: https://upoma.pythonanywhere.com

---

## 1. Getting started

### Create an account
1. Click **Register**.
2. Choose **Passenger** (to find rides) or **Driver** (to offer rides).
3. Fill in your name, phone, email, password and NID number, and upload the front and back of your NID.
4. Enter the 6-digit code sent to your phone. In demo mode the code is shown in a yellow box on the same page.
5. Sign in with your phone and password.

Your NID is checked by an admin. Until it is verified you can sign in but cannot book or post rides.

### Light and dark mode
Tap **🌙** in the top bar for dark mode and **☀️** to switch back. The site remembers your choice.

### On a phone
Tap **☰** to open the menu.

---

## 2. Passenger guide

### Find a ride
1. After signing in, use the **Where are you going?** box on your dashboard (or **Find a ride** in the menu).
2. Enter **From**, **To**, **Date**, **Time** (rides leaving from this time on) and **Seats**.
3. Press **Search** and open a ride to see the route, fare, seats left, driver and reviews.

### Book a seat
1. On the ride page choose the number of seats and send a request.
2. Your booking page shows a timeline: **Requested → Accepted → On board → Completed**.
3. While it is **Pending** you can cancel it from **My bookings**.

When the driver accepts, the page shows the **plate number**, **driver's phone** and a **📞 Call driver** button.

### Get in the car with your Trip PIN
1. Open your booking and press **Show my Trip PIN**.
2. Tell the 4-digit PIN to your driver at pickup. The driver enters it and you become **On board**.
3. Each press creates a new PIN, so always use the latest one. Never share it with anyone else.

### During the trip
- Open **Open active ride & SOS** from your booking.
- Use **Open ride chat** to talk to the driver and other passengers.
- If you feel unsafe press **SOS** and allow location access. Keep the page open: your live location is sent to admins every 30 seconds until the alert is resolved. You can also tap **Call 999**.

### Pay and get a receipt
1. After boarding or completing the trip, press **Pay** on your booking.
2. Choose **Cash**, **bKash**, **Nagad** or **Card**. For mobile and card payments enter the transaction ID.
3. Your receipt opens and can be printed.

### Rate your driver
After the trip is completed press **⭐ Rate your driver**, choose 1 to 5 stars and add a comment.

### My bookings and trip history
- **My bookings** lists upcoming and past trips. Use the tabs (**Pending, Accepted, On board, Completed, Cancelled, Missed**), **Today / This week / This month** or **From / To** dates to filter.
- **Trip history** shows completed trips, total spent and unpaid trips.

### Missed rides
If the driver does not start the ride within 2 hours of its time, your booking becomes **Missed**. You can report it from **Complaints**.

### Report a problem
Press **Report a problem** on a booking, choose a category, and describe what happened. Follow the status and the admin's reply under **Complaints**.

---

## 3. Driver guide

### Add a vehicle and post a ride
1. Press **+ Post a ride**.
2. Choose or add your vehicle (brand, model, colour, plate, seats).
3. Enter pickup, destination, date, time, seats and fare per seat, then post.

You can **Edit** or **Cancel** a scheduled ride from your dashboard. Cancelling also cancels its bookings.

### Your dashboard
- The top boxes show **Total rides**, **Upcoming** and **Earnings**.
- Filter your rides by status (**Scheduled, Started, Completed, Cancelled, Missed**) and by date.
- On a phone each ride appears as a card.

### Handle requests
Open **Requests** on a ride to **Accept** or **Reject** passengers. Seats are reserved only when you accept.

### Start and finish a trip
1. Press **Start trip** on the ride.
2. Ask each passenger for their Trip PIN and enter it. After 5 wrong tries that passenger is locked.
3. When everyone has arrived, press **Complete trip**. Passengers who never boarded are cancelled and all PINs are cleared.

Start the ride within 2 hours of its time, otherwise it is marked **Missed** and can no longer be started.

### Ride history
Completed, cancelled and missed rides show a **History** button. It shows ride times, each passenger's phone, seats, fare and payment (with receipts), the chat history, reviews you received, and your earnings for that ride. Press **⭐ Rate** to rate a passenger.

---

## 4. Admin guide

### Overview
Sign in as admin to see buttons for **Users**, **Rides**, **Complaints**, **Audit log** and **Review NIDs**, plus a red box for any open **SOS alerts**.

### Verify NIDs and manage accounts
1. Open **Review NIDs**, view the front and back images (every view is logged).
2. **Approve**, or **Reject** with a reason.
3. On the same page use **Account actions** to **Suspend**, **Block** (with a reason) or **Reinstate** a member.

### Users and rides
- **Users**: search by name, phone or email and filter by role and status.
- **Rides**: status tabs with counts (including **Missed**), date and route filters. Rides with an SOS are highlighted.

### Handle complaints
1. Open **Complaints**, choose a tab and open a complaint.
2. Check the ride, the people involved, earlier complaints, and use **Read ride chat** as evidence.
3. Set **Investigating**, or **Resolved / Dismissed** with a reply the user will see. When resolving you can give a warning, or suspend or block the account.

### Respond to an SOS
1. Click **Open** on the alert in the overview.
2. The SOS page shows a live map (updated every 15 seconds), the last update time and accuracy, the ride, driver and plate, and every passenger with a **Call** button.
3. Use **Call 999**, call the sender or driver, or read the ride chat.
4. Write what action was taken and press **Mark as resolved**. The sender's phone stops sharing location.

### Audit log
Every admin action is recorded. Filter by action type, admin, **From date**, **To date** or text, and use **Download CSV** for reports.

---

## 5. Safety tips

- Check that the plate number matches before getting in.
- Share your Trip PIN only with your driver at pickup.
- Keep the active ride page open during the trip if you have sent an SOS.
- Report any problem from your booking. Admins review every complaint.
