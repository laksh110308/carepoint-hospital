from flask import Flask, jsonify, request, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = "hospital_secret_2024"

app.config["SQLALCHEMY_DATABASE_URI"]        = "sqlite:///hospital.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "hospital123"

token_counter = {"value": 0}

def get_next_token():
    token_counter["value"] += 1
    return f"T-{token_counter['value']:03d}"

class Patient(db.Model):
    id             = db.Column(db.String(8),   primary_key=True)
    token          = db.Column(db.String(10),  nullable=False, default="T-000")
    name           = db.Column(db.String(100), nullable=False)
    age            = db.Column(db.Integer,      nullable=False)
    heart_rate     = db.Column(db.Integer,      nullable=False)
    blood_pressure = db.Column(db.String(20),  nullable=False)
    temperature    = db.Column(db.Float,        nullable=False)
    arrived_at     = db.Column(db.String(20),  nullable=False)
    status         = db.Column(db.String(20),  default="waiting")
    priority_score = db.Column(db.Integer,      default=0)
    priority_level = db.Column(db.String(20),  default="STABLE")
    room           = db.Column(db.String(10),  nullable=True)
    doctor         = db.Column(db.String(100), nullable=True)
    bed            = db.Column(db.String(20),  nullable=True)

    def to_dict(self):
        return {
            "id"             : self.id,
            "token"          : self.token,
            "name"           : self.name,
            "age"            : self.age,
            "heart_rate"     : self.heart_rate,
            "blood_pressure" : self.blood_pressure,
            "temperature"    : self.temperature,
            "arrived_at"     : self.arrived_at,
            "status"         : self.status,
            "priority_score" : self.priority_score,
            "priority_level" : self.priority_level,
            "room"           : self.room,
            "doctor"         : self.doctor,
            "bed"            : self.bed
        }

rooms = [
    {"room_number": "101", "status": "available", "patient_id": None},
    {"room_number": "102", "status": "available", "patient_id": None},
    {"room_number": "103", "status": "available", "patient_id": None},
    {"room_number": "104", "status": "available", "patient_id": None},
    {"room_number": "105", "status": "available", "patient_id": None},
]

doctors = [
    {"id": "D01", "name": "Dr. Arun Kumar",  "specialty": "Emergency",  "available": True, "patient_id": None},
    {"id": "D02", "name": "Dr. Meena Raj",   "specialty": "Cardiology", "available": True, "patient_id": None},
    {"id": "D03", "name": "Dr. Suresh Nair", "specialty": "General",    "available": True, "patient_id": None},
]

beds = [
    {"id": "ICU-1",  "type": "ICU",       "status": "available", "patient_id": None},
    {"id": "ICU-2",  "type": "ICU",       "status": "available", "patient_id": None},
    {"id": "ICU-3",  "type": "ICU",       "status": "available", "patient_id": None},
    {"id": "GEN-1",  "type": "General",   "status": "available", "patient_id": None},
    {"id": "GEN-2",  "type": "General",   "status": "available", "patient_id": None},
    {"id": "GEN-3",  "type": "General",   "status": "available", "patient_id": None},
    {"id": "GEN-4",  "type": "General",   "status": "available", "patient_id": None},
    {"id": "EMG-1",  "type": "Emergency", "status": "available", "patient_id": None},
    {"id": "EMG-2",  "type": "Emergency", "status": "available", "patient_id": None},
    {"id": "EMG-3",  "type": "Emergency", "status": "available", "patient_id": None},
]

def calculate_priority(age, heart_rate, temperature, blood_pressure):
    score = 0
    if heart_rate > 100 or heart_rate < 60:
        score += 30
    if temperature > 38.0:
        score += 20
    if age > 60:
        score += 20
    try:
        systolic = int(blood_pressure.split("/")[0])
        if systolic > 140:
            score += 30
    except:
        pass
    if score >= 60:
        level = "CRITICAL"
    elif score >= 30:
        level = "MODERATE"
    else:
        level = "STABLE"
    return score, level

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

with app.app_context():
    db.create_all()
    last = Patient.query.order_by(Patient.token.desc()).first()
    if last and last.token:
        try:
            token_counter["value"] = int(last.token.split("-")[1])
        except:
            pass

@app.route("/login", methods=["GET"])
def login():
    return render_template("login.html", error=None)

@app.route("/login", methods=["POST"])
def do_login():
    username = request.form.get("username")
    password = request.form.get("password")
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session["logged_in"] = True
        return redirect(url_for("index"))
    return render_template("login.html", error="Wrong username or password!")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/api/patients", methods=["POST"])
@login_required
def add_patient():
    data = request.get_json()
    required = ["name", "age", "heart_rate", "blood_pressure", "temperature"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400
    score, level = calculate_priority(
        data["age"], data["heart_rate"],
        data["temperature"], data["blood_pressure"]
    )
    patient = Patient(
        id             = str(uuid.uuid4())[:8],
        token          = get_next_token(),
        name           = data["name"],
        age            = data["age"],
        heart_rate     = data["heart_rate"],
        blood_pressure = data["blood_pressure"],
        temperature    = data["temperature"],
        arrived_at     = datetime.now().strftime("%H:%M:%S"),
        status         = "waiting",
        priority_score = score,
        priority_level = level,
        room           = None,
        doctor         = None,
        bed            = None
    )
    db.session.add(patient)
    db.session.commit()
    return jsonify({"message": "✅ Patient added!", "patient": patient.to_dict()}), 201

@app.route("/api/patients", methods=["GET"])
@login_required
def get_patients():
    all_patients = Patient.query.order_by(Patient.priority_score.desc()).all()
    return jsonify({
        "total"    : len(all_patients),
        "patients" : [p.to_dict() for p in all_patients]
    })

@app.route("/api/patients/<patient_id>", methods=["DELETE"])
@login_required
def delete_patient(patient_id):
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({"error": "Patient not found"}), 404
    for room in rooms:
        if room["patient_id"] == patient_id:
            room["status"]     = "available"
            room["patient_id"] = None
    for doc in doctors:
        if doc["patient_id"] == patient_id:
            doc["available"]   = True
            doc["patient_id"]  = None
    for bed in beds:
        if bed["patient_id"] == patient_id:
            bed["status"]      = "available"
            bed["patient_id"]  = None
    db.session.delete(patient)
    db.session.commit()
    return jsonify({"message": "🗑️ Patient removed!"}), 200

@app.route("/api/patients/<patient_id>/status", methods=["PATCH"])
@login_required
def update_status(patient_id):
    data    = request.get_json()
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({"error": "Patient not found"}), 404
    valid = ["waiting", "in-treatment", "discharged"]
    if data["status"] not in valid:
        return jsonify({"error": "Invalid status"}), 400
    patient.status = data["status"]
    db.session.commit()
    return jsonify({"message": "✅ Updated!", "patient": patient.to_dict()}), 200

@app.route("/api/stats", methods=["GET"])
@login_required
def get_stats():
    all_p = Patient.query.all()
    return jsonify({
        "total"        : len(all_p),
        "critical"     : sum(1 for p in all_p if "CRITICAL" in p.priority_level),
        "moderate"     : sum(1 for p in all_p if "MODERATE" in p.priority_level),
        "stable"       : sum(1 for p in all_p if "STABLE"   in p.priority_level),
        "waiting"      : sum(1 for p in all_p if p.status == "waiting"),
        "in_treatment" : sum(1 for p in all_p if p.status == "in-treatment"),
        "discharged"   : sum(1 for p in all_p if p.status == "discharged"),
    })

@app.route("/api/rooms", methods=["GET"])
@login_required
def get_rooms():
    return jsonify({"rooms": rooms})

@app.route("/api/rooms/assign/<patient_id>", methods=["POST"])
@login_required
def assign_room(patient_id):
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({"error": "Patient not found"}), 404
    if patient.room:
        return jsonify({"error": f"Already in Room {patient.room}"}), 400
    room = next((r for r in rooms if r["status"] == "available"), None)
    if not room:
        return jsonify({"error": "No rooms available"}), 400
    room["status"]     = "occupied"
    room["patient_id"] = patient_id
    patient.room       = room["room_number"]
    db.session.commit()
    return jsonify({"message": f"✅ Room {room['room_number']} assigned!"}), 200

@app.route("/api/rooms/release/<patient_id>", methods=["POST"])
@login_required
def release_room(patient_id):
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({"error": "Patient not found"}), 404
    for room in rooms:
        if room["patient_id"] == patient_id:
            room["status"]     = "available"
            room["patient_id"] = None
            patient.room       = None
            db.session.commit()
            return jsonify({"message": f"✅ Room {room['room_number']} is free!"}), 200
    return jsonify({"error": "No room assigned"}), 400

@app.route("/api/doctors", methods=["GET"])
@login_required
def get_doctors():
    return jsonify({"doctors": doctors})

@app.route("/api/doctors/assign/<patient_id>", methods=["POST"])
@login_required
def assign_doctor(patient_id):
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({"error": "Patient not found"}), 404
    if patient.doctor:
        return jsonify({"error": f"Already assigned: {patient.doctor}"}), 400
    doctor = next((d for d in doctors if d["available"]), None)
    if not doctor:
        return jsonify({"error": "No doctors available"}), 400
    doctor["available"]  = False
    doctor["patient_id"] = patient_id
    patient.doctor       = doctor["name"]
    db.session.commit()
    return jsonify({"message": f"✅ {doctor['name']} assigned!"}), 200

@app.route("/api/doctors/release/<patient_id>", methods=["POST"])
@login_required
def release_doctor(patient_id):
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({"error": "Patient not found"}), 404
    for doc in doctors:
        if doc["patient_id"] == patient_id:
            doc["available"]  = True
            doc["patient_id"] = None
            patient.doctor    = None
            db.session.commit()
            return jsonify({"message": f"✅ {doc['name']} is free!"}), 200
    return jsonify({"error": "No doctor assigned"}), 400

@app.route("/api/beds", methods=["GET"])
@login_required
def get_beds():
    icu_total        = sum(1 for b in beds if b["type"] == "ICU")
    general_total    = sum(1 for b in beds if b["type"] == "General")
    emergency_total  = sum(1 for b in beds if b["type"] == "Emergency")
    icu_free         = sum(1 for b in beds if b["type"] == "ICU"       and b["status"] == "available")
    general_free     = sum(1 for b in beds if b["type"] == "General"   and b["status"] == "available")
    emergency_free   = sum(1 for b in beds if b["type"] == "Emergency" and b["status"] == "available")
    return jsonify({
        "beds"           : beds,
        "icu_total"      : icu_total,
        "icu_free"       : icu_free,
        "general_total"  : general_total,
        "general_free"   : general_free,
        "emergency_total": emergency_total,
        "emergency_free" : emergency_free,
    })

@app.route("/api/beds/assign/<patient_id>", methods=["POST"])
@login_required
def assign_bed(patient_id):
    data     = request.get_json()
    patient  = Patient.query.get(patient_id)
    if not patient:
        return jsonify({"error": "Patient not found"}), 404
    if patient.bed:
        return jsonify({"error": f"Already assigned: {patient.bed}"}), 400
    bed_type = data.get("bed_type", "General")
    bed = next((b for b in beds if b["type"] == bed_type and b["status"] == "available"), None)
    if not bed:
        return jsonify({"error": f"No {bed_type} beds available"}), 400
    bed["status"]     = "occupied"
    bed["patient_id"] = patient_id
    patient.bed       = bed["id"]
    db.session.commit()
    return jsonify({"message": f"✅ {bed['id']} ({bed_type}) assigned!"}), 200

@app.route("/api/beds/release/<patient_id>", methods=["POST"])
@login_required
def release_bed(patient_id):
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({"error": "Patient not found"}), 404
    for bed in beds:
        if bed["patient_id"] == patient_id:
            bed["status"]     = "available"
            bed["patient_id"] = None
            patient.bed       = None
            db.session.commit()
            return jsonify({"message": f"✅ {bed['id']} is now free!"}), 200
    return jsonify({"error": "No bed assigned"}), 400

if __name__ == "__main__":
   import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
