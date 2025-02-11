from flask import Flask, request, jsonify, render_template
import json
import os
from datetime import datetime

app = Flask(__name__)

DATA_FILE = "data.json"
UNIT_PRICE = 8  # Updated unit price

# Load data from JSON
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"records": []}
    with open(DATA_FILE, "r") as file:
        return json.load(file)

# Save data to JSON
def save_data(data):
    with open(DATA_FILE, "w") as file:
        json.dump(data, file, indent=4)

@app.route("/")
def home():
    data = load_data()
    return render_template("index.html", data=data)

@app.route("/add_reading", methods=["POST"])
def add_reading():
    data = load_data()
    
    current_reading = request.json.get("current_reading")
    entry_date = request.json.get("date")  # Optional: For adding old entries

    if not isinstance(current_reading, (int, float)):
        return jsonify({"error": "Invalid reading"}), 400

    # Get last recorded reading
    last_entry = data["records"][0] if data["records"] else None  # Newest first
    last_reading = last_entry["reading"] if last_entry else 0

    # Calculate units consumed and bill
    units_used = max(current_reading - last_reading, 0)  # Prevent negative values
    bill_amount = units_used * UNIT_PRICE

    # Save new entry (at the start of the list)
    entry = {
        "timestamp": datetime.now().isoformat() if not entry_date else entry_date,
        "date": datetime.now().strftime("%Y-%m") if not entry_date else entry_date,
        "reading": current_reading,
        "units_used": units_used,
        "bill": bill_amount
    }
    
    data["records"].insert(0, entry)  # Newest first
    save_data(data)

    return jsonify({
        "message": "Reading added",
        "entry": entry,
        "units_used": units_used,
        "bill_amount": bill_amount
    })

@app.route("/add_old_reading", methods=["POST"])
def add_old_reading():
    data = load_data()
    
    current_reading = request.json.get("current_reading")
    entry_date = request.json.get("date")  # Date for the old entry

    if not isinstance(current_reading, (int, float)):
        return jsonify({"error": "Invalid reading"}), 400

    # Get last recorded reading before the old entry's date
    last_entry = None
    for record in data["records"]:
        if record["date"] < entry_date:
            last_entry = record
            break

    last_reading = last_entry["reading"] if last_entry else 0

    # Calculate units consumed and bill
    units_used = max(current_reading - last_reading, 0)  # Prevent negative values
    bill_amount = units_used * UNIT_PRICE

    # Save old entry (inserted in the correct position based on date)
    entry = {
        "timestamp": entry_date + "T12:00:00",  # Placeholder timestamp for old entries
        "date": entry_date,
        "reading": current_reading,
        "units_used": units_used,
        "bill": bill_amount
    }

    # Insert the old entry in the correct position (sorted by date)
    inserted = False
    for i, record in enumerate(data["records"]):
        if record["date"] < entry_date:
            data["records"].insert(i, entry)
            inserted = True
            break

    if not inserted:
        data["records"].append(entry)  # Add to the end if no older records exist

    save_data(data)

    return jsonify({
        "message": "Old reading added",
        "entry": entry,
        "units_used": units_used,
        "bill_amount": bill_amount
    })

@app.route("/get_data", methods=["GET"])
def get_data():
    return jsonify(load_data())

if __name__ == "__main__":
    app.run(debug=True)