from datetime import datetime
from threading import Thread, Event
import json
import logging
import uuid
import paho.mqtt.client as mqtt
from flask import current_app

logger = logging.getLogger(__name__)


class HospitalMQTTHandler:
    def __init__(self, app):
        print("Initializing Hospital MQTT Handler")
        self.app = app

        client_id = f"hospital_handler_{uuid.uuid4().hex[:8]}"
        if hasattr(mqtt, "CallbackAPIVersion"):
            self.client = mqtt.Client(
                mqtt.CallbackAPIVersion.VERSION1,
                client_id=client_id,
                clean_session=True,
            )
        else:
            self.client = mqtt.Client(client_id=client_id, clean_session=True)

        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        self.client.on_subscribe = self._on_subscribe

        self._setup_mqtt()
        self.connected = False
        self.stopping = Event()
        self.reconnect_thread = None

    def _setup_mqtt(self):
        """Setup MQTT configuration"""
        config = self.app.config.get("MQTT_CONFIG", {})
        self.broker = config.get("broker", "broker.hivemq.com")
        self.port = config.get("port", 1883)

        # Topics to subscribe (patient vital signs)
        self.topics = [
            # hospital/patient/<patient_id>/vitals/<measure_type>
            ("hospital/patient/+/vitals/#", 0),
        ]
        print(f"MQTT Setup - Broker: {self.broker}, Port: {self.port}")
        print(f"Topics: {self.topics}")

    def start(self):
        """Start MQTT client in non-blocking mode"""
        try:
            print("Starting MQTT handler...")
            self.client.loop_start()
            self._connect()
            self.reconnect_thread = Thread(target=self._reconnection_loop, daemon=True)
            self.reconnect_thread.start()
            print("MQTT handler started")
        except Exception as e:
            print(f"Error starting MQTT handler: {str(e)}")

    def stop(self):
        """Stop MQTT client"""
        self.stopping.set()
        if self.reconnect_thread:
            self.reconnect_thread.join(timeout=1.0)
        self.client.loop_stop()
        if self.connected:
            self.client.disconnect()
        print("MQTT handler stopped")

    def _connect(self):
        """Attempt to connect to the MQTT broker"""
        try:
            self.client.connect(self.broker, self.port, 60)
            print(f"Connecting to {self.broker}:{self.port}...")
        except Exception as e:
            print(f"MQTT connection attempt failed: {str(e)}")
            self.connected = False

    def _reconnection_loop(self):
        """Background thread handling automatic reconnection"""
        while not self.stopping.wait(5):
            if not self.connected:
                print("Attempting MQTT reconnection...")
                self._connect()

    def _on_connect(self, client, userdata, flags, rc):
        """Connection callback"""
        if rc == 0:
            self.connected = True
            print("Connected to MQTT broker")
            for topic, qos in self.topics:
                client.subscribe(topic, qos)
                print(f"Subscribed to {topic}")
        else:
            self.connected = False
            print(f"Failed to connect to MQTT broker with code: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        """Disconnection callback"""
        self.connected = False
        if rc != 0:
            print(f"Unexpected disconnection from MQTT broker (rc={rc})")

    def _on_subscribe(self, client, userdata, mid, granted_qos):
        """Subscription confirmation callback"""
        print(f"Subscription confirmed (mid={mid}, qos={granted_qos})")

    def _on_message(self, client, userdata, msg) -> None:
        """Message callback routing incoming MQTT messages"""
        try:
            topic = msg.topic
            topic_parts = topic.split("/")
            payload = msg.payload.decode("utf-8").strip()
            print(f"Received message on {topic}: {payload}")

            with self.app.app_context():
                if "vitals" in topic_parts:
                    self._handle_vitals_message(topic_parts, payload)
                else:
                    print(f"Unhandled MQTT topic: {topic}")

        except UnicodeDecodeError:
            print(f"Failed to decode non-UTF8 payload on topic '{msg.topic}'")
        except Exception as e:
            print(f"Error processing message: {str(e)}")

    def _handle_vitals_message(self, topic_parts: list[str], payload: str) -> None:
        """Process vital sign readings: hospital/patient/<patient_id>/vitals/<measure_type>"""
        if len(topic_parts) < 5:
            print(f"Invalid vitals topic format: {'/'.join(topic_parts)}")
            return

        patient_id = topic_parts[2].strip()
        measure_type = topic_parts[4].strip()

        # Parse payload (supports both raw numbers like "78" and JSON like {"value": 78, "device_id": "DEV_01"})
        try:
            parsed = json.loads(payload)
            if isinstance(parsed, dict):
                if "value" not in parsed:
                    print(f"Missing 'value' key in JSON payload: {payload}")
                    return
                value = float(parsed["value"])
                device_id = str(parsed.get("device_id", "nodemcu_patient"))
            else:
                value = float(parsed)
                device_id = "unknown"
        except (ValueError, TypeError) as e:
            print(f"Invalid vitals payload '{payload}': {str(e)}")
            return

        db_service = current_app.config["DB_SERVICE"]
        patients = db_service.query_drs(
            "patient", {"profile.patient_id": patient_id}
        )
        if not patients:
            print(f"Patient not found for vitals update: {patient_id}")
            return

        patient = patients[0]
        measurements = patient.get("data", {}).get("measurements", [])
        measurement = {
            "device_id": device_id,
            "measure_type": measure_type,
            "value": value,
            "timestamp": datetime.utcnow(),
        }
        measurements.append(measurement)

        patient_metadata = {**patient.get("metadata", {})}
        db_service.update_dr(
            "patient",
            patient["_id"],
            {
                "data.measurements": measurements,
                "metadata": patient_metadata,
            },
        )
        print(f"Saved {measure_type}={value} for patient {patient_id}")