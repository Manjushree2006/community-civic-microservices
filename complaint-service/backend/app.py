from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os
import requests

app = Flask(__name__)
CORS(app)

DATABASE = os.path.join(
    os.path.dirname(__file__),
    "../database/complaint.db"
)

CITIZEN_SERVICE_URL = "http://localhost:5001"

# Load-balancing support: which port this particular instance listens on.
# Run two copies of this exact same file on different ports, e.g.:
#   set PORT=5002 && python app.py   (instance #1)
#   set PORT=5006 && python app.py   (instance #2)
# Both instances share the same complaint.db, so either one can serve any request.
PORT = int(os.environ.get("PORT", 5002))

def get_db():
    return sqlite3.connect(DATABASE)

def initialize_database():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            citizen_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            location TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)
    db.commit()
    db.close()

@app.route("/complaints", methods=["POST"])
def create_complaint():
    data = request.json
    citizen_id = data["citizen_id"]
    description = data["description"]
    location = data["location"]

    # Ask Citizen Service to verify the citizen
    try:
        response = requests.get(
            f"{CITIZEN_SERVICE_URL}/citizens/{citizen_id}",
            timeout=3
        )
    except requests.exceptions.RequestException:
        return jsonify({
            "error": "Citizen Service is unavailable"
        }), 503

    if response.status_code == 404:
        return jsonify({
            "error": "Citizen does not exist"
        }), 400

    if response.status_code != 200:
        return jsonify({
            "error": "Unable to verify citizen"
        }), 500

    citizen = response.json()

    status = "OPEN"
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO complaints
        (citizen_id, description, location, status)
        VALUES (?, ?, ?, ?)
    """, (citizen_id, description, location, status))
    db.commit()
    complaint_id = cursor.lastrowid
    db.close()

    # Print which instance handled this — lets you visually confirm load balancing
    print(f"[Complaint instance on port {PORT}] created complaint #{complaint_id}")

    return jsonify({
        "complaint_id": complaint_id,
        "citizen_id": citizen_id,
        "citizen_name": citizen["name"],
        "description": description,
        "location": location,
        "status": status,
        "handled_by_port": PORT
    }), 201

@app.route("/complaints/<int:complaint_id>", methods=["GET"])
def get_complaint(complaint_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT id, citizen_id, description, location, status
        FROM complaints
        WHERE id = ?
    """, (complaint_id,))
    complaint = cursor.fetchone()
    db.close()

    if complaint is None:
        return jsonify({"error": "Complaint not found"}), 404

    print(f"[Complaint instance on port {PORT}] served GET for complaint #{complaint_id}")

    return jsonify({
        "complaint_id": complaint[0],
        "citizen_id": complaint[1],
        "description": complaint[2],
        "location": complaint[3],
        "status": complaint[4],
        "handled_by_port": PORT
    })

if __name__ == "__main__":
    initialize_database()
    app.run(port=PORT, debug=True, use_reloader=False)
