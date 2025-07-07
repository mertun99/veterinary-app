from functions import *

#FLASK
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session

#PASSWORD HASHING
from werkzeug.security import check_password_hash, generate_password_hash

#SQL
from cs50 import SQL

#SQL CONFIG
db = SQL("sqlite:///vet_clinic.db")

#FLASK CONFIG
app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

def check_if_logged_in():
    global user
    user = session.get("user_id")
    #print(user)


@app.route('/')
def index():
    check_if_logged_in()
    return render_template("index.html", user=user)

@app.route('/services')
def services():
    check_if_logged_in()
    return render_template("services.html", user=user)

@app.route('/pricing')
def pricing():
    check_if_logged_in()
    return render_template("pricing.html", user=user)

@app.route('/appointments',  methods=["GET", "POST"])
def appointments():
    check_if_logged_in()
    if request.method == "GET":
        time = get_time()
        today = time["today"]
        tomorrow = time["tomorrow"]
        taken = db.execute("SELECT id, name, email, option, strftime('%d. %m. %Y', date) AS formatted_date, hour, status FROM appointments WHERE status = 'accepted' AND date >= (?) ORDER BY date, hour ASC;", today)
        return render_template("appointments.html", min = tomorrow, max = time["max"], taken=taken, user=user)

    elif request.method == "POST":
        usr_name = request.form.get("name")
        usr_email = request.form.get("email")
        usr_option = request.form.get("option")
        usr_date = request.form.get("date")
        usr_hour = request.form.get("hour")
        #print(usr_name,usr_email, usr_option, usr_dateusr_, hour)


        time = get_time()
        if time["today"] == usr_date:
            #Reservation for the same day --> should select another day
            return apology("Please select another day", user)
            #TODO: Implement FULL server-side validation for real world use
        if db.execute("SELECT id FROM appointments WHERE date = (?) and hour = (?) and status = (?);",usr_date,usr_hour,"accepted") != []:
            #Occupied date
            return apology("This date and time is taken already! Please select another one.", user)
        else:
            db.execute("INSERT INTO appointments (name, email, option, date,hour,status) VALUES (?,?,?,?,?,?);",usr_name, usr_email, usr_option, usr_date, usr_hour, "pending")
            return render_template("message.html", user=user)




# DROPDOWN ROUTES:

@app.route('/contact')
def contact():
    check_if_logged_in()
    return render_template("contact.html", user=user)

@app.route('/map')
def map():
    check_if_logged_in()
    return render_template("map.html", user=user)


@app.route('/logout')
def logout():
    session.clear()
    return redirect("/")

#END OF DROPDOWN ROUTES:



@app.route('/admin', methods=["GET", "POST"])
def admin():
    check_if_logged_in()
    if request.method == "GET":
        return render_template("admin.html", user=user)

    elif request.method == "POST":
        login = request.form.get("admin_username")
        password = request.form.get("password")

        hashed_password = db.execute("SELECT hash FROM admins WHERE login = ?;", login)
        if hashed_password != []:
            hashed_password = hashed_password[0]["hash"]
        else:
            return apology("Invalid username!", user)


        if check_password_hash(hashed_password,password) == True:

            # Remembering session ID
            data = db.execute("SELECT * FROM admins WHERE login = ?", login)
            if len(data) != 1:
                return apology("Something indeed went wrong!",user)
            elif data == []:
                return apology("Something indeed went wrong!",user)
            else:
                session["user_id"] = data[0]["admin_id"]
                print(session["user_id"])
            return redirect("/console")
            print("SUCCESS")
        else:
            return apology("Invalid password!",user)




@app.route('/console', methods=["GET", "POST"])
@login_required
def console():
    check_if_logged_in()
    if request.method == "GET":
        pending = db.execute("SELECT id, name, email, option, strftime('%d. %m. %Y', date) AS formatted_date, hour, status FROM appointments WHERE status = 'pending' ORDER BY date, hour ASC;")
        accepted = db.execute("SELECT id, name, email, option, strftime('%d. %m. %Y', date) AS formatted_date, hour, status FROM appointments WHERE status = 'accepted' ORDER BY date, hour ASC;")
        rejected = db.execute("SELECT id, name, email, option, strftime('%d. %m. %Y', date) AS formatted_date, hour, status FROM appointments WHERE status = 'rejected' ORDER BY date, hour ASC;")
        return render_template("console.html", pending=pending, accepted=accepted, rejected=rejected, user=user)

        return render_template("console.html", pending=pending, accepted=accepted, rejected=rejected, user=user)

    elif request.method == "POST":
        appointment_id = request.form.get('accept') or request.form.get('reject') #ChatGPT
        action = 'Accepted' if 'accept' in request.form else 'Rejected'

        if action == 'Accepted':
            db.execute("UPDATE appointments SET status = 'accepted' WHERE id = (?);", appointment_id)

            # SENDS MAIL (NOT REALLY)
            email=(db.execute("SELECT email FROM appointments WHERE id = (?);", appointment_id))
            date = (db.execute("SELECT date FROM appointments WHERE id = (?);", appointment_id))
            send_mail("Your request status has changed to ACCEPTED! We will be expecting you :)", email[0], date[0])


        elif action == 'Rejected':
            db.execute("UPDATE appointments SET status = 'rejected' WHERE id = (?);", appointment_id)

            #SENDS MAIL (NOT REALLY)
            email = (db.execute("SELECT email FROM appointments WHERE id = (?);", appointment_id))
            date = (db.execute("SELECT date FROM appointments WHERE id = (?);", appointment_id))
            send_mail("Your request status has changed to REJECTED! We are sorry :( Maybe try asking for other time?", email[0], date[0])

        #print(f"Appointment ID: {appointment_id}, Action: {action}")
        return redirect('/console')



@app.route('/clear')
@login_required
def clear():
    time = get_time()
    today = time["today"]
    db.execute("DELETE FROM appointments WHERE date < ?;",today)
    db.execute("DELETE FROM appointments WHERE status = ?;", "rejected")
    return redirect("/console")



@app.route('/layout')
def layout():
    check_if_logged_in()
    return render_template("layout.html", user=user)


if __name__ == '__main__':
    app.run()
