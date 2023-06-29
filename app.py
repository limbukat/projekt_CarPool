from icalendar import Calendar, Event
from datetime import datetime, date
from flask import Flask, render_template, request, session, jsonify
import sqlite3
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import ssl

from markupsafe import Markup   # prevest html kod do template

app = Flask(__name__)
app.secret_key = 'super secret key'

# hlavni stranka, nacte template index.html
@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('index.html')

# vyber data z kalendare + vypis dostupnych aut
@app.route('/search', methods=['POST'])
def search():

    data = request.get_json() # data z fetch
    start_date = data['start_date']
    end_date = data['end_date']

    # Convert the dates to datetime objects
    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')

    if start_date_obj.date() < date.today(): # server side validation, pro jistotu, uz se checkovalo v javascript
        return render_template("error.html", error_message="Začátek nesmí být v minulosti.")
    if start_date_obj > end_date_obj:
        return render_template("error.html", error_message="Konec musí být ve stejný nebo pozdèjší den jako začátek.")

    # Format the dates as "dd.mm.yyyy"
    start_date = start_date_obj.strftime('%d.%m.%Y')
    end_date = end_date_obj.strftime('%d.%m.%Y')

    session["start_date"] = start_date
    session["end_date"] = end_date
    # Connect to the SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect('carpool.sqlite')
    conn.row_factory = sqlite3.Row
    # Create a cursor object
    c = conn.cursor() # ukazovatko v tabulce

    c.execute('''
        SELECT car_category.name, COUNT(DISTINCT car.id) as count 
        FROM car
        INNER JOIN car_category ON car.category = car_category.id
        WHERE car.id NOT IN (
            SELECT car
            FROM reservation
            WHERE NOT (reservation.end_date < ? OR reservation.start_date > ?)
        )
        GROUP BY car_category.id, car_category.name ORDER BY car_category.id
    ''', (data['start_date'], data['end_date']))

    # Fetch all rows from the last executed statement
    rows = c.fetchall()
    # convert list to dictonary aby to slo do jsonify
    car_categories = {row['name']: row['count'] for row in rows}
    conn.close()

    # Return a JSON response: convert a json (JavaScript Object Notation) output into a response object with application
    # conversion of multiple arguments to array or multiple arguments into dictionary
    return jsonify({
        'start_date': start_date,
        'end_date': end_date,
        'car_categories': car_categories
    })


@app.route('/reservation', methods=['POST'])
def reservation():
    car_category = request.form['car_category']
    session["car_category"] = car_category
    return render_template('reservation.html', data=session)


@app.route('/confirm_reservation', methods=['POST'])
def confirm_reservation():

    driver_name = request.form['driver_name']
    email = request.form['email']
    purpose = request.form['purpose']

    session["driver_name"] = driver_name
    session["email"] = email
    session["purpose"] = purpose

    return render_template('reservation_details.html', driver_name=driver_name, email=email,
                           purpose=purpose, car_category=session['car_category'],
                           start_date=session['start_date'], end_date=session['end_date'])


