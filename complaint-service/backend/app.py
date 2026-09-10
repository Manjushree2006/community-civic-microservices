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
    db = sqlite3.connect(DATABASE)
    db.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            citizen_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            location TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS civic_scores (
            citizen_id INTEGER PRIMARY KEY,
            score INTEGER NOT NULL DEFAULT 0
        )
    """)
    db.commit()
    return db

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
    db.execute("""
        CREATE TABLE IF NOT EXISTS civic_scores (
            citizen_id INTEGER PRIMARY KEY,
            score INTEGER NOT NULL DEFAULT 0
        )
    """)
    db.commit()
    db.close()

@app.route("/")
def home():
    return send_from_directory(FRONTEND_DIR, "index.html")

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
    cursor.execute("""
        INSERT INTO civic_scores (citizen_id, score)
        VALUES (?, 10)
        ON CONFLICT(citizen_id) DO UPDATE SET score = score + 10
    """, (citizen_id,))
    db.commit()
    complaint_id = cursor.lastrowid
    score = cursor.execute(
        "SELECT score FROM civic_scores WHERE citizen_id = ?",
        (citizen_id,)
    ).fetchone()[0]
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
        "civic_score": score,
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

    if complaint is None:
        db.close()
        return jsonify({"error": "Complaint not found"}), 404

    score = cursor.execute(
        "SELECT score FROM civic_scores WHERE citizen_id = ?",
        (complaint[1],)
    ).fetchone()
    db.close()

    print(f"[Complaint instance on port {PORT}] served GET for complaint #{complaint_id}")

    return jsonify({
        "complaint_id": complaint[0],
        "citizen_id": complaint[1],
        "description": complaint[2],
        "location": complaint[3],
        "status": complaint[4],
        "civic_score": score[0] if score else 0,
        "handled_by_port": PORT
    })

@app.route("/scores/leaderboard", methods=["GET"])
def civic_score_leaderboard():
    db = get_db()
    rows = db.execute("""
        SELECT citizen_id, score
        FROM civic_scores
        ORDER BY score DESC, citizen_id ASC
    """).fetchall()
    db.close()

    leaderboard = []
    for index, row in enumerate(rows, start=1):
        try:
            citizen_response = requests.get(
                f"{CITIZEN_SERVICE_URL}/citizens/{row[0]}",
                timeout=3
            )
            citizen = citizen_response.json() if citizen_response.ok else {}
        except requests.exceptions.RequestException:
            citizen = {}
        leaderboard.append({
            "rank": index,
            "citizen_id": row[0],
            "name": citizen.get("name", "Citizen"),
            "ward": citizen.get("ward", "Unknown"),
            "civic_score": row[1]
        })

    return jsonify(leaderboard)

if __name__ == "__main__":
    initialize_database()
    app.run(port=PORT, debug=True, use_reloader=False)
