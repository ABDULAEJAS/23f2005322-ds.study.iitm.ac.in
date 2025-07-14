from flask import Flask, render_template, request, redirect, session, jsonify
import os
import datetime

app = Flask(__name__)
app.secret_key = 'boss_secret_key'

SLOT_FILE = 'slots.txt'
CITIES_FILE = 'cities.txt'
BOOKINGS_FILE = 'bookings.txt'
PAYMENTS_FILE = 'payments.txt'
n = datetime.datetime.now()

def read_lines(filename):
    if not os.path.exists(filename):
        return []
    with open(filename, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def get_cities():
    if os.path.exists(CITIES_FILE):
        with open(CITIES_FILE, 'r') as f:
            return [line.strip() for line in f if line.strip()]

def get_total_slots():
    try:
        return int(open(SLOT_FILE).read().strip())
    except:
        return 3

@app.route('/')
def home():
    return redirect('/signin')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        with open('users.txt', 'a+') as f:
            f.seek(0)
            for line in f:
                _, e, _ = line.strip().split(',')
                if e == email:
                    return "Email exists. <a href='/signin'>Login</a>"
            f.write(f"{name},{email},{password}\n")
        return redirect('/signin')
    return render_template('signup.html')

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password'].strip()

        # Admin login check
        if email == 'owner@gmail.com' and password == 'admin123':
            session['email'] = email
            session['name'] = 'Admin'
            return redirect('/admin')

        # User login check
        if os.path.exists('users.txt'):
            with open('users.txt', 'r') as f:
                for line in f:
                    try:
                        mail, pwd, name = line.strip().split(',')
                        if mail == email and pwd == password:
                            session['email'] = mail
                            session['name'] = name
                            return redirect('/user')
                    except:
                        continue  # skip invalid lines

        return "Invalid login. <a href='/signin'>Try again</a>"

    return render_template('signin.html')

@app.route('/user')
def user_dashboard():
    if 'email' not in session or session['email'] == 'owner@gmail.com':
        return redirect('/signin')
    return render_template('user.html', user_email=session['email'])
@app.route('/user_chart')
def user_chart():
    if 'email' not in session or session['email'] == 'owner@gmail.com':
        return redirect('/signin')

    email = session['email']
    revenue_data = {}  # {city: total_revenue}

    if os.path.exists('payments.txt'):
        with open('payments.txt', 'r') as f:
            for line in f:
                parts = line.strip().split(',')
                if len(parts) == 5 and parts[4] == email:
                    city = parts[0]
                    try:
                        amount = int(parts[2])
                        revenue_data[city] = revenue_data.get(city, 0) + amount
                    except:
                        continue

    labels = list(revenue_data.keys())
    values = list(revenue_data.values())

    return render_template('user_chart.html', labels=labels, values=values)
@app.route('/availability')
def availability():
    if 'email' not in session:
        return redirect('/signin')

    selected_city = request.args.get('city')  # From dropdown
    cities = get_cities()  # Read from cities.txt
    slots = {}

    if selected_city:
        slot_file = f'slots_{selected_city}.txt'
        if os.path.exists(slot_file):
            with open(slot_file, 'r') as sf:
                try:
                  total_slots = int(sf.read().strip())
                except:
                  total_slots = get_total_slots()
    else:
        total_slots = get_total_slots()
    # Mark all as vacant initially
    for i in range(1, total_slots + 1):
        slots[str(i)] = "Vacant"

        # Mark booked slots from bookings.txt
        if os.path.exists('bookings.txt'):
            with open('bookings.txt', 'r') as f:
                for line in f:
                    parts = line.strip().split(',')
                    if len(parts) >= 5 and parts[0] == selected_city:
                        booked_slot = parts[2]
                        booked_end = parts[4]
                        try:
                           booked_end_dt = datetime.datetime.strptime(booked_end, '%Y-%m-%d %H:%M')
                           if booked_end_dt > n:
                              slots[booked_slot] = "Booked"
                        except:
                            continue
                        

    return render_template('availability.html',
                           cities=cities,
                           selected_city=selected_city,
                           slots=slots)

@app.route('/user_history')
def user_history():
    if 'email' not in session:
        return redirect('/signin')

    email = session['email']
    bookings = []
    payments = []

    # Booking data (city, vehicle, slot, start, end, email)
    if os.path.exists('bookings.txt'):
        with open('bookings.txt', 'r') as f:
            for line in f:
                parts = line.strip().split(',')
                if len(parts) >= 6 and parts[5] == email:
                    bookings.append(parts[:5])

    # Payment data (city, vehicle, amount, date, email)
    if os.path.exists('payments.txt'):
        with open('payments.txt', 'r') as f:
            for line in f:
                parts = line.strip().split(',')
                if len(parts) >= 5 and parts[4] == email:
                    payments.append(parts[:4])

    return render_template('user_history.html', bookings=bookings, payments=payments)

@app.route('/user/book')
def book_slot_redirect():
    if 'email' not in session or session['email'] == 'owner@gmail.com':
        return redirect('/signin')
    return redirect('/book')

@app.route('/about')
def about():
    if 'email' not in session or session['email'] == 'owner@gmail.com':
        return redirect('/signin')
    return render_template('about.html')

@app.route('/book', methods=['GET', 'POST'])
def book():
    if 'email' not in session or session['email'] == 'owner@gmail.com':
        return redirect('/signin')

    cities = get_cities()
    total_slots = get_total_slots()

    if not cities:
        return "<h3 style='color: red;'>No cities available. Admin must add cities.</h3>"

    if request.method == 'POST':
        city = request.form['city'].strip()
        vehicle = request.form['vehicle'].strip().upper()
        slot = request.form['slot'].strip()
        start = request.form['start'].strip()
        end = request.form['end'].strip()

        try:
            start_dt = datetime.datetime.strptime(start, '%Y-%m-%dT%H:%M')
            end_dt = datetime.datetime.strptime(end, '%Y-%m-%dT%H:%M')
        except:
            return "<h3 style='color: red;'>Invalid datetime format.</h3>"

        # Check for slot conflicts
        if os.path.exists('bookings.txt'):
            with open('bookings.txt', 'r') as f:
                for line in f:
                    parts = line.strip().split(',')
                    if len(parts) >= 5:
                        booked_city, booked_vehicle, booked_slot, booked_start, booked_end, email = parts
                        if city == booked_city and slot == booked_slot:
                            booked_start_dt = datetime.datetime.strptime(booked_start, '%Y-%m-%d %H:%M')
                            booked_end_dt = datetime.datetime.strptime(booked_end, '%Y-%m-%d %H:%M')
                            if start_dt < booked_end_dt and end_dt > booked_start_dt:
                                return "<h3 style='color:red;'>⚠ Slot already booked in this time range. <a href='/book'>Try again</a></h3>"

        # Save in session
        session['city'] = city
        session['vehicle'] = vehicle
        session['slot'] = slot
        session['start'] = start
        session['end'] = end

        return redirect('/payment')

    return render_template('book.html', cities=cities, total_slots=total_slots)

@app.route('/get_slots')
def get_slots():
    city = request.args.get('city')
    slot_file = f'slots_{city}.txt'
    try:
        if city and os.path.exists(slot_file):
            with open(slot_file, 'r') as sf:
                total_slots = int(sf.read().strip())
        else:
            total_slots = get_total_slots()
    except:
        total_slots = 3

    # Find booked slots for this city, only if booking end time is in the future
    booked_slots = set()
    if os.path.exists('bookings.txt'):
        with open('bookings.txt', 'r') as f:
            for line in f:
                parts = line.strip().split(',')
                if len(parts) >= 5 and parts[0] == city:
                    booked_slot = parts[2]
                    booked_end = parts[4]
                    try:
                        booked_end_dt = datetime.datetime.strptime(booked_end, '%Y-%m-%d %H:%M')
                        if booked_end_dt > n:
                            booked_slots.add(booked_slot)
                    except:
                        continue

    available_slots = [str(i) for i in range(1, total_slots + 1) if str(i) not in booked_slots]

    return jsonify({'available_slots': available_slots})

@app.route('/payment', methods=['GET', 'POST'])
def payment():
    if 'email' not in session or 'vehicle' not in session or 'slot' not in session:
        return redirect('/signin')

    try:
        city = session['city']
        vehicle = session['vehicle']
        slot = session['slot']
        start = session['start']
        end = session['end']
        email = session['email']

        start_dt = datetime.datetime.strptime(start, '%Y-%m-%dT%H:%M')
        end_dt = datetime.datetime.strptime(end, '%Y-%m-%dT%H:%M')
        hours = max(1, int((end_dt - start_dt).total_seconds() // 3600))
        amount = hours * 500

        # Double-check slot conflict
        conflict = False
        if os.path.exists('bookings.txt'):
            with open('bookings.txt', 'r') as f:
                for line in f:
                    parts = line.strip().split(',')
                    if len(parts) >= 5 and parts[0] == city and parts[2] == slot:
                        existing_start = datetime.datetime.strptime(parts[3], '%Y-%m-%d %H:%M')
                        existing_end = datetime.datetime.strptime(parts[4], '%Y-%m-%d %H:%M')
                        if start_dt < existing_end and end_dt > existing_start:
                            conflict = True
                            break

        if conflict:
            return "<h2 style='color:red;'>❌ Slot already booked. <a href='/book'>Try another</a></h2>"

        if request.method == 'POST':
            # Save booking and payment
            with open('bookings.txt', 'a') as f:
                f.write(f"{city},{vehicle},{slot},{start_dt.strftime('%Y-%m-%d %H:%M')},{end_dt.strftime('%Y-%m-%d %H:%M')},{email}\n")
            with open('payments.txt', 'a') as p:
                p.write(f"{city},{vehicle},{amount},{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')},{email}\n")

            for key in ['city', 'vehicle', 'slot', 'start', 'end']:
                session.pop(key, None)

            return "<h2 style='color:green;'>✅ Booking Confirmed and Payment Successful!</h2><a href='/book'>Book Another</a>"

        return render_template('payment.html',
                               vehicle=vehicle,
                               slot=slot,
                               start=start_dt.strftime('%Y-%m-%d %H:%M'),
                               end=end_dt.strftime('%Y-%m-%d %H:%M'),
                               city=city,
                               hours=hours,
                               amount=amount)

    except Exception as e:
        return f"<h3 style='color:red;'>Error: {e}</h3><a href='/book'>Back</a>"

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'email' not in session or session['email'] != 'owner@gmail.com':
        return redirect('/signin')

    cities = read_lines(CITIES_FILE)
    total_slots = get_total_slots()

    if request.method == 'POST':
        if 'new_city' in request.form:
            new = request.form['new_city'].strip()
            if new and new not in cities:
                cities.append(new)
                write_lines(CITIES_FILE, cities)
                open(os.path.join(BOOKINGS_DIR, f"{new}.txt"), 'a').close()

        elif 'del_city' in request.form:
            d = request.form['del_city'].strip()
            if d in cities:
                cities.remove(d)
                write_lines(CITIES_FILE, cities)
                try:
                    os.remove(os.path.join(BOOKINGS_DIR, f"{d}.txt"))
                except:
                    pass

        elif 'total_slots' in request.form:
            try:
                slots = int(request.form['total_slots'])
                with open(SLOT_FILE, 'w') as f:
                    f.write(str(slots))
                total_slots = slots
            except:
                pass

        return redirect('/admin')

    bookings = [line.strip().split(',') for line in read_lines(BOOKINGS_FILE)]
    payments = [line.strip().split(',') for line in read_lines(PAYMENTS_FILE)]
    total_revenue = sum(int(p[2]) for p in payments if len(p) >= 2)

    return render_template('admin.html',
                           cities=cities,
                           total_slots=total_slots,
                           bookings=bookings,
                           payments=payments,
                           total_revenue=total_revenue)

@app.route('/manage_cities', methods=['GET', 'POST'])
def manage_cities():
    if 'email' not in session or session['email'] != 'owner@gmail.com':
        return redirect('/signin')

    cities = []
    slot_data = {}

    # Load cities
    if os.path.exists('cities.txt'):
        with open('cities.txt', 'r') as f:
            cities = [line.strip() for line in f if line.strip()]

    # Handle form submissions
    if request.method == 'POST':
        # Add City
        if 'add_city' in request.form:
            new_city = request.form.get('new_city').strip()
            if new_city and new_city not in cities:
                with open('cities.txt', 'a') as f:
                    f.write(f"{new_city}\n")
                cities.append(new_city)
                # Create default slot file
                with open(f'slots_{new_city}.txt', 'w') as sf:
                    sf.write("3")  # Default 3 slots

        # Delete City
        elif 'del_city' in request.form:
            del_city = request.form.get('del_city')
            if del_city in cities:
                cities.remove(del_city)
                with open('cities.txt', 'w') as f:
                    for city in cities:
                        f.write(f"{city}\n")
                # Delete slot file if exists
                slot_file = f'slots_{del_city}.txt'
                if os.path.exists(slot_file):
                    os.remove(slot_file)

        # Update Slots
        elif 'update_slot' in request.form:
            slot_city = request.form.get('slot_city')
            slot_count = request.form.get('slot_count')
            if slot_city and slot_count:
                with open(f'slots_{slot_city}.txt', 'w') as sf:
                    sf.write(str(slot_count))

    # Reload updated cities and slot data
    cities = []
    if os.path.exists('cities.txt'):
        with open('cities.txt', 'r') as f:
            cities = [line.strip() for line in f if line.strip()]
    
    for city in cities:
        slot_file = f'slots_{city}.txt'
        if os.path.exists(slot_file):
            with open(slot_file, 'r') as sf:
                try:
                    count = int(sf.read().strip())
                except:
                    count = 0
        else:
            count = 0
        slot_data[city] = count

    return render_template('manage_cities.html', cities=cities, slot_data=slot_data)

@app.route('/current_bookings')
def current_bookings():
    if 'email' not in session or session['email'] != 'owner@gmail.com':
        return redirect('/signin')

    selected_city = request.args.get('city')
    cities = get_cities()
    slots_status = {}

    if selected_city:
        slot_file = f'slots_{selected_city}.txt'
        if os.path.exists(slot_file):
            with open(slot_file, 'r') as sf:
                try:
                    total_slots = int(sf.read().strip())
                except:
                    total_slots = 3
        else:
            total_slots = 3

        # Mark all as Vacant
        for i in range(1, total_slots + 1):
            slots_status[str(i)] = ("Vacant", "")

        # Mark booked slots and store vehicle
        if os.path.exists('bookings.txt'):
            with open('bookings.txt', 'r') as f:
                for line in f:
                    parts = line.strip().split(',')
                    if len(parts) >= 6 and parts[0] == selected_city:
                        booked_slot = parts[2]
                        booked_vehicle = parts[1]
                        booked_end = parts[4]
                        try:
                            booked_end_dt = datetime.datetime.strptime(booked_end, '%Y-%m-%d %H:%M')
                            if booked_end_dt > datetime.datetime.now():
                                slots_status[booked_slot] = ("Booked", booked_vehicle)
                        except:
                            continue

    return render_template('current_bookings.html',
                           cities=cities,
                           selected_city=selected_city,
                           slots_status=slots_status)
@app.route('/booking_history')
def booking_history():
    if session.get('email') != 'owner@gmail.com':
        return redirect('/signin')

    selected_city = request.args.get('city')
    cities = get_cities()
    bookings = []
    if os.path.exists('bookings.txt'):
        with open('bookings.txt', 'r') as f:
            for line in f:
                parts = line.strip().split(',')
                if len(parts) >= 6:
                    if not selected_city or parts[0] == selected_city:
                        bookings.append(parts[:6])

    return render_template('booking_history.html', bookings=bookings, cities=cities, selected_city=selected_city)
@app.route('/payment_history')
def payment_history():
    if 'email' not in session:
        return redirect('/signin')

    if session['email'] != 'owner@gmail.com':
        return "Access Denied"

    selected_city = request.args.get('city')
    cities = get_cities()
    payments = []
    if os.path.exists('payments.txt'):
        with open('payments.txt', 'r') as f:
            for line in f:
                parts = line.strip().split(',')
                if len(parts) == 5:
                    if not selected_city or parts[0] == selected_city:
                        payments.append(parts)
    return render_template('payment_history.html', payments=payments, cities=cities, selected_city=selected_city)         

@app.route('/api/add_city', methods=['POST'])
def add_city():
    city = request.json.get('city')
    cities = read_lines('cities.txt')
    if city and city not in cities:
        cities.append(city)
        write_lines('cities.txt', cities)

        # Ensure bookings folder exists
        os.makedirs(BOOKINGS_DIR, exist_ok=True)

        # Create a file for the new city
        open(os.path.join(BOOKINGS_DIR, f"{city}.txt"), 'a').close()

    return jsonify(success=True)                    

@app.route('/chart')
def chart():
    if 'email' not in session or session['email'] != 'owner@gmail.com':
        return redirect('/signin')

    revenue_data = {}  # {city: total_revenue}

    if os.path.exists('payments.txt'):
        with open('payments.txt', 'r') as f:
            for line in f:
                parts = line.strip().split(',')
                if len(parts) >= 3:
                    city = parts[0]
                    try:
                        amount = int(parts[2])
                        revenue_data[city] = revenue_data.get(city, 0) + amount
                    except:
                        continue  # Skip bad data

    labels = list(revenue_data.keys())
    values = list(revenue_data.values())

    return render_template('chart.html', labels=labels, values=values)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/signin')

if __name__ == '__main__':
    app.run(debug=True)