@app.route('/thank_you', methods=['POST'])
def thank_you():
    conn = sqlite3.connect('carpool.sqlite')
    conn.row_factory = sqlite3.Row
    # Create a cursor object
    c = conn.cursor()
    c.execute("SELECT id FROM car_category WHERE name = ?", (session["car_category"],)) # vybere se id kategorie auta
    row = c.fetchone() # ziska prvni radek

    if row:
        car_category_id = row[0] # ulozit id kategorie
    else:
        return render_template("error.html", error_message="Kategorie vozidla nebyla nalezena! :(((")

    # Convert start_date and end_date to the desired format (e.g., 'YYYY-MM-DD')
    start_date = datetime.strptime(session["start_date"], '%d.%m.%Y').strftime('%Y-%m-%d') # str premenit na str ve formatu pro sql
    end_date = datetime.strptime(session["end_date"], '%d.%m.%Y').strftime('%Y-%m-%d')
    c.execute(''' 
        SELECT car.id
            FROM car
            INNER JOIN car_category ON car.category = car_category.id
            WHERE car.id NOT IN (
                SELECT car
                FROM reservation
                WHERE NOT (reservation.end_date < ? OR reservation.start_date > ?)
            )
            AND car_category.id = ?
            LIMIT 1
    ''', (start_date, end_date, car_category_id)) # vybira prvni auto, ktere neni rezervovane
    row = c.fetchone()
    if row:
        car_id = row[0]  # vrati id auta, pokud neni rezervovane
    else:
        return render_template("error.html", error_message="Vozidla již nejsou dispozici! :(((")

    c.execute("INSERT INTO reservation (car, start_date, end_date, driver, purpose) VALUES (?, ?, ?, ?, ?)",
              (car_id, start_date, end_date, session["driver_name"], session["purpose"]))
    conn.commit()  # ulozi data do databaze

    c.execute("SELECT spz FROM car WHERE id = ?", (car_id,))
    row = c.fetchone()
    conn.close()

    if row:
        spz = row[0]  # vrati spz pokud se nejake auto najde
    else:
        return render_template("error.html", error_message="neco je hooodne spatne! :(((")
    conn.close()
    email = request.form['email']

    ics = generate_ics_file("Vypujčení vozidla " + spz + " ",
                            datetime.strptime(start_date+" 08:00:00", '%Y-%m-%d %H:%M:%S'),
                            datetime.strptime(end_date+" 18:00:00", '%Y-%m-%d %H:%M:%S'),
                            "Parkoviště u OBI",
                            "Podmínky: Auto je k dispozici od 8:00 první den rezervace na parkovišti před hlavní budovou.\n" +
                            "Vrácení auta je nutné provést nejpozději do 18:00 poslední den termínu rezervace zpět na parkoviště před hlavní budovou."
                            )

    email_send_message = send_calendar_email(email, "Rezervace vozidla",
                        render_template('confirmation_email.html', email=email, spz=spz), ics)

    return render_template('confirmation.html', email=email, spz=spz, email_send_message=email_send_message)


def generate_ics_file(summary, start_time, end_time, location, description):
    cal = Calendar()

    event = Event()
    event.add('summary', summary)
    event.add('dtstart', start_time)
    event.add('dtend', end_time)
    event.add('location', location)
    event.add('description', description)

    cal.add_component(event)

    return cal.to_ical()


def send_calendar_email(receiver_email, subject, html_content, ics):
    # SMTP server configuration
    smtp_server = 'smtp.seznam.cz'
    smtp_port = 465  # Replace with the appropriate SMTP port for your server
    # Create a multipart message and set the headers
    msg = MIMEMultipart('mixed')
    sender_email = "limbukat@seznam.cz"
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    # Attach the HTML content as alternative text
    part1 = MIMEText(html_content, 'html')
    msg.attach(part1)

    # Attach the calendar appointment file
    part2 = MIMEBase('text', 'calendar', method='REQUEST')
    part2.set_payload(ics)
    encoders.encode_base64(part2)
    part2.add_header('Content-Disposition', f'attachment; filename="rezervace.ics"')
    msg.attach(part2)

    context = ssl.create_default_context()

    try:
        # Create a secure SSL/TLS connection with the SMTP server
        server = smtplib.SMTP_SSL(smtp_server, smtp_port, context=context)
        server.ehlo()

        # Authenticate with your email address and password (if required)
        login = server.login(sender_email, '123456Kl')

        # Send the email
        server.send_message(msg)
        return "Na email "+receiver_email+" byly odeslány detaily rezervace."
    except Exception as e:
        return Markup("<p class='red-text'>Chyba při odeslání e-mailu na adresu "+receiver_email+":" + str(e)+"</p>")
    finally:
        # Close the connection to the SMTP server
        server.quit()


if __name__ == '__main__':
    app.run()
