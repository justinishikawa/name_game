from flask import Flask, render_template, request, jsonify
import os
import json

app = Flask(__name__)

# List of names
names = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry"]

# Dictionary to store selected names and associated emails
selected_names = {}

@app.route('/')
def index():
    return render_template('index.html', names=names)

@app.route('/select_name', methods=['POST'])
def select_name():
    data = request.json
    name = data.get('name')
    email = data.get('email')

    if name in selected_names:
        return jsonify({"error": "Name already selected"}), 400

    if name not in names:
        return jsonify({"error": "Invalid name"}), 400

    # Mark the name as selected
    selected_names[name] = email

    # Remove the name from the list
    names.remove(name)

    return jsonify({"message": "Name selected successfully"})

@app.route('/payment', methods=['POST'])
def payment():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    payment_method = data.get('payment_method')

    if name not in selected_names or selected_names[name] != email:
        return jsonify({"error": "Invalid selection or email"}), 400

    # Simulate payment processing
    if payment_method not in ["venmo", "cashapp"]:
        return jsonify({"error": "Invalid payment method"}), 400

    # Generate a simple key pair (in a real app, use proper encryption)
    key_pair = f"{email}:{name}"

    return jsonify({"message": "Payment successful", "key_pair": key_pair})

if __name__ == '__main__':
    app.run(debug=True)
