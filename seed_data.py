import pandas as pd
from flask import Flask
from main import db, Location, Venue, PersonnelAvailability, app
from datetime import datetime

# Paths to CSV files
VENUES_CSV = "venues.csv"
PERSONNEL_CSV = "personnel_availability.csv"

def seed_venues():
    df = pd.read_csv(VENUES_CSV)
    for _, row in df.iterrows():
        # Check or create location
        location = Location.query.filter_by(name=row["location_name"]).first()
        if not location:
            location = Location(name=row["location_name"])
            db.session.add(location)
            db.session.flush()  # Ensure location.id is available

        # Parse open/close times
        open_time = datetime.strptime(row["open_time"], "%H:%M").time()
        close_time = datetime.strptime(row["close_time"], "%H:%M").time()

        # Create venue
        venue = Venue(
            name=row["venue_name"],
            capacity=int(row["capacity"]),
            personnel_required=int(row["personnel_required"]),
            location_id=location.id,
            open_time=open_time,
            close_time=close_time
        )
        db.session.add(venue)
    db.session.commit()
    print("Venues and locations seeded.")

def seed_personnel():
    df = pd.read_csv(PERSONNEL_CSV)
    for _, row in df.iterrows():
        personnel = PersonnelAvailability(
            month=row["month"],
            available_personnel=int(row["available_personnel"])
        )
        db.session.add(personnel)
    db.session.commit()
    print("Personnel availability seeded.")

def main():
    with app.app_context():
        print("Dropping and recreating database...")
        db.drop_all()
        db.create_all()
        seed_venues()
        seed_personnel()
        print("Seeding complete.")

if __name__ == "__main__":
    main()
