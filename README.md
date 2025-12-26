# 📚 Smart Library Booking System

A complete IoT-based system for monitoring seat availability in a university library. The project integrates hardware sensors, a backend API, and a responsive frontend to help students find free spots in real time.

## 🎯 Project Goals

- Detect seat occupancy using microcontrollers and sensors
- Store and process data via a backend service
- Display seat availability through a web-based frontend
- Provide real-time updates and intuitive user experience

## 🧱 Tech Stack

### 💡 Hardware
- Arduino
- IR and pressure sensors
- Wi-Fi modules

### 🖥️ Software
- **Backend**: Python (Flask)
- **Frontend**: Vue
- **Database**: MySQL

## 🛠️ Features
- Booking system
- Real-time seat tracking
- RESTful API for data access
- Interactive UI for students
- Admin dashboard for analytics

## 🚀 Getting Started

1. Clone the repo:
   ```bash
   git clone https://github.com/your-username/smart-library-seat-tracker.git
2. Open terminal and use:
- **Create env**:
```bash  
py -3.12 -m venv IoT_env
```
- **Activate env**: 
```bash  
IoT_env\Scripts\activate
```
- **Install requirements**: 
 ```bash  
pip install -r requirements.txt
```

## DB
Il db è sqllite, quindi scarica e avvia DBeaver -> file-> trova file per nome e apri il file del progetto -> instance-> iot.db.
Una volta aperto puoi selezionare "diagramma" per vedere le relazioni tra le tabelle. 
Qualunque modifica al db va fatta o tramite script oppure modificando i file model e avviando il progetto, che aggiornerà il db in automatico.

## Aggiornamento modifiche: 
Sono stati create diverse tabelle e relazioni per rappresentare i digital twin, tabelle di lettura e tabelle i "comando" per l'energia. 
Ho anche creato un seatSuggestion in modo che venga calcolato dinamicamente (AI - like) un sistema di suggerimento dei posti a sedere basato su uno score calcolato in base a diversi fattori (vicinanza ad altri posti occupati, vicinanza a prese di corrente, vicinanza a finestre, ecc..)
## Come funziona il calcolo dello score: Predictive Energy-Aware Seat Recommendation
Ogni posto ha uno score energetico + comfort + probabilità di riempimento.
score = 
  (occupancy_probability * 0.4)
+ (comfort_score * 0.3)
- (energy_cost * 0.3)
1. Occupancy probability

Calcolata da storico booking:
- stesso giorno della settimana
- stessa fascia oraria
- stesso periodo dell’anno

prenotazioni_passate / slot_totali
2. Comfort score
Basato su:
- temperatura media storica
- esposizione al sole
- stagione
3. Energy cost
Stima euristica:
- stanza vuota → costo alto
- stanza già occupata → costo basso