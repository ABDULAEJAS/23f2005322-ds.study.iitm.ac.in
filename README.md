A2 PARKING SERVICE – Parking Lot Management Website

This is a basic web application developed as part of the Application Development I project for the IITM BS Degree Program. It allows users to register, log in, book parking slots, and enables an admin to manage bookings and view payment details.

=====================
FEATURES
=====================
- User Signup & Login
- Admin Login (owner@gmail.com)
- Book Parking Slots (with date and time input)
- Prevents Double Booking of the Same Slot
- Payment Summary (₹500/hour)
- Admin Dashboard:
    * View Bookings
    * Manage Total Available Slots
    * View Revenue
- Supports Multiple Cities (basic dropdown)
- Session-based login/logout

=====================
TECHNOLOGIES USED
=====================
- Frontend: HTML, CSS
- Backend: Python (Flask)
- Data Storage: Plain Text Files
    * users.txt
    * bookings.txt
    * payments.txt
    * slots.txt

=====================
HOW TO RUN
=====================
1. Download or clone the project folder
2. Open terminal/command prompt in the project directory
3. Install Flask (if not already):
   pip install flask
4. Run the app:
   python app.py
5. Open your browser and go to:
   http://127.0.0.1:5000

=====================
ADMIN CREDENTIALS
=====================
- Email: owner@gmail.com
- Password: You will set during signup

=====================
FOLDER STRUCTURE
=====================
parking-lot-project/
│
├── app.py
├── users.txt
├── bookings.txt
├── payments.txt
├── slots.txt
│
├── templates/
│   ├── signin.html
│   ├── signup.html
│   ├── book.html
│   ├── admin.html
│   └── check.html
│
├── static/
    ├── style.css
    └── images/

=====================
NOTES
=====================
- This project avoids advanced tools like Bootstrap, Jinja templates, or databases to remain beginner-friendly.
- Admin is identified by the email "owner@gmail.com"
- Ideal for educational/demo purposes only.

=====================
DEVELOPER
=====================
Name: Abdul Aejas
Course: IITM BS - Application Development I
GitHub: https://github.com/YourUsername
