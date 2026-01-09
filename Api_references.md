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

### 🔹 Ingestione temperatura stanza

**POST** `/temperatures`

**Input JSON**
```json
{
  "room_id": 2,
  "temperature": 23.4
}
```

**Output JSON**
```json
{
  "message": "Temperature recorded"
}
```

**Descrizione**  
Registra una lettura di temperatura per una stanza.

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

## 🔄 Nuovi endpoint per Seat Suggestions (estensioni)

### 🔹 Generate con opzioni (aggiornamento)

**POST** `/seat-suggestions/generate`

**Input JSON (opzionale)**
```json
{
  "date": "2026-01-15",    // YYYY-MM-DD, opzionale (default: today)
  "hour": 10,               // 0-23, opzionale (default: current hour)
  "history_days": 90,       // intero, opzionale (default: 90)
  "top_n": 10               // quanti vengono marcati come consigliati
}
```

**Output JSON**
```json
[
  { "seat_id": 5, "score": 0.82, "reason": "...", "is_recommended": true },
  ...
]
```

**Descrizione**  
Genera suggerimenti per la data/ora specificata (default: oggi/ora corrente), salva le raccomandazioni nel DB e marca i primi `top_n` risultati con `is_recommended=true`.

---

### 🔹 Get suggestions per data

**GET** `/seat-suggestions?date=YYYY-MM-DD&top=10`

**Output JSON**
```json
[
  { "seat_id": 5, "score": 0.82, "reason": "...", "is_recommended": true },
  ...
]
```

**Descrizione**  
Recupera le suggerimenti calcolati per la data indicata (o le ultime se non fornita). Parametro `top` facoltativo per limitare la risposta.

---

### 🔹 Recompute (admin)

**POST** `/seat-suggestions/recompute`

**Input JSON** (opzionale: vedi `/generate`)

**Output JSON**
```json
{ "message": "Recompute triggered", "generated": 120 }
```

**Descrizione**  
Endpoint protetto per forzare il ricalcolo globale delle raccomandazioni (richiede ruolo admin/staff). Può essere chiamato dal backend (job schedulato) o manualmente dall'admin.

---

### 🔹 Explain score

**GET** `/seat-suggestions/<seat_id>/explain?date=YYYY-MM-DD&hour=10`

**Output JSON**
```json
{
  "seat_id": 5,
  "date": "2026-01-15",
  "hour": 10,
  "occupancy_probability": 0.62,
  "comfort_score": 0.71,
  "energy_cost": 0.20,
  "final_score": 0.48,
  "reason": "Stanza già attiva, buona probabilità e comfort adeguato"
}
```

**Descrizione**  
Fornisce la spiegazione dettagliata dello score per un singolo posto, utile per la trasparenza delle raccomandazioni.

---