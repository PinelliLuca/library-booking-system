import serial
import requests
import json

# Apri la porta seriale (es. COM3 su Windows, /dev/ttyUSB0 su Linux)
ser = serial.Serial("COM3", 9600)

while True:
    line = ser.readline().decode().strip()
    if not line:
        continue

    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        print("Errore nel parsing JSON:", line)
        continue

    # Caso 1: stato del posto
    if "id" in data and "is_occupied" in data:
        seat_id = data["id"]
        payload = {"is_occupied": data["is_occupied"]}
        response = requests.patch(f"http://localhost:5000/seats/{seat_id}", json=payload)
        print(f"Seat {seat_id} aggiornato: {payload}, risposta {response.status_code}")

    # Caso 2: errore sensore
    elif "sensor_error" in data:
        # Qui puoi decidere come gestire l'errore (log, DB, alert)
        print(f"Errore sensore rilevato: {data['sensor_error']}")
