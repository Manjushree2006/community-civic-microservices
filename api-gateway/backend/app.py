from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import os
from itertools import cycle

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "../frontend")

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
CORS(app)

# ---------- Service registry ----------
# Each service can have ONE or MULTIPLE instances. Complaint Service has two,
# to demonstrate load balancing. Add more URLs to any list to scale that service.
SERVICE_INSTANCES = {
    "citizens":   ["http://localhost:5001"],
    "complaints": ["http://localhost:5002", "http://localhost:5006"],
    "volunteers": ["http://localhost:5005"],
    "signups":    ["http://localhost:5005"],
    "scores":     ["http://localhost:5002", "http://localhost:5006"],
}

# A round-robin cursor per service, so consecutive requests rotate through instances
_cycles = {name: cycle(urls) for name, urls in SERVICE_INSTANCES.items()}

def next_instance(service):
    return next(_cycles[service])

# ---------- Reverse proxy with load balancing + failover ----------

@app.route("/api/<service>", methods=["GET", "POST"], defaults={"subpath": ""})
@app.route("/api/<service>/<path:subpath>", methods=["GET", "POST"])
def gateway(service, subpath):
    if service not in SERVICE_INSTANCES:
        return jsonify({"error": f"Unknown service '{service}'"}), 404

    instances = SERVICE_INSTANCES[service]
    attempts = 0
    last_error = None

    # Try up to len(instances) times, rotating to the next instance on failure.
    # This gives both load balancing (normal case) and failover (if one instance is down).
    while attempts < len(instances):
        base_url = next_instance(service)
        target_url = f"{base_url}/{service}"
        if subpath:
            target_url += f"/{subpath}"

        try:
            if request.method == "GET":
                resp = requests.get(target_url, timeout=3)
            else:
                resp = requests.post(target_url, json=request.get_json(silent=True), timeout=3)

            print(f"[Gateway] {request.method} /api/{service}/{subpath} -> {base_url}  (attempt {attempts + 1})")

            response_headers = {"Content-Type": "application/json", "X-Upstream": base_url}
            return (resp.content, resp.status_code, response_headers)

        except requests.exceptions.RequestException as e:
            print(f"[Gateway] {base_url} failed ({e}), trying next instance...")
            last_error = e
            attempts += 1
            continue

    # Every instance of this service failed
    return jsonify({"error": f"All instances of '{service}' are unavailable"}), 503

# ---------- Multipage frontend ----------

@app.route("/")
def home():
    return send_from_directory(FRONTEND_DIR, "home.html")

@app.route("/<page>.html")
def page(page):
    return send_from_directory(FRONTEND_DIR, f"{page}.html")

if __name__ == "__main__":
    app.run(port=5000, debug=True, use_reloader=False)
