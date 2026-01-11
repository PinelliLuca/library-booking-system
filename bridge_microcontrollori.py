import json
import time
import threading
import serial
import requests


BACKEND_BASE = "http://127.0.0.1:5000"

DEVICES = [
    {
        "name": "esp32-room",
        "port": "COM6",
        "baud": 115200,
        "endpoint": "/temperatures",
        "expects_response": True,
        "schema": "temperature",
    },
    {
        "name": "arduino-seat",
        "port": "COM5",
        "baud": 9600,
        "endpoint": "/seat-occupancy",
        "expects_response": False,
        "schema": "seat",
    },
]


def is_json_line(line: str) -> bool:
    return line.startswith("{") and line.endswith("}")


def handle_message(schema: str, msg: dict) -> bool:
    if schema == "temperature":
        return "room_id" in msg and "temperature" in msg
    if schema == "seat":
        return "device_id" in msg and "is_occupied" in msg
    return False


def serial_worker(cfg: dict):
    name = cfg["name"]
    port = cfg["port"]
    baud = cfg["baud"]
    endpoint = cfg["endpoint"]
    expects_response = cfg["expects_response"]
    schema = cfg["schema"]

    print(f"[{name}] Opening {port} @ {baud}")
    ser = serial.Serial(port, baud, timeout=1)
    time.sleep(2)

    while True:
        try:
            raw = ser.readline().decode("utf-8", errors="ignore").strip()
            if not raw:
                continue

            print(f"[{name} RX]", raw)

            if not is_json_line(raw):
                continue

            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                print(f"[{name} ERR] invalid JSON")
                continue

            if not handle_message(schema, msg):
                continue

            url = BACKEND_BASE + endpoint
            r = requests.post(url, json=msg, timeout=10)
            print(f"[{name} -> BE] {r.status_code}")

            if expects_response and r.status_code in (200, 201):
                try:
                    resp = r.json()
                except ValueError:
                    continue

                line = json.dumps(resp, separators=(",", ":")) + "\n"
                ser.write(line.encode("utf-8"))
                print(f"[{name} TX]", line.strip())

        except Exception as e:
            print(f"[{name} ERR]", e)
            time.sleep(1)


def main():
    for cfg in DEVICES:
        t = threading.Thread(target=serial_worker, args=(cfg,), daemon=True)
        t.start()

    print("[BRIDGE] Running (multi-device)")
    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()
