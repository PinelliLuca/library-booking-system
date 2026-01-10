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

### 🔹 Generate suggestions

**POST** `/seat-suggestions/generate`

**Input JSON (opzionale)**
```json
{
  "date": "2026-01-15",
  "hour": 10,
  "history_days": 90,
  "top_n": 10
}
```

**Output JSON**
```json
[
  {
    "seat_id": 5,
    "score": 0.82,
    "reason": "occ=0.62,comfort=0.71,energy=0.20",
    "is_recommended": true
  }
]
```

**Descrizione**  
Calcola i suggerimenti per la data/ora indicata (default: now), salva i risultati a DB e marca i migliori `top_n` con `is_recommended=true`.

---

### 🔹 Get suggestions

**GET** `/seat-suggestions?date=YYYY-MM-DD&top=10`

**Output JSON**
```json
[
  {
    "seat_id": 5,
    "score": 0.82,
    "reason": "occ=0.62,comfort=0.71,energy=0.20",
    "is_recommended": true
  }
]
```

**Descrizione**  
Recupera i suggerimenti già calcolati per una data specifica. Se `date` non è fornita, restituisce l’ultimo calcolo disponibile.

---

### 🔹 Recompute suggestions (admin)

**POST** `/seat-suggestions/recompute`

**Input JSON** (opzionale, come `/generate`)

**Output JSON**
```json
{
  "message": "Recompute triggered",
  "generated": 120
}
```

**Descrizione**  
Forza il ricalcolo globale delle seat suggestions. Pensato per:
- admin
- job schedulati
- dimostrazione in tempo reale

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
  "reason": "occ=0.62,comfort=0.71,energy=0.20"
}
```

**Descrizione**  
Espone in modo trasparente tutti i fattori che contribuiscono allo score di un posto. Endpoint chiave per la spiegazione all’esame.

---

## 🎭 Demo Endpoints (per esame)

Questi endpoint **non sono destinati alla produzione**, ma servono a:
- popolare il DB
- simulare scenari
- mostrare il comportamento AI-like del sistema

---

### 🔹 Clear all demo data

**POST** `/demo/clear-all`

**Descrizione**  
Elimina tutti i dati di demo rispettando le foreign key.

---

### 🔹 Populate rooms & seats

**POST** `/demo/populate-rooms-seats`

**Descrizione**  
Crea 3 stanze:
- Cold Room (north)
- Medium Room (east)
- Hot Room (south)

con 10 posti ciascuna.

---

### 🔹 Populate users

**POST** `/demo/populate-users`

**Input JSON**
```json
{ "count": 5 }
```

**Descrizione**  
Crea utenti fittizi (studenti) per simulare prenotazioni reali.

---

### 🔹 Populate temperatures

**POST** `/demo/populate-temperatures`

**Descrizione**  
Genera uno storico di 30 giorni di temperature coerenti con l’esposizione della stanza.

---

### 🔹 Populate bookings

**POST** `/demo/populate-bookings`

**Descrizione**  
Crea prenotazioni storiche casuali per alimentare l’occupancy probability.

---

### 🔹 Set room energy state

**POST** `/demo/set-room-energy`

**Input JSON**
```json
{
  "room_id": 1,
  "lights_on": true,
  "ac_on": true,
  "target_temperature": 22
}
```

**Descrizione**  
Imposta manualmente lo stato energetico di una stanza (IoT simulation).

---

### 🔹 Run full scenario

**POST** `/demo/run-scenario`

**Descrizione**  
Esegue l’intera demo in sequenza:
1. clear DB
2. crea stanze e posti
3. crea utenti
4. genera temperature
5. genera prenotazioni

Pronto per eseguire subito `/seat-suggestions/generate`.