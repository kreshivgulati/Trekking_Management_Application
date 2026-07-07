# Trekking_Management_Application
Adventure organizations require efficient systems to manage trekking activities involving trek organizers, staff, and participants. Currently, many trekking groups rely on spreadsheets, phone calls, or manual coordination, which makes it difficult to manage trek approvals, track bookings, avoid overbooking, and maintain trek history.
## Setup

1. Clone or extract the project.
2. Create and activate a virtual environment.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Start the application:

```bash
flask --app app run
```

On the first run, the application automatically:

- Creates the SQLite database (`instance/trek_management.db`)
- Creates all required tables
- Seeds the default admin account

Default Admin Credentials:

- Email: `admin@trekapp.com`
- Password: `12345678`
