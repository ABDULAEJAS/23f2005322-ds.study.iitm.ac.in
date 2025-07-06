from flask import Flask, render_template, request, redirect, session
import os
import datetime

app = Flask(__name__)
app.secret_key = 'boss_secret_key'

SLOT_FILE = 'slots.txt'

# Helper: Get total available slots
def get_total_slots():
    return int(open(SLOT_FILE).read().strip()) if os.path.exists(SLOT_FILE) else 3

@app.route('/')
def home():
    return redirect('/signin')

# SIGNUP
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password'].strip()

        with open('users.txt', 'a+') as f:
            f.seek(0)
            for line in f:
                _, e, _ = line.strip().split(',')
                if e == email:
                    return "Email already exists. <a href='/signin'>Login</a>"
            f.write(f"{name},{email},{password}\n")
        return redirect('/signin')
    return render_template('signup.html')

# SIGNIN
@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password'].strip()

        with open('users.txt', 'r') as f:
            for line in f:
                parts = line.strip().split(',')
                if len(parts) == 3 and parts[1] == email and parts[2] == password:
                    session['email'] = email
                    return redirect('/admin' if email == 'owner@gmail.com' else '/book')

        return "Invalid credentials. <a href='/signin'>Try again</a>"
    return render_template('signin.html')

# BOOK SLOT
@app.route('/book', methods=['GET', 'POST'])
def book():
    if 'email' not in session or session['email'] == 'owner@gmail.com':
        return redirect('/signin')

    total_slots = get_total_slots()

    if request.method == 'POST':
        vehicle = request.form['vehicle'].strip().upper()
        slot = request.form['slot'].strip()
        start = request.form['start'].strip()
        end = request.form['end'].strip()

        start_dt = datetime.datetime.strptime(start, '%Y-%m-%dT%H:%M')
        end_dt = datetime.datetime.strptime(end, '%Y-%m-%dT%H:%M')

        # Conflict check
        if os.path.exists('bookings.txt'):
            with open('bookings.txt', 'r') as f:
                for line in f:
                    v, s, existing_start, existing_end = line.strip().split(',')
                    if s == slot:
                        es = datetime.datetime.strptime(existing_start, '%Y-%m-%d %H:%M')
                        ee = datetime.datetime.strptime(existing_end, '%Y-%m-%d %H:%M')
                        if start_dt < ee and end_dt > es:
                            return "Slot already booked. <a href='/book'>Try another slot</a>"

        # Save booking temporarily in session
        session['vehicle'] = vehicle
        session['slot'] = slot
        session['start'] = start
        session['end'] = end
        return redirect('/payment')

    return render_template('book.html', total_slots=total_slots)

# PAYMENT PAGE
@app.route('/payment', methods=['GET', 'POST'])
def payment():
    if 'email' not in session or 'vehicle' not in session:
        return redirect('/signin')

    try:
        vehicle = session['vehicle']
        slot = session['slot']
        start = session['start']
        end = session['end']
        email = session['email']

        start_dt = datetime.datetime.strptime(start, '%Y-%m-%dT%H:%M')
        end_dt = datetime.datetime.strptime(end, '%Y-%m-%dT%H:%M')
        hours = max(1, int((end_dt - start_dt).total_seconds() // 3600))
        amount = hours * 500

        if request.method == 'POST':
            with open('bookings.txt', 'a') as f:
                f.write(f"{vehicle},{slot},{start_dt.strftime('%Y-%m-%d %H:%M')},{end_dt.strftime('%Y-%m-%d %H:%M')}\n")
            with open('payments.txt', 'a') as p:
                p.write(f"{vehicle},{amount},{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')},{email}\n")

            for key in ['vehicle', 'slot', 'start', 'end']:
                session.pop(key, None)

            return "<h2>✅ Payment Successful!</h2><a href='/book'>Book Another</a>"

        return render_template('payment.html',
                               vehicle=vehicle,
                               slot=slot,
                               start=start_dt.strftime('%Y-%m-%d %H:%M'),
                               end=end_dt.strftime('%Y-%m-%d %H:%M'),
                               hours=hours,
                               amount=amount)
    except Exception as e:
        return f"<h3>Error: {e}</h3><a href='/book'>Back</a>"

# ADMIN DASHBOARD
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'email' not in session or session['email'] != 'owner@gmail.com':
        return redirect('/signin')

    total_slots = get_total_slots()

    if request.method == 'POST':
        try:
            new_slots = int(request.form['total_slots'])
            with open(SLOT_FILE, 'w') as f:
                f.write(str(new_slots))
            total_slots = new_slots
        except:
            pass

    bookings = []
    if os.path.exists('bookings.txt'):
        with open('bookings.txt', 'r') as f:
            bookings = [line.strip().split(',') for line in f if line.strip()]

    payments = []
    if os.path.exists('payments.txt'):
        with open('payments.txt', 'r') as f:
            payments = [line.strip().split(',') for line in f if line.strip()]

    total_revenue = sum(int(p[1]) for p in payments if len(p) >= 2)

    return render_template('admin.html', total_slots=total_slots,
                           bookings=bookings, payments=payments, total_revenue=total_revenue)

# LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/signin')

if __name__ == '__main__':
    app.run(debug=True)