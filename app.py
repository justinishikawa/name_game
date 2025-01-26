from flask import Flask, render_template, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os
import re
import logging

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
# Database connection details
DATABASE_URI = os.getenv("DATABASE_URI")

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URI, cursor_factory=RealDictCursor)
    return conn

def initialize_database():
    logging.info("Initializing database...")
    conn = None
    try:
        conn = get_db_connection()
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
        logging.info("Database initialized successfully.")
    except Exception as e:
        logging.error(f"Error initializing database: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

app = Flask(__name__)
initialize_database()  # Call the function here

# List of names
names = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry"]

# Dictionary to store selected names and associated emails
selected_names = {}

# Dictionary to store emails and their purchased names
email_purchases = {}

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

    # Validate email format
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return jsonify({"error": "Invalid email format"}), 400

    # Validate first and last name (only allow letters and spaces)
    if not re.match(r"^[a-zA-Z\s]+$", first_name):
        return jsonify({"error": "Invalid first name format"}), 400
    if not re.match(r"^[a-zA-Z\s]+$", last_name):
        return jsonify({"error": "Invalid last name format"}), 400

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
    if payment_method not in ["venmo", "cashapp", "zelle", "paypal"]:
        return jsonify({"error": "Invalid payment method"}), 400

    # Fetch first name and last name from the database
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT first_name, last_name FROM selected_names WHERE name = %s AND email = %s",
                (name, email)
            )
            result = cur.fetchone()
            if result:
                first_name = result['first_name']
                last_name = result['last_name']
            else:
                return jsonify({"error": "Name and email not found in database"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

    # Generate a simple key pair (in a real app, use proper encryption)
    key_pair = f"{email}:{name}"

    return jsonify({"message": f"{first_name} {last_name} ({email}) reserved {name}", "key_pair": key_pair})

if __name__ == '__main__':
    app.run(debug=True)
