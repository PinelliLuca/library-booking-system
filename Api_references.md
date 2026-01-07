# 📡 API Reference – Smart Library Digital Twin System

Questo documento riassume **tutte le route disponibili** nel backend:

Per ogni endpoint sono indicati:
- metodo HTTP
- endpoint
- input JSON (se presente)
- output JSON
- descrizione sintetica

---

## 👤 USER / AUTH

### 🔹 Register

**POST** `/register`

**Input JSON**
```json
{
  "username": "string",
  "password": "string",
  "first_name": "string",
  "last_name": "string",
  "email": "string"
}
```

**Output JSON**
```json
{
  "message": "User registered successfully",
  "user_id": 1
}
```

**Descrizione**  
Crea un nuovo utente nel sistema.

---

### 🔹 Login

**POST** `/login`

**Input JSON**
```json
{
  "username": "string",
  "password": "string"
}
```

**Output JSON**
```json
{
  "access_token": "JWT_TOKEN",
  "user": {
    "id": 1,
    "username": "string",
    "role": "student"
  }
}
```

**Descrizione**  
Autentica l’utente e restituisce un JWT.

---

## 🪑 SEATS

### 🔹 Lista posti

**GET** `/seats`

**Output JSON**
```json
[
  {
    "seat_id": 1,
    "room_id": 2,
    "active": true,
    "booking_status": "confirmed",
    "real_occupancy": true
  }
]
```

**Descrizione**  
Restituisce tutti i posti con stato di prenotazione e occupazione reale.

---

### 🔹 Dettaglio posto

**GET** `/seats/{seat_id}`

**Output JSON**
```json
{
  "seat_id": 1,
  "room_id": 2,
  "active": true,
  "real_occupancy": false
}
```

**Descrizione**  
Restituisce le informazioni di un singolo posto.

---

## 📅 BOOKINGS

### 🔹 Booking attivi dell’utente

**GET** `/bookings`  
🔐 JWT required

**Output JSON**
```json
[
  {
    "id": 10,
    "seat_id": 3,
    "start_time": "2025-06-24T10:00:00",
    "end_time": "2025-06-24T12:00:00",
    "status": "confirmed"
  }
]
```

**Descrizione**  
Restituisce le prenotazioni attive dell’utente loggato.

---

### 🔹 Crea booking

**POST** `/bookings`  
🔐 JWT required

**Input JSON**
```json
{
  "seat_id": 3,
  "start_time": "2025-06-24T10:00:00",
  "end_time": "2025-06-24T12:00:00"
}
```

**Output JSON**
```json
{
  "message": "Booking created, waiting for check-in",
  "booking_id": 10
}
```

**Descrizione**  
Crea una prenotazione se il posto è disponibile.

---

### 🔹 Check-in booking

**POST** `/bookings/check-in`  
🔐 JWT required

**Input JSON**
```json
{
  "seat_id": 3
}
```

**Output JSON**
```json
{
  "message": "Check-in successful"
}
```

**Descrizione**  
Conferma la presenza fisica dell’utente sul posto prenotato.

---

## 📡 IOT – SEAT OCCUPANCY (ARDUINO)

### 🔹 Ingestione sensori seduta

**POST** `/seat-occupancy`

**Input JSON**
```json
{
  "device_id": 12,
  "weight": true,
  "proximity": true
}
```

**Output JSON**
```json
{
  "message": "Occupancy reading saved"
}
```

**Descrizione**  
Invio dati sensori (peso + prossimità) dal microcontrollore.

---

## 🌡️ IOT – TEMPERATURE

🔹 Ingestione temperatura stanza  
POST /temperatures

Input JSON
{
  "room_id": 2,
  "temperature": 23.4
}

Output JSON
{
  "message": "Temperature recorded"
}

Descrizione  
Riceve una lettura di temperatura inviata dal microcontrollore e la salva nel backend associandola a una stanza.

---

🔹 Ultima temperatura registrata  
GET /temperatures/latest

Output JSON
{
  "room_id": 2,
  "temperature": 23.4,
  "timestamp": "2026-01-03T10:15:00"
}

Descrizione  
Restituisce l’ultima temperatura disponibile per una stanza.  
Se non sono presenti dati, il backend risponde con un messaggio di assenza dati.

---

🔹 Statistiche temperature  
GET /temperatures/stats

Output JSON
{
  "min": 19.8,
  "max": 25.1,
  "avg": 22.6,
  "count": 42
}

Descrizione  
Calcola statistiche di base sulle temperature raccolte (minima, massima, media e numero di campioni).  
Questi dati costituiscono la base per analisi energetiche e future predizioni di consumo.


---

## ⚡ ENERGY MANAGEMENT

### 🔹 Invio comando energetico

**POST** `/energy-command`  
🔐 JWT required (admin)

**Input JSON**
```json
{
  "room_id": 2,
  "command_type": "set_temp",
  "value": 22
}
```

**Output JSON**
```json
{
  "message": "Command issued"
}
```

**Descrizione**  
Invia comandi a luci o climatizzazione di una stanza.

---

## 🧠 AI-LIKE – SEAT SUGGESTIONS

### 🔹 Posti suggeriti

**GET** `/seat-suggestions`  
🔐 JWT required

**Output JSON**
```json
[
  {
    "seat_id": 5,
    "score": 0.82,
    "reason": "Low energy cost and high comfort"
  }
]
```

**Descrizione**  
Restituisce i posti suggeriti in base a comfort, occupazione e consumo energetico.

---

## 📝 Note finali


- JWT va passato come `Authorization: Bearer <token>`
- I microcontrollori **non modificano direttamente lo stato**, ma inviano letture
- Il backend agisce come Digital Twin centrale

---
