# 📚 Smart Library Digital Twin System

## 📌 Riassunto del progetto

Questo progetto realizza un **sistema IoT per la gestione intelligente di una biblioteca universitaria**, basato sul concetto di **Digital Twin**. L’obiettivo è ottimizzare l’uso dei posti a sedere e il consumo energetico attraverso sensori fisici, un backend centralizzato e un sistema di suggerimento "AI-like".

Gli studenti possono prenotare un posto per una specifica data e fascia oraria. I posti sono monitorati da microcontrollori dotati di **sensori di prossimità e di peso**, che permettono di verificare se il posto è realmente occupato. Se un posto prenotato rimane libero per troppo tempo, il sistema lo **disassegna automaticamente**, rendendolo nuovamente disponibile.

Parallelamente, il sistema gestisce un secondo Digital Twin dedicato alle **stanze della biblioteca**, monitorando temperatura, climatizzazione, illuminazione e consumo energetico. In base all’occupazione reale e storica, il sistema suggerisce i posti che minimizzano il dispendio energetico complessivo.

Il progetto è pensato come **dimostrazione architetturale e concettuale** per un esame universitario, ma è implementato in modo funzionante.

---

## 🎯 Obiettivi principali

- Gestione delle prenotazioni dei posti a sedere
- Verifica dell’occupazione reale tramite sensori IoT
- Rilascio automatico dei posti non utilizzati
- Monitoraggio ambientale delle stanze (temperatura)
- Controllo energetico (luci e climatizzazione)
- Suggerimento intelligente dei posti a sedere
- Riduzione del consumo energetico della biblioteca

---

## 🧱 Architettura del sistema

Il sistema è composto da tre livelli principali:

### 🔌 Hardware (IoT)
- Microcontrollori (es. Arduino / ESP)
- Sensori di peso (seduta)
- Sensori di prossimità
- Sensori di temperatura
- Attuatori per climatizzazione e illuminazione

### 🖥️ Backend
- **Python – Flask**
- **Flask-Smorest** per API REST
- **Flask-JWT-Extended** per autenticazione
- **SQLAlchemy** per ORM
- **SQLite** come database

### 🌐 Frontend
- **Vue.js**
- Interfaccia studenti per prenotazioni
- Dashboard admin per monitoraggio energetico

---

## 🧠 Digital Twin

### Digital Twin dei Posti (Seat Twin)

Ogni posto fisico è rappresentato digitalmente e associato a:
- Prenotazioni
- Sensori di peso e prossimità
- Stato di occupazione reale

Il sistema confronta:
- prenotazione attiva
- presenza fisica reale

Se lo studente si allontana per un tempo eccessivo, il posto viene **rilasciato automaticamente**.

---

### Digital Twin delle Stanze (Room Energy Twin)

Ogni stanza della biblioteca è rappresentata da un Digital Twin che gestisce:
- Temperatura attuale e storica
- Stato luci (on/off)
- Stato climatizzazione (on/off)
- Temperatura target

Se una stanza è vuota:
- luci spente
- climatizzazione disattivata

Questo permette di **ridurre sprechi energetici**.

---

## 🧠 Sistema di suggerimento (AI-like)

Il progetto include un sistema di suggerimento dei posti a sedere chiamato:

**Predictive Energy-Aware Seat Recommendation**

Non utilizza Machine Learning complesso, ma un approccio **rule-based con scoring**, facilmente spiegabile e dimostrabile in sede d’esame.

### 📊 Calcolo dello score

Ogni posto riceve uno score calcolato come:

```
score =
  (occupancy_probability * 0.4)
+ (comfort_score * 0.3)
- (energy_cost * 0.3)
```

#### 1️⃣ Occupancy Probability

Probabilità che la stanza venga occupata in quello specifico periodo, calcolata dallo storico delle prenotazioni:
- stesso giorno della settimana
- stessa fascia oraria
- stesso periodo dell’anno

```
prenotazioni_passate / slot_totali
```

#### 2️⃣ Comfort Score

Stima del comfort ambientale basata su:
- temperatura media storica
- esposizione al sole della stanza
- stagione

Una stanza troppo calda in estate o troppo fredda in inverno avrà uno score più basso.

#### 3️⃣ Energy Cost

Stima euristica del costo energetico:
- stanza vuota → costo alto
- stanza già occupata → costo basso

Il sistema preferisce concentrare gli studenti nelle stanze già attive.

---

## 👤 Ruoli utente

- **Student**: prenotazione posti e visualizzazione suggerimenti
- **Staff/Admin**: monitoraggio stanze, temperatura, consumo energetico
- **System**: gestione automatica (rilasci, suggerimenti, comandi energia)

---

## 📬 Notifiche

Le notifiche asincrone avvengono tramite email e possono essere inviate in caso di:
- rilascio automatico di un posto
- modifiche alla prenotazione
- avvisi di sistema

---

## 🚀 Avvio del progetto

### 1️⃣ Clona il repository

```bash
git clone https://github.com/your-username/smart-library-seat-tracker.git
```

### 2️⃣ Ambiente virtuale

```bash
py -3.12 -m venv IoT_env
IoT_env\Scripts\activate
pip install -r requirements.txt
```

---

## 🗄️ Database

Il database è **SQLite**.

Per visualizzarlo:
1. Apri **DBeaver**
2. File → Apri file → seleziona `iot.db`
3. Espandi lo schema → Diagramma per vedere le relazioni

⚠️ **ATTENZIONE**

Se modifichi i model SQLAlchemy:
- elimina il file `iot.db`
- riavvia il progetto

Il database verrà ricreato automaticamente.

(Alembic non è utilizzato per semplicità.)

---

## 📈 Stato del progetto

- Implementate le entità dei Digital Twin
- Tabelle di lettura e di comando energetico
- Sistema di suggerimento basato su scoring
- Architettura pronta per estensioni future (ML reale, dashboard avanzate)

---

## 📚 Contesto accademico

Il progetto è pensato per essere **esposto e spiegato** durante un esame universitario, dimostrando:
- capacità di progettazione architetturale
- integrazione IoT–Backend
- uso consapevole dei Digital Twin
- approccio sostenibile ed energeticamente efficiente

---

## ✨ Estensioni future

- Integrazione Machine Learning reale
- Simulazione avanzata dei sensori
- Ottimizzazione multi-obiettivo
- Analisi predittiva a lungo termine

---

📖 *Smart Library Digital Twin System – Università*

