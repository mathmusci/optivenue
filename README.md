# Optivenue - Hospitality Management System

A lightweight Flask-based application for managing event bookings across multiple venues, enforcing personnel constraints and venue availability.

---

## 📦 Features

- Book events (weddings, parties, corporate functions, etc.)
- Validate against venue capacity and personnel limits (real-time checks)
- Enforce venue opening hours (including overnight)
- Dynamic form filtering for available venues
- Admin panel to view events, venues, and staffing capacity

---

## 🚀 Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/mathmusci/optivenue.git
cd optivenue
```

### 2. Create a Python Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 📊 Seed the Database

Prepare two CSV files:

### `venues.csv`

```csv
venue_name,location_name,capacity,personnel_required,open_time,close_time
Grand Hall,City Centre,200,12,09:00,23:00
Night Lounge,Downtown,100,8,18:00,03:00
```

### `personnel_availability.csv`

```csv
month,available_personnel
2025-05,120
2025-06,110
...
```

Then run the seeding script:

```bash
python seed_data.py
```

This will recreate the database and populate it with venue and personnel data.

---

## 🖥️ Run the Application

```bash
python main.py
```

Then open your browser at:  
**[http://localhost:5000](http://localhost:5000)**

---

## 📁 File Structure

```
.
├── main.py     				   # Main Flask app
├── seed_data.py                   # DB seeding script
├── templates/                     # HTML templates
│   ├── admin.html
│   ├── book.html
│   └── upload.html
├── uploads/                       # CSV upload folder
├── static/                        # Optional static assets
├── hospitality.db                 # SQLite database
└── requirements.txt
```

---

## 🧠 Notes

- Python 3.8+ recommended
- Uses SQLite for storage (no setup required)
- Timestamps default to local system time (`datetime.now()`)