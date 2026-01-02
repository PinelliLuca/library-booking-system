import serial, threading, requests, json

def handle_serial(port):
    ser = serial.Serial(port, 9600)
    while True:
        line = ser.readline().decode().strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            print(f"Errore JSON da {port}: {line}")
            continue

        if "id" in data and "is_occupied" in data:
            seat_id = data["id"]
            payload = {"is_occupied": data["is_occupied"]}
            requests.patch(f"http://localhost:5000/seats/{seat_id}", json=payload)
            print(f"[{port}] Seat {seat_id} aggiornato: {payload}")
        elif "sensor_error" in data:
            print(f"[{port}] Errore sensore: {data['sensor_error']}")

# Lista delle porte da aprire
ports = ["COM3", "COM4"]

for port in ports:
    threading.Thread(target=handle_serial, args=(port,), daemon=True).start()

print("Bridge avviato per più microcontrollori...")
while True:
    pass  # il main thread resta vivo
#per sapere quali porte aprire, terminale->mode
#altrimenti gestione dispositivi e controlli le porte COM da aggiunere alla lista