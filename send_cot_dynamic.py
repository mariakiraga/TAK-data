import socket
import ssl
import time
import requests
from json2cot import create_cot_event, xy_to_latlon

from dotenv import load_dotenv
import os

load_dotenv()

SERVER_IP = os.getenv("TAK_SERVER_IP")
SERVER_PORT = int(os.getenv("TAK_SERVER_PORT"))
CLIENT_CERT = os.getenv("TAK_CLIENT_CERT")
CLIENT_KEY = os.getenv("TAK_CLIENT_KEY")
CA_CERT = os.getenv("TAK_CA_CERT")

JSON_URL = "https://df02d693a0bf.ngrok-free.app/position"  # remote JSON endpoint
POLL_INTERVAL = 1  # seconds between checks

headers = {
    "ngrok-skip-browser-warning": "true"
}

# ====== SSL CONTEXT ======
context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=CA_CERT)
context.load_cert_chain(certfile=CLIENT_CERT, keyfile=CLIENT_KEY)

# ====== Track last sent position ======
last_position = None
first_point_sent = False  # flag to always send the first point

def fetch_json():
    try:
        # print(f"[DEBUG] Fetching JSON from {JSON_URL}...")
        r = requests.get(JSON_URL, headers=headers, timeout=5)
        r.raise_for_status()
        data = r.json()
        # print(f"[DEBUG] Received data: {data}")
        return data
    except Exception as e:
        print(f"[ERROR] Fetching JSON failed: {e}")
        return None

# ====== Connect to TAK ======
with socket.create_connection((SERVER_IP, SERVER_PORT)) as sock:
    with context.wrap_socket(sock, server_hostname=SERVER_IP) as ssock:
        print(f"[INFO] Connected to TAK Server at {SERVER_IP}:{SERVER_PORT}")

        try:
            while True:
                data = fetch_json()
                if not data or "new_position" not in data:
                    # print("[DEBUG] No new_position in JSON, skipping this cycle.")
                    time.sleep(POLL_INTERVAL)
                    continue

                x, y = data["new_position"]
                lat, lon = xy_to_latlon(x, y)
                # print(f"[DEBUG] Converted x={x}, y={y} to lat={lat}, lon={lon}")

                # Always send the first point
                if not first_point_sent:
                    cot_message = create_cot_event(lat, lon)
                    ssock.sendall((cot_message + "\n").encode("utf-8"))
                    last_position = (lat, lon)
                    first_point_sent = True
                    print(f"[INFO] Sent FIRST CoT point: lat={lat} lon={lon}")
                # Send subsequent points only if they moved
                elif last_position != (lat, lon):
                    cot_message = create_cot_event(lat, lon)
                    ssock.sendall((cot_message + "\n").encode("utf-8"))
                    last_position = (lat, lon)
                    print(f"[INFO] Sent updated CoT point: lat={lat} lon={lon}")
                # else:
                #     print("[DEBUG] Position unchanged, not sending.")

                time.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            print("[INFO] Exiting, connection will close.")
