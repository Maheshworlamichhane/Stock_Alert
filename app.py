from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from bs4 import BeautifulSoup
import requests
import smtplib
import schedule
import time

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///stockalert.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.app_context().push()


class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    email = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.Integer, nullable=False)
    alert_time = db.Column(db.Integer, nullable=False)
    alert_type = db.Column(db.String(50))

    def __repr__(self):
        return f"Alert('{self.symbol}', '{self.price}', '{self.email}', '{self.phone}', '{self.alert_time}', '{self.alert_type}')"

# Function to retrieve stock data from Yahoo Finance API
def get_stock_data(ticker):
    url = f'https://finance.yahoo.com/quote/{ticker}/history?p={ticker}'
    # Send GET request to API and retrieve latest stock data
    response = requests.get(url)
    # Extract relevant data from response
    soup = BeautifulSoup(response.content, 'html.parser')
    price = soup.find('span', {'data-reactid': '50'}).get_text().replace(',', '')
    date = soup.find('span', {'data-reactid': '53'}).get_text()
    # Return stock data as a dictionary
    return {
        'ticker': ticker,
        'price': float(price),
        'date': date
    }


# Function to check stock price against user's threshold and send notification if necessary
def check_stock_price(ticker, threshold, notification_type):
    stock_data = get_stock_data(ticker)
    # Check if stock price exceeds threshold
    if stock_data['price'] >= threshold:
        # Send notification
        send_notification(ticker, stock_data['price'], notification_type)

# Function to send notification to user
def send_notification(ticker, price, notification_type):
    # Create message based on notification type
    if notification_type == 'email':
        message = f'Stock {ticker} has reached your threshold price of {price}.'
        # Use smtplib to send email notification
        try:
            # Example using Gmail SMTP server
            with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
                smtp.ehlo()
                smtp.starttls()
                smtp.ehlo()

                # Replace with your email and password
                smtp.login('maheshworlamichhane777@gmail.com', 'mrxdevmowjsoammq')

                # Replace with recipient email
                subject = f'Stock {ticker} Alert'
                body = message
                msg = f'Subject: {subject}\n\n{body}'
                smtp.sendmail('maheshworlamichhane777@gmail.com', 'mahe@gmail.com', msg)
        except Exception as e:
            print(f'Error sending email notification: {e}')
    elif notification_type == 'sms':
        message = f'Stock {ticker} has reached your threshold price of {price}.'
        # Use third-party SMS service to send text message notification
        # ...

# Route for user input form
@app.route('/')
def index():
    return render_template('index.html')


# Route to handle form submission
@app.route('/', methods=['POST'])
def submit():
    # Retrieve user input from form
    ticker = request.form['ticker']
    threshold = float(request.form['threshold'])
    email = request.form['email']
    phone = request.form['phone']
    frequency = int(request.form['frequency'])
    notification_type = request.form['notification_type']

    # Save alert data to database
    new_alert = Alert(symbol=ticker, price=threshold,email = email, phone= phone, alert_time=frequency, alert_type=notification_type)
    db.session.add(new_alert)
    db.session.commit()

    # Schedule recurring task to check stock price at user-specified frequency
    schedule.every(frequency).hours.do(check_stock_price, ticker, threshold, notification_type)

    # Redirect user to success page
    return render_template('submit.html', alert = new_alert)

@app.route('/run_scheduled_tasks', methods=['POST'])
def run_scheduled_tasks():
    data = Alert.query.all()
    for i in data:
        ticker = i.symbol
        threshold = i.price
        notification_type = i.alert_type
        schedule.every(i.alert_time).hours.do(
            check_stock_price, ticker, threshold, notification_type)
    while True:
        schedule.run_pending()
        time.sleep(1)
    # return "Scheduled tasks are running"

if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)

