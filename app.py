from enum import unique

from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///events2.db'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
migrate = Migrate(app, db)

# User model for the User table
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    bookings = db.relationship('Booking', backref='user_owner', lazy=True)

# Event model for the Event table
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    venue = db.Column(db.String(200), nullable=False)
    held_by = db.Column(db.String(100), nullable=False)
    participants_count = db.Column(db.Integer, nullable=False)
    food_type = db.Column(db.String(100), nullable=False)
    price = db.Column(db.String(100), nullable=False)
    bookings = db.relationship('Booking', backref='booking_info', lazy=True)


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)

    # Use a unique backref name to avoid conflicts
    event = db.relationship('Event', backref=db.backref('event_bookings', lazy=True))
    user = db.relationship('User', backref='user_bookings', lazy=True)

    __table_args__ = (db.UniqueConstraint('user_id', 'event_id', name='_user_event_uc'),)


from datetime import datetime
from sqlalchemy.exc import IntegrityError

# Helper function to create tables and add sample data
def create_tables():
    db.create_all()

    # List of events to be added
    events = [
        {'name': 'India Tech Conference 2024', 'date': '2024-12-05', 'venue': 'Bengaluru, Karnataka',
         'held_by': 'Tech Innovations', 'participants_count': 300, 'food_type': 'Vegetarian', 'price': '100'},
        {'name': 'National Startup Expo 2024', 'date': '2024-11-18', 'venue': 'New Delhi, Delhi',
         'held_by': 'Startup India', 'participants_count': 500, 'food_type': 'Mixed', 'price': '200'},
        {'name': 'Mumbai Film Festival 2024', 'date': '2024-11-20', 'venue': 'Mumbai, Maharashtra',
         'held_by': 'Mumbai Film Society', 'participants_count': 1000, 'food_type': 'Vegan', 'price': '300'},
        {'name': 'Global AI Summit 2024', 'date': '2024-12-10', 'venue': 'Hyderabad, Telangana',
         'held_by': 'AI Research Institute', 'participants_count': 250, 'food_type': 'Non-Vegetarian', 'price': '150'},
        {'name': 'International Yoga Festival 2024', 'date': '2024-12-15', 'venue': 'Rishikesh, Uttarakhand',
         'held_by': 'Yoga Foundation', 'participants_count': 700, 'food_type': 'Ayurvedic', 'price': '50'},
        {'name': 'Bengaluru Design Week 2024', 'date': '2024-11-25', 'venue': 'Bengaluru, Karnataka',
         'held_by': 'Design Bengaluru', 'participants_count': 400, 'food_type': 'Vegetarian', 'price': '100'},
        {'name': 'Delhi International Book Fair 2024', 'date': '2024-12-02', 'venue': 'New Delhi, Delhi',
         'held_by': 'Book Publishers Association', 'participants_count': 600, 'food_type': 'Mixed', 'price': '120'},
        {'name': 'National Science Conference 2024', 'date': '2024-11-28', 'venue': 'Chennai, Tamil Nadu',
         'held_by': 'Indian Science Congress', 'participants_count': 350, 'food_type': 'Non-Vegetarian', 'price': '180'},
        {'name': 'Goa Music Festival 2024', 'date': '2024-12-12', 'venue': 'Goa, India',
         'held_by': 'Goa Tourism', 'participants_count': 800, 'food_type': 'Seafood', 'price': '250'},
        {'name': 'Kolkata Fashion Week 2024', 'date': '2024-12-18', 'venue': 'Kolkata, West Bengal',
         'held_by': 'Kolkata Fashion Association', 'participants_count': 400, 'food_type': 'Vegetarian', 'price': '200'}
    ]

    # Add each event only if it doesn't already exist in the database
    for event_data in events:
        try:
            # Create new Event instance
            new_event = Event(
                name=event_data['name'],
                date=datetime.strptime(event_data['date'], '%Y-%m-%d').date(),
                venue=event_data['venue'],
                held_by=event_data['held_by'],
                participants_count=event_data['participants_count'],
                food_type=event_data['food_type'],
                price=event_data['price']
            )
            db.session.add(new_event)
            db.session.commit()
        except IntegrityError:
            # Roll back if there's a duplicate constraint violation and skip without logging
            db.session.rollback()




# Routes
@app.route('/')
def home():
    create_tables()
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists! Please choose another one.', 'danger')
            return redirect(url_for('login'))
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('user_page'))
        else:
            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/user', methods=['GET', 'POST'])
@login_required
def user_page():
    user = current_user
    bookings = Booking.query.filter_by(user_id=user.id).all()
    events = Event.query.all()

    # Handle booking and cancelation
    if request.method == 'POST':
        if 'book_event' in request.form:
            event_id = request.form.get('event_id')
            existing_booking = Booking.query.filter_by(user_id=user.id, event_id=event_id).first()
            if existing_booking:
                flash('You have already booked this event!', 'warning')
            else:
                booking = Booking(user_id=user.id, event_id=event_id)
                db.session.add(booking)
                db.session.commit()
                flash('Event booked successfully!', 'success')
            return redirect(url_for('user_page'))

        elif 'add_event' in request.form:
            event_name = request.form.get('event_name')
            event_date = datetime.strptime(request.form.get('event_date'), '%Y-%m-%d').date()
            event_venue = request.form.get('event_venue')
            participants_count = int(request.form.get('event_participants_count'))
            food_type = request.form.get('event_food_type')
            held_by = request.form.get('event_held_by')
            price = request.form.get('event_price')

            # Check if required fields are populated
            if not event_name or not event_date or not event_venue:
                flash('All fields are required to add an event!', 'danger')
                return redirect(url_for('user_page'))

            # Create and add the new event to the database
            new_event = Event(
                name=event_name,
                date=event_date,
                venue=event_venue,
                participants_count=participants_count,
                food_type=food_type,
                held_by=held_by,
                price=price
            )
            db.session.add(new_event)
            db.session.commit()

            flash('New event added successfully!', 'success')
            return redirect(url_for('user_page'))


        elif 'cancel_booking' in request.form:
            booking_id = request.form.get('booking_id')
            booking = Booking.query.get(booking_id)
            if booking:
                db.session.delete(booking)
                db.session.commit()
                flash('Booking canceled successfully!', 'success')
            else:
                flash('Booking not found!', 'danger')
            return redirect(url_for('user_page'))

    return render_template('user_page.html', user_name=user.username, bookings=bookings, events=events)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))


@app.route('/cancel_booking/<int:booking_id>', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    # Find the booking to delete
    booking = Booking.query.get_or_404(booking_id)

    # Ensure that the logged-in user is the one who created the booking
    if booking.user_id != current_user.id:
        flash('You can only cancel your own bookings.', 'danger')
        return redirect(url_for('user_page'))

    # Remove the booking and commit changes
    db.session.delete(booking)
    db.session.commit()
    flash('Booking canceled successfully!', 'success')
    return redirect(url_for('user_page'))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

if __name__ == "__main__":
    app.run(debug=True)
