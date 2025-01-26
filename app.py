from flask import Flask, render_template, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# List of names
names = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry"]

# Dictionary to store selected names and associated emails
selected_names = {}

# Dictionary to store emails and their purchased names
email_purchases = {}

# Database connection details
DATABASE_URI = os.getenv("DATABASE_URI")

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URI, cursor_factory=RealDictCursor)
    return conn

def initialize_database():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                DROP TABLE IF EXISTS selected_names;
                CREATE TABLE selected_names (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) NOT NULL,
                    first_name VARCHAR(255) NOT NULL,
                    last_name VARCHAR(255) NOT NULL,
                    payment_method VARCHAR(50) NOT NULL
                );
            """)
        conn.commit()
    except Exception as e:
        print(f"Error initializing database: {e}")
    finally:
        conn.close()

@app.route('/')
def index():
    available_names = [name for name in names if name not in selected_names]
    return render_template('index.html', names=available_names)

@app.route('/select_name', methods=['POST'])
def select_name():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    payment_method = data.get('payment_method')

    if name in selected_names:
        return jsonify({"error": "Name already selected"}), 400

    if name not in names:
        return jsonify({"error": "Invalid name"}), 400

    if payment_method not in ["venmo", "cashapp", "zelle", "paypal"]:
        return jsonify({"error": "Invalid payment method"}), 400

    # Associate the name with the email
    selected_names[name] = email

    # Add the name to the email's purchases
    if email in email_purchases:
        email_purchases[email].append(name)
    else:
        email_purchases[email] = [name]

    # Remove the name from the list
    names.remove(name)

    # Insert the selected name and email into the database
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO selected_names (name, email, first_name, last_name, payment_method) VALUES (%s, %s, %s, %s, %s)",
                (name, email, first_name, last_name, payment_method)
            )
        conn.commit()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

    return jsonify({"message": "Name selected successfully"})

@app.route('/available_names', methods=['GET'])
def available_names():
    available_names = [name for name in names if name not in selected_names]
    return jsonify({"names": available_names})

@app.route('/payment', methods=['POST'])
def payment():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    payment_method = data.get('payment_method')

    if name not in selected_names or selected_names[name] != email:
        return jsonify({"error": "Invalid selection or email"}), 400

    if payment_method not in ["venmo", "cashapp"]:
        return jsonify({"error": "Invalid payment method"}), 400

    # Generate a simple key pair (in a real app, use proper encryption)
    key_pair = f"{email}:{name}"

    return jsonify({"message": "Payment successful", "key_pair": key_pair})

if __name__ == '__main__':
    initialize_database()
    app.run(debug=True)