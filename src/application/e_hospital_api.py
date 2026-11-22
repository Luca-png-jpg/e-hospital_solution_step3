from flask import Blueprint, request, jsonify, current_app
from src.virtualization.digital_replica.dr_factory import DRFactory

hospital_api = Blueprint("e_hospital_api", __name__, url_prefix="/api/hospital")


def register_e_hospital_blueprint(app):
    """Register the e-hospital blueprint with the Flask app"""
    app.register_blueprint(hospital_api)


# --- Room endpoints ---

@hospital_api.route("/rooms", methods=["POST"])
def create_room():
    """Create a new room DR"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400

        dr_factory = DRFactory("src/virtualization/templates/room.yaml")
        room = dr_factory.create_dr("room", data)

        room_number = room["profile"]["room_number"]
        existing = current_app.config["DB_SERVICE"].query_drs(
            "room", {"profile.room_number": room_number}
        )
        if existing:
            return jsonify({"error": f"Room {room_number} already exists"}), 409

        dr_id = current_app.config["DB_SERVICE"].save_dr("room", room)

        return jsonify({
            "status": "success",
            "message": "Room created successfully",
            "dr_id": dr_id,
            "room_number": room_number,
        }), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@hospital_api.route("/rooms", methods=["GET"])
def list_rooms():
    """List all rooms with optional filters"""
    try:
        filters = {}
        if request.args.get("status"):
            filters["metadata.status"] = request.args.get("status")
        if request.args.get("room_type"):
            filters["profile.room_type"] = request.args.get("room_type")
        if request.args.get("floor") is not None:
            filters["profile.floor"] = int(request.args.get("floor"))

        rooms = current_app.config["DB_SERVICE"].query_drs("room", filters)
        return jsonify(rooms), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@hospital_api.route("/rooms/<room_number>", methods=["GET"])
def get_room(room_number):
    """Get room details"""
    try:
        room = current_app.config["DB_SERVICE"].query_drs("room", {"profile.room_number": room_number})
        if not room:
            return jsonify({"error": "Room not found"}), 404
        return jsonify(room), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- Patient endpoints ---

@hospital_api.route("/patients", methods=["POST"])
def create_patient():
    """Create a new patient DR"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400

        dr_factory = DRFactory("src/virtualization/templates/patient.yaml")
        patient = dr_factory.create_dr("patient", data)

        clinical_id = patient["profile"]["patient_id"]
        existing = current_app.config["DB_SERVICE"].query_drs(
            "patient", {"profile.patient_id": clinical_id}
        )
        if existing:
            return jsonify({"error": f"Patient {clinical_id} already exists"}), 409

        dr_id = current_app.config["DB_SERVICE"].save_dr("patient", patient)

        return jsonify({
            "status": "success",
            "message": "Patient created successfully",
            "dr_id": dr_id,
            "patient_id": clinical_id,
        }), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@hospital_api.route("/patients", methods=["GET"])
def list_patients():
    """List all patients with optional filters"""
    try:
        filters = {}
        if request.args.get("status"):
            filters["metadata.status"] = request.args.get("status")
        if request.args.get("patient_id"):
            filters["profile.patient_id"] = request.args.get("patient_id")

        patients = current_app.config["DB_SERVICE"].query_drs("patient", filters)
        return jsonify(patients), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@hospital_api.route("/patients/<patient_id>", methods=["GET"])
def get_patient(patient_id):
    """Get patient details"""
    try:
        patient = current_app.config["DB_SERVICE"].query_drs("patient", {"profile.patient_id": patient_id})
        if not patient:
            return jsonify({"error": "Patient not found"}), 404
        return jsonify(patient), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- Doctor endpoints ---

