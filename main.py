from datetime import datetime, timedelta, time
from pytz import timezone
import pandas as pd
import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import joinedload
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField, DateTimeField, SubmitField
from wtforms.validators import DataRequired, NumberRange
from werkzeug.utils import secure_filename



app = Flask(__name__)
app.config["SECRET_KEY"] = "secret-key-goes-here"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///hospitality.db"
app.config["UPLOAD_FOLDER"] = "uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
db = SQLAlchemy(app)

### MODELS ###
class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    venues = db.relationship("Venue", backref="location", lazy=True)

class Venue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    personnel_required = db.Column(db.Integer, nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey("location.id"), nullable=False)
    open_time = db.Column(db.Time, nullable=False, default=time(9, 0))
    close_time = db.Column(db.Time, nullable=False, default=time(23, 0))
    events = db.relationship("Event", backref="venue", lazy=True)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(50), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    duration_hours = db.Column(db.Integer, nullable=False)
    participants = db.Column(db.Integer, nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey("venue.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone("Europe/Chisinau")))

class PersonnelAvailability(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    month = db.Column(db.String(7), nullable=False)  # Format: YYYY-MM
    available_personnel = db.Column(db.Integer, nullable=False)

### FORM ###
class BookingForm(FlaskForm):
    event_type = SelectField("Event type", choices=[
        ("wedding", "Wedding"),
        ("birthday", "Birthday party"),
        ("private", "Private function"),
        ("christening", "Christening"),
        ("corporate", "Corporate retreat")
    ], validators=[DataRequired()])
    start_time = DateTimeField("Start time", validators=[DataRequired()], format="%Y-%m-%dT%H:%M")
    duration_hours = IntegerField("Duration (hours)", validators=[DataRequired(), NumberRange(min=1, max=24)])
    participants = IntegerField("Number of participants", validators=[DataRequired(), NumberRange(min=1)])
    venue_id = SelectField("Available venues (make your choices above to see which venues are available)", coerce=int, validators=[DataRequired()])
    submit = SubmitField("Book event")

### HELPERS ###
def is_venue_available(venue, start, duration):
    end = start + timedelta(hours=duration)
    overnight = venue.close_time < venue.open_time

    # Check opening hours
    if overnight:
        if not ((start.time() >= venue.open_time or start.time() < venue.close_time) and
                (end.time() >= venue.open_time or end.time() < venue.close_time)):
            return False
    else:
        if not (venue.open_time <= start.time() <= venue.close_time and venue.open_time <= end.time() <= venue.close_time):
            return False

    for event in venue.events:
        e_start = event.start_time
        e_end = event.start_time + timedelta(hours=event.duration_hours)
        if not (end <= e_start or start >= e_end):
            return False
    return True

def is_personnel_capacity_ok(start: datetime, end: datetime, required: int) -> bool:
    month = start.strftime("%Y-%m")
    availability = PersonnelAvailability.query.filter_by(month=month).first()
    if not availability:
        return False

    step = timedelta(minutes=15)
    t = start
    while t < end:
        # Get candidate events that might overlap — filter in Python to avoid InstrumentedAttribute issues
        overlapping = Event.query.filter(Event.start_time <= t).all()

        active = [
            e for e in overlapping
            if e.start_time + timedelta(hours=e.duration_hours) > t
        ]
        total = sum(e.venue.personnel_required for e in active)
        if total + required > availability.available_personnel:
            return False
        t += step
    return True

def import_venues(filepath):
    df = pd.read_csv(filepath)
    for _, row in df.iterrows():
        loc = Location.query.filter_by(name=row["location_name"]).first()
        if not loc:
            loc = Location(name=row["location_name"])
            db.session.add(loc)
            db.session.flush()
        open_time = datetime.strptime(row["open_time"], "%H:%M").time()
        close_time = datetime.strptime(row["close_time"], "%H:%M").time()
        venue = Venue(
            name=row["venue_name"],
            capacity=int(row["capacity"]),
            personnel_required=int(row["personnel_required"]),
            location_id=loc.id,
            open_time=open_time,
            close_time=close_time
        )
        db.session.add(venue)
    db.session.commit()

def import_personnel(filepath):
    df = pd.read_csv(filepath)
    for _, row in df.iterrows():
        record = PersonnelAvailability(
            month=row["month"],
            available_personnel=int(row["available_personnel"])
        )
        db.session.add(record)
    db.session.commit()

### CONTROLLERS ###
@app.route("/")
def home():
    return redirect(url_for("admin_panel"))

@app.route("/admin")
def admin_panel():
    events = Event.query.options(joinedload(Event.venue))\
        .join(Venue)\
        .order_by(Event.start_time, Venue.name)\
        .all()

    venues = Venue.query.order_by(Venue.name).all()
    personnel = PersonnelAvailability.query.order_by(PersonnelAvailability.month).all()
    return render_template("admin.html", events=events, venues=venues, personnel=personnel)

@app.route("/book", methods=["GET", "POST"])
def book_event():
    form = BookingForm()
    # start = form.start_time.data or datetime.now()
    # duration = form.duration_hours.data or 1
    # participants = form.participants.data or 1
    # venues = Venue.query.all()
    # for v in venues:
    #     print(f"venue {v.name} has capacity {v.capacity} (is this venue available (start={start}, duration={duration})? {is_venue_available(v, start, duration)})")
    # available = [(v.id, v.name) for v in venues if v.capacity >= participants and is_venue_available(v, start, duration)]
    # available = [(v.id, v.name) for v in venues]
    # print(f"available: {available}")
    # form.venue_id.choices = available or []
    
    all_venues = Venue.query.all()
    form.venue_id.choices = [(v.id, v.name) for v in all_venues]  # Always populate valid choices
    visible_venues = []

    if request.method == "POST" and form.validate_on_submit():
        start = form.start_time.data
        duration = form.duration_hours.data
        end = start + timedelta(hours=duration)
        venue = Venue.query.get(form.venue_id.data)

        if is_personnel_capacity_ok(start, end, venue.personnel_required):
            new_event = Event(
                event_type=form.event_type.data,
                start_time=start,
                duration_hours=duration,
                participants=form.participants.data,
                venue_id=venue.id
            )
            db.session.add(new_event)
            db.session.commit()
            flash("Event booked successfully!")
            return redirect(url_for("admin_panel"))
        else:
            flash("Insufficient personnel capacity or venue unavailable during requested time.")
            return redirect(url_for("admin_panel"))
    if request.method == "POST" and not form.validate_on_submit():
        flash("Form validation failed!")
        flash(str(form.errors))
        for attr in ["start_time", "duration_hours", "participants", "venue_id"]:
            flash(attr + str(getattr(getattr(form, attr), "raw_data")) + str(getattr(getattr(form, attr), "data")))
        return redirect(url_for("admin_panel"))

    return render_template("book.html", form=form, visible_venues=visible_venues)

@app.route("/available_venues", methods=["POST"])
def available_venues():
    data = request.json
    start = datetime.strptime(data["start_time"], "%Y-%m-%dT%H:%M")
    duration = int(data["duration_hours"])
    end = start + timedelta(hours=duration)
    participants = int(data["participants"])

    venues = Venue.query.all()
    available = [
        {"id": v.id, "name": v.name}
        for v in venues
        if v.capacity >= participants and is_venue_available(v, start, duration) and is_personnel_capacity_ok(start, end, v.personnel_required)
    ]
    return {"venues": available}

@app.route("/upload", methods=["GET", "POST"])
def upload_data():
    if request.method == "POST":
        file_type = request.form.get("file_type")
        file = request.files["file"]
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)
            if file_type == "venues":
                import_venues(filepath)
                flash("Venues imported.")
            elif file_type == "personnel":
                import_personnel(filepath)
                flash("Personnel data imported.")
            return redirect(url_for("admin_panel"))
    return render_template("upload.html")


if __name__ == "__main__":
    app.run(debug=True)
