from flask import Flask, render_template, request, jsonify, make_response
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os
import re
import logging
import random
from datetime import datetime

load_dotenv()
logging.basicConfig(level=logging.INFO)
DATABASE_URI = os.getenv("DATABASE_URI")

def get_db_connection():
    return psycopg2.connect(DATABASE_URI, cursor_factory=RealDictCursor)

def initialize_database():
    logging.info("Initializing database...")
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS selected_names (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE,
                email VARCHAR(255) NOT NULL,
                first_name VARCHAR(255) NOT NULL,
                last_name VARCHAR(255) NOT NULL,
                payment_method VARCHAR(50) NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
initialize_database()

names = [
    'Richard', 'Bryan', 'Harold', 'Kai', 'Axel', 'Lucian', 'James', 'Alex',
    'Buddy', 'Keanu', 'Noah', 'Lorcan', 'John', 'Sebastian', 'Ash', 'Helios',
    'Justin_Jr', 'Sterling', 'Koloa', 'Victor', 'Bayes', 'Lucas', 'Andrew',
    'Adam', 'Anders', 'Dylan', 'Ian', 'Dante', 'Orion', 'Marlo'
]

@app.route('/')
def index():
    return render_template('index.html')

def get_available_names():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM selected_names")
            reserved_names = [row['name'] for row in cur.fetchall()]
    except Exception as e:
        logging.error(f"Error fetching reserved names: {e}")
        reserved_names = []
    finally:
        conn.close()
    available_names = [name for name in names if name not in reserved_names]
    return ['Random'] + sorted(available_names)

@app.route('/available_names', methods=['GET'])
def available_names():
    available = get_available_names()
    timestamp = datetime.now().isoformat()
    response = make_response(jsonify({"names": available, "timestamp": timestamp}))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/select_name', methods=['POST'])
def select_name():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    payment_method = data.get('payment_method')

    if not all([name, email, first_name, last_name, payment_method]):
        return jsonify({"error": "Missing required fields"}), 400
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return jsonify({"error": "Invalid email format"}), 400
    if not re.match(r"^[a-zA-Z\s]+$", first_name) or not re.match(r"^[a-zA-Z\s]+$", last_name):
        return jsonify({"error": "Invalid name format"}), 400
    if payment_method not in ["venmo", "cashapp", "zelle", "paypal"]:
        return jsonify({"error": "Invalid payment method"}), 400

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM selected_names WHERE name = %s", (name,))
            if cur.fetchone():
                return jsonify({"error": "Name already selected"}), 400
            cur.execute(
                "INSERT INTO selected_names (name, email, first_name, last_name, payment_method) VALUES (%s, %s, %s, %s, %s)",
                (name, email, first_name, last_name, payment_method)
            )
        conn.commit()
    except psycopg2.errors.UniqueViolation:
        return jsonify({"error": "Name already selected"}), 400
    except Exception as e:
        logging.error(f"Error selecting name: {e}")
        return jsonify({"error": "An error occurred while processing your request"}), 500
    finally:
        conn.close()
    return jsonify({"message": "Name selected successfully"})

@app.route('/random_name', methods=['GET'])
def random_name():
    available_names = get_available_names()[1:]  # Exclude 'Random'
    if not available_names:
        return jsonify({"error": "No names available"}), 400
    return jsonify({"name": random.choice(available_names)})

if __name__ == '__main__':
    app.run(debug=True)