@hospital_api.route("/doctors", methods=["POST"])
def create_doctor():
    """Create a new doctor DR"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400

        dr_factory = DRFactory("src/virtualization/templates/doctor.yaml")
        doctor = dr_factory.create_dr("doctor", data)

        doctor_id = doctor["profile"]["doctor_id"]
        rfid_tag = doctor["profile"]["rfid_tag"]

        existing_id = current_app.config["DB_SERVICE"].query_drs(
            "doctor", {"profile.doctor_id": doctor_id}
        )
        if existing_id:
            return jsonify({"error": f"Doctor {doctor_id} already exists"}), 409

        existing_rfid = current_app.config["DB_SERVICE"].query_drs(
            "doctor", {"profile.rfid_tag": rfid_tag}
        )
        if existing_rfid:
            return jsonify({"error": f"RFID tag {rfid_tag} is already assigned"}), 409

        dr_id = current_app.config["DB_SERVICE"].save_dr("doctor", doctor)

        return jsonify({
            "status": "success",
            "message": "Doctor created successfully",
            "dr_id": dr_id,
            "doctor_id": doctor_id,
        }), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@hospital_api.route("/doctors", methods=["GET"])
def list_doctors():
    """List all doctors with optional filters"""
    try:
        filters = {}
        if request.args.get("status"):
            filters["metadata.status"] = request.args.get("status")
        if request.args.get("specialization"):
            filters["profile.specialization"] = request.args.get("specialization")
        if request.args.get("rfid_tag"):
            filters["profile.rfid_tag"] = request.args.get("rfid_tag")

        doctors = current_app.config["DB_SERVICE"].query_drs("doctor", filters)
        return jsonify(doctors), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@hospital_api.route("/doctors/<doctor_id>", methods=["GET"])
def get_doctor(doctor_id):
    """Get doctor details"""
    try:
        doctor = current_app.config["DB_SERVICE"].query_drs("doctor", {"profile.doctor_id": doctor_id})
        if not doctor:
            return jsonify({"error": "Doctor not found"}), 404
        return jsonify(doctor), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Operational & Relationship endpoints ---

@hospital_api.route("/rooms/<room_number>/patients", methods=["POST"])
def assign_patient_to_room(room_number):
    """Assign (or transfer) a patient to a room"""
    try:
        data = request.get_json()
        if not data or not data.get("patient_id"):
            return jsonify({"error": "Missing required field: patient_id"}), 400

        room_number = room_number.strip()
        patient_id = data["patient_id"].strip()
        db_service = current_app.config["DB_SERVICE"]

        rooms = db_service.query_drs("room", {"profile.room_number": room_number})
        if not rooms:
            return jsonify({"error": f"Room {room_number} not found"}), 404
        room = rooms[0]

        if room.get("metadata", {}).get("status") in ["maintenance", "cleaning"]:
            return jsonify({"error": f"Room {room_number} is not available"}), 400

        patients = db_service.query_drs("patient", {"profile.patient_id": patient_id})
        if not patients:
            return jsonify({"error": f"Patient {patient_id} not found"}), 404
        patient = patients[0]

        current_patients = room.get("data", {}).get("current_patients", [])
        if patient_id in current_patients:
            return jsonify(
                {"error": f"Patient {patient_id} is already in room {room_number}"}
            ), 409

        capacity = room["profile"]["capacity"]
        if len(current_patients) >= capacity:
            return jsonify(
                {"error": f"Room {room_number} is at full capacity ({capacity})"}
            ), 400

        # If the patient was in another room, remove them from the previous room
        old_room_number = patient.get("metadata", {}).get("current_room_id")
        if old_room_number and old_room_number != room_number:
            old_rooms = db_service.query_drs(
                "room", {"profile.room_number": old_room_number}
            )
            if old_rooms:
                old_room = old_rooms[0]
                old_patients = old_room.get("data", {}).get("current_patients", [])
                if patient_id in old_patients:
                    old_patients.remove(patient_id)
                    old_metadata = {**old_room.get("metadata", {})}
                    if not old_patients and old_metadata.get("status") == "occupied":
                        old_metadata["status"] = "available"
                    db_service.update_dr(
                        "room",
                        old_room["_id"],
                        {
                            "data.current_patients": old_patients,
                            "metadata": old_metadata,
                        },
                    )

        # Add patient to the target room and mark room as occupied
        current_patients.append(patient_id)
        room_metadata = {**room.get("metadata", {}), "status": "occupied"}
        db_service.update_dr(
            "room",
            room["_id"],
            {
                "data.current_patients": current_patients,
                "metadata": room_metadata,
            },
        )

        # Update patient's current_room_id
        patient_metadata = {
            **patient.get("metadata", {}),
            "current_room_id": room_number,
        }
        db_service.update_dr(
            "patient",
            patient["_id"],
            {"metadata": patient_metadata},
        )

        return jsonify({
            "status": "success",
            "message": f"Patient {patient_id} assigned to room {room_number}",
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@hospital_api.route("/doctors/<doctor_id>/patients", methods=["POST"])
def assign_patient_to_doctor(doctor_id):
    """Assign a patient to a doctor"""
    try:
        data = request.get_json()
        if not data or not data.get("patient_id"):
            return jsonify({"error": "Missing required field: patient_id"}), 400

        doctor_id = doctor_id.strip()
        patient_id = data["patient_id"].strip()
        db_service = current_app.config["DB_SERVICE"]

        doctors = db_service.query_drs("doctor", {"profile.doctor_id": doctor_id})
        if not doctors:
            return jsonify({"error": f"Doctor {doctor_id} not found"}), 404
        doctor = doctors[0]

        patients = db_service.query_drs("patient", {"profile.patient_id": patient_id})
        if not patients:
            return jsonify({"error": f"Patient {patient_id} not found"}), 404

        assigned_patients = doctor.get("data", {}).get("assigned_patients", [])
        if patient_id in assigned_patients:
            return jsonify(
                {"error": f"Patient {patient_id} is already assigned to doctor {doctor_id}"}
            ), 409

        assigned_patients.append(patient_id)
        doctor_metadata = {**doctor.get("metadata", {})}
        db_service.update_dr(
            "doctor",
            doctor["_id"],
            {
                "data.assigned_patients": assigned_patients,
                "metadata": doctor_metadata,
            },
        )

        return jsonify({
            "status": "success",
            "message": f"Patient {patient_id} assigned to doctor {doctor_id}",
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- Staff Monitoring endpoints ---

@hospital_api.route("/patients/<patient_id>/vitals", methods=["GET"])
def get_patient_vitals(patient_id):
    """Get vital signs measurements for a patient (optional ?measure_type= filter)"""
    try:
        matches = current_app.config["DB_SERVICE"].query_drs(
            "patient", {"profile.patient_id": patient_id.strip()}
        )
        if not matches:
            return jsonify({"error": "Patient not found"}), 404

        patient = matches[0]
        measurements = patient.get("data", {}).get("measurements", [])

        measure_type = request.args.get("measure_type")
        if measure_type:
            measurements = [
                m for m in measurements if m.get("measure_type") == measure_type
            ]

        return jsonify({
            "patient_id": patient["profile"]["patient_id"],
            "status": patient.get("metadata", {}).get("status"),
            "current_room_id": patient.get("metadata", {}).get("current_room_id"),
            "measurements": measurements,
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@hospital_api.route("/patients/<patient_id>/visits", methods=["GET"])
def get_patient_visits(patient_id):
    """Get recorded doctor visits for a patient"""
    try:
        matches = current_app.config["DB_SERVICE"].query_drs(
            "patient", {"profile.patient_id": patient_id.strip()}
        )
        if not matches:
            return jsonify({"error": "Patient not found"}), 404

        patient = matches[0]
        return jsonify({
            "patient_id": patient["profile"]["patient_id"],
            "doctor_visits": patient.get("data", {}).get("doctor_visits", []),
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@hospital_api.route("/rooms/<room_number>/access-logs", methods=["GET"])
def get_room_access_logs(room_number):
    """Get RFID doctor access logs for a room"""
    try:
        matches = current_app.config["DB_SERVICE"].query_drs(
            "room", {"profile.room_number": room_number.strip()}
        )
        if not matches:
            return jsonify({"error": "Room not found"}), 404

        room = matches[0]
        return jsonify({
            "room_number": room["profile"]["room_number"],
            "current_patients": room.get("data", {}).get("current_patients", []),
            "access_logs": room.get("data", {}).get("access_logs", []),
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500