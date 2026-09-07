from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os

app = Flask(__name__)
CORS(app)

DATABASE = os.path.join(
    os.path.dirname(__file__),
    "../database/civicscore.db"
)

POINTS_PER_COMPLAINT = 10

def get_db():
    return sqlite3.connect(DATABASE)

def initialize_database():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            citizen_id INTEGER PRIMARY KEY,
            total_score INTEGER NOT NULL DEFAULT 0,
            complaints_filed INTEGER NOT NULL DEFAULT 0
        )
    """)
    db.commit()
    db.close()

@app.route("/score/award", methods=["POST"])
def award_points():
    data = request.json
    citizen_id = data["citizen_id"]
    points = data.get("points", POINTS_PER_COMPLAINT)

    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT total_score, complaints_filed FROM scores WHERE citizen_id = ?", (citizen_id,))
    row = cursor.fetchone()

    if row is None:
        cursor.execute("""
            INSERT INTO scores (citizen_id, total_score, complaints_filed)
            VALUES (?, ?, 1)
        """, (citizen_id, points))
        new_total = points
        new_count = 1
    else:
        new_total = row[0] + points
        new_count = row[1] + 1
        cursor.execute("""
            UPDATE scores
            SET total_score = ?, complaints_filed = ?
            WHERE citizen_id = ?
        """, (new_total, new_count, citizen_id))

    db.commit()
    db.close()

    return jsonify({
        "citizen_id": citizen_id,
        "points_awarded": points,
        "total_score": new_total,
        "complaints_filed": new_count
    }), 201

@app.route("/score/<int:citizen_id>", methods=["GET"])
def get_score(citizen_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT citizen_id, total_score, complaints_filed
        FROM scores
        WHERE citizen_id = ?
    """, (citizen_id,))
    row = cursor.fetchone()
    db.close()

    if row is None:
        return jsonify({
            "citizen_id": citizen_id,
            "total_score": 0,
            "complaints_filed": 0
        })

    return jsonify({
        "citizen_id": row[0],
        "total_score": row[1],
        "complaints_filed": row[2]
    })

@app.route("/leaderboard", methods=["GET"])
def get_leaderboard():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT citizen_id, total_score, complaints_filed
        FROM scores
        ORDER BY total_score DESC
        LIMIT 10
    """)
    rows = cursor.fetchall()
    db.close()

    leaderboard = [
        {
            "rank": index + 1,
            "citizen_id": row[0],
            "total_score": row[1],
            "complaints_filed": row[2]
        }
        for index, row in enumerate(rows)
    ]

    return jsonify(leaderboard)

if __name__ == "__main__":
    initialize_database()
    app.run(port=5004, debug=True)
