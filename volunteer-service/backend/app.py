from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import os
import requests

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "../frontend")

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
CORS(app)

DATABASE = os.path.join(
    os.path.dirname(__file__),
    "../database/volunteer.db"
)

COMPLAINT_SERVICE_URL = "http://localhost:5002"

def get_db():
    return sqlite3.connect(DATABASE)

def initialize_database():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS volunteers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            skill TEXT NOT NULL
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS signups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            volunteer_id INTEGER NOT NULL,
            complaint_id INTEGER NOT NULL,
            complaint_description TEXT NOT NULL
        )
    """)
    db.commit()
    db.close()

@app.route("/")
def home():
    return send_from_directory(FRONTEND_DIR, "index.html")

# ---------- Volunteer registration ----------

@app.route("/volunteers", methods=["POST"])
def create_volunteer():
    data = request.json
    name = data["name"]
    phone = data["phone"]
    skill = data["skill"]

    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO volunteers (name, phone, skill)
        VALUES (?, ?, ?)
    """, (name, phone, skill))
    db.commit()
    volunteer_id = cursor.lastrowid
    db.close()

    return jsonify({
        "volunteer_id": volunteer_id,
        "name": name,
        "phone": phone,
        "skill": skill
    }), 201

@app.route("/volunteers/<int:volunteer_id>", methods=["GET"])
def get_volunteer(volunteer_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT id, name, phone, skill
        FROM volunteers
        WHERE id = ?
    """, (volunteer_id,))
    volunteer = cursor.fetchone()
    db.close()

    if volunteer is None:
        return jsonify({"error": "Volunteer not found"}), 404

    return jsonify({
        "volunteer_id": volunteer[0],
        "name": volunteer[1],
        "phone": volunteer[2],
        "skill": volunteer[3]
    })

# ---------- Signups (the REST link to Complaint Service) ----------

@app.route("/signups", methods=["POST"])
def create_signup():
    data = request.json
    volunteer_id = data["volunteer_id"]
    complaint_id = data["complaint_id"]

    # Verify the complaint exists — blocking call, same pattern as Part C
    try:
        response = requests.get(
            f"{COMPLAINT_SERVICE_URL}/complaints/{complaint_id}",
            timeout=3
        )
    except requests.exceptions.RequestException:
        return jsonify({
            "error": "Complaint Service is unavailable"
        }), 503

    if response.status_code == 404:
        return jsonify({
            "error": "Complaint does not exist"
        }), 400

    if response.status_code != 200:
        return jsonify({
            "error": "Unable to verify complaint"
        }), 500

    complaint = response.json()

    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO signups (volunteer_id, complaint_id, complaint_description)
        VALUES (?, ?, ?)
    """, (volunteer_id, complaint_id, complaint["description"]))
    db.commit()
    signup_id = cursor.lastrowid
    db.close()

    return jsonify({
        "signup_id": signup_id,
        "volunteer_id": volunteer_id,
        "complaint_id": complaint_id,
        "complaint_description": complaint["description"],
        "complaint_location": complaint["location"]
    }), 201

@app.route("/signups/complaint/<int:complaint_id>", methods=["GET"])
def get_signups_for_complaint(complaint_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT s.id, s.volunteer_id, v.name, v.phone, s.complaint_id
        FROM signups s
        JOIN volunteers v ON v.id = s.volunteer_id
        WHERE s.complaint_id = ?
    """, (complaint_id,))
    rows = cursor.fetchall()
    db.close()

    signups = [
        {
            "signup_id": row[0],
            "volunteer_id": row[1],
            "volunteer_name": row[2],
            "volunteer_phone": row[3],
            "complaint_id": row[4]
        }
        for row in rows
    ]
    return jsonify(signups)

if __name__ == "__main__":
    initialize_database()
    app.run(port=5005, debug=True)
