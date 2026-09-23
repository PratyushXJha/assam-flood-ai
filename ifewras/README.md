# FloodCast AI — Flood Early Warning, Forecasting & Rescue Allocation
**Smart India Hackathon 2026 | Problem Statement: IH260071 + SIH260192 (Merged)**
**Designed for: Assam State Disaster Management Authority (ASDMA) & SDRF Assam**

---

## 🌊 Overview

Assam's flood crisis is a multi-stage cascade: intense rainfall in upstream hill catchments (Arunachal Pradesh, Meghalaya, Karbi Anglong) surges into the Brahmaputra and Barak river corridors, inundating downstream plains and char (river island) communities with little warning.

**FloodCast AI** follows the flood from upstream cloudburst detection to last-mile resident alerts and rescue dispatch in three stages:

```
┌───────────────────────────┐      ┌───────────────────────────┐      ┌───────────────────────────┐
│ Stage 1: Watch the Hills  │ ───▶ │ Stage 2: Predict Plains   │ ───▶ │ Stage 3: Help the People  │
├───────────────────────────┤      ├───────────────────────────┤      ├───────────────────────────┤
│ • GPM-IMERG Satellite     │      │ • CWC River Gauges        │      │ • Explainable AI Risk     │
│ • Hill Catchment Flow     │      │ • 24h / 48h / 72h Forecast│      │ • Red / Yellow / Green    │
│ • Soil Moisture Saturation│      │ • DEM Bathtub Flood Fill  │      │ • Constrained Boat Alloc  │
│ • 3–6 hr Advance Triggers │      │ • Village Depth & Roads   │      │ • SMS + AI Voice Alerts   │
└───────────────────────────┘      └───────────────────────────┘      └───────────────────────────┘
```

---

## ✨ What's new in FloodCast AI 2.0

| Feature | How it works |
| :--- | :--- |
| **Separate pages** | The control centre is split into **Dashboard**, **Map & Zones**, **Forecast**, **Relief**, **Alerts** and **Settings** (hash routes like `#/map`) instead of one crowded screen. |
| **Working Play button** | Play steps through the 72-hour dataset (`backend/app/data/assam_72h_dataset.csv`, 73 hourly rows). For each hour the server runs the full Stage 1 → 2 → 3 pipeline (`POST /api/v1/simulation/compute/{hour}`) and the map, KPIs and charts redraw from the computed result. Gauge forecasts use the rise rate observed over the previous 6 hours of data. You can load your own CSV in Settings. |
| **Red-zone popups** | Each flood zone is graded RED / YELLOW / GREEN. Only a zone that *newly* turns RED raises a popup, centred on the map at that zone. Yellow and green zones never pop up. On other pages a small toast links to the map. |
| **Buzzer alarms** | A synthesised buzzer (Web Audio, no files) sounds in the control centre when a zone turns red or an alert is sent, and on the resident device (`/receiver`) when an alert arrives. |
| **Short multilingual alerts** | Every alert is generated in **English, Hindi and Assamese**. English fits one SMS (≤160 chars). Hindi and Assamese fit two Unicode SMS parts (≤134 chars). |
| **Throttled SMS** | Messages are queued and sent one at a time at a low, steady rate (default 30 SMS/min and 6 calls/min), with retries and backoff, so carriers don't rate-limit or block the sender. Rates are adjustable in Settings. |
| **AI assistant** | A chat assistant (robot button, bottom-right on every page, or **AI briefing** on the Dashboard) answers plain-language questions about the live situation: overview, red zones, any village or district, river levels and forecasts, hill rainfall, boats and reserves, alert delivery, next steps and helplines. It accepts English, Hindi and Assamese, supports voice input and can read answers aloud. |
| **AI voice calls** | Critical (red) alerts also place an automated call that reads: *"There will be a flood in your area… Please evacuate and proceed to the nearest relief centre."* Scripts exist in English, Hindi and Assamese. |

### AI assistant: Claude or built-in NLP
The assistant always works offline with a built-in NLP engine (keyword intent classification plus fuzzy village and district matching, in English, Hindi and Assamese). Set `ANTHROPIC_API_KEY` to have **Claude** (`claude-opus-5`) answer instead. Claude answers by calling read-only tools over the live data (`backend/app/assistant/tools.py`), so every number comes from the computed state. If Claude is unreachable, the assistant falls back to the built-in engine automatically. Options: `ASSISTANT_MODE=offline|claude`, `ASSISTANT_MODEL`, `ASSISTANT_EFFORT` (default `medium`). The assistant can only read data; it never sends alerts or changes settings.

### Real SMS and voice calls (optional)
By default FloodCast AI runs in **simulated (dry-run)** mode, and alerts go to demo recipients. To send real messages:

1. Set `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN` and `TWILIO_FROM_NUMBER`.
2. Create `backend/app/data/recipients.csv` with columns `phone,village_id,language` (phone in E.164 form, e.g. `+91…`; language `english` / `hindi` / `assamese`).

Voice calls use Twilio `<Say>` with Google `en-IN` and `hi-IN` voices. Twilio has no Assamese voice, so Assamese scripts are read by the Bengali `bn-IN` voice, which uses the same script. You can override the voices with `VOICE_EN`, `VOICE_HI` and `VOICE_AS`. Send rates can also be set with `SMS_PER_MINUTE` and `CALLS_PER_MINUTE`.

---

## 🚀 Quickstart

### Prerequisites
- Python 3.10+ (FastAPI, Uvicorn, NumPy)

### Launch the control centre and API
```powershell
pip install -r requirements.txt
python run_server.py
```

- **Control centre:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Resident device view:** [http://127.0.0.1:8000/receiver](http://127.0.0.1:8000/receiver). Open it on a phone, pick a location and language, and tap *Turn on alerts*.
- **Swagger API docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Demo in 30 seconds
1. Open the control centre and the `/receiver` page (tap *Turn on alerts* there).
2. Press **Play**. Zones start turning red from about T+36h.
3. The control centre buzzes and a red-zone popup opens on the map. SMS and voice calls queue at the throttled rate (see **Alerts**).
4. The resident device buzzes, shows the SMS in its language and plays the AI voice message.

---

## 🧪 Running tests
```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

To regenerate the 72-hour dataset from the calibrated historical anchors:
```powershell
python scripts/generate_72h_dataset.py
```

---

## 📐 Pipeline

### Stage 1: Watch the Hills (Upstream Trigger Detection)
- **Catchments monitored:** Siang/Upper Brahmaputra, Subansiri, Lohit & Dibang, Jia Bharali/Kameng, Kopili/Meghalaya Escarpment, Manas-Beki, Barak Headwaters.
- **Runoff physics:**
  $$Q = \frac{C_{\text{eff}} \times I \times A}{3.6}$$
  where antecedent soil saturation (>75%) magnifies the runoff coefficient $C_{\text{eff}}$ by up to 1.45×.

### Stage 2: Predict the Plains
- **CWC river gauges:** Dibrugarh, Nematighat (Majuli), Tezpur, Pandu (Guwahati), Goalpara, Dhubri, Silchar.
- **Hydrograph routing:** 24h, 48h and 72h water levels from the upstream surge plus the observed trend (backtest $R^2 = 0.94$, RMSE = $0.14\text{m}$ at 24h).
- **DEM flood fill:** village depths, flood extent and submerged roads.

### Stage 3: Help the People
- **Explainable risk score:**
  $$\text{Risk} = \left[ 0.40 \cdot D_{\text{depth}} + 0.30 \cdot V_{\text{vuln}} + 0.30 \cdot I_{\text{isolation}} \right] \times P_{\text{pop\_scale}}$$
- **Hazard zones:** a zone is **RED** if it contains a P1 (extreme-risk) village or the bank is overtopped by ≥1.5 m, **YELLOW** if water is above the bank, and **GREEN** otherwise.
- **Relief allocation:** matches finite SDRF/NDRF boats, medical teams and relief kits down the risk ranking.
- **Alerts:** short SMS plus an AI voice call in English, Hindi and Assamese, sent through the throttled dispatcher.

---

## 🔌 Key API endpoints

| Method | Path | Purpose |
| :--- | :--- | :--- |
| POST | `/api/v1/simulation/compute/{hour}` | Run the pipeline on dataset hour 0–72 |
| GET / POST | `/api/v1/simulation/dataset` | Describe or upload (raw CSV body) the 72-hour dataset |
| GET | `/api/v1/simulation/dataset/template` | Download the built-in dataset CSV |
| GET | `/api/v1/stage3/zones` | Red / yellow / green hazard zones |
| POST | `/api/v1/alerts/dispatch` | Queue SMS + voice alerts for a `zone_id` or `village_ids` |
| GET | `/api/v1/alerts/dispatch/status` | Queue depth, sent/failed counts, delivery log |
| GET / PUT | `/api/v1/alerts/settings` | SMS / call send rate and retry policy |
| GET | `/api/v1/alerts/feed?since=` | Alerts for resident devices |
| POST | `/api/v1/assistant/chat` | Ask the AI assistant (`{"message": "...", "history": [...]}`) |
| GET | `/api/v1/assistant/status` | Assistant mode (Claude or built-in NLP) and suggested questions |

---

## 📂 Project structure

```
ifewras/
├── backend/app/
│   ├── config.py              # Geo bounds, thresholds, voice locales, dispatch rates
│   ├── main.py                # FastAPI app, static pages, dispatcher lifecycle
│   ├── data/                  # 72-hour telemetry dataset (CSV)
│   ├── stage1_hills/          # Upstream catchment & trigger engine
│   ├── stage2_plains/         # Gauge forecasts, DEM extent, villages & roads
│   ├── stage3_relief/         # Risk, access, allocation, zones & multilingual alerts
│   ├── alerts/dispatcher.py   # Throttled SMS + AI voice-call queue (Twilio or simulated)
│   ├── assistant/             # AI assistant: situation tools, Claude tool loop, offline NLP
│   ├── scenarios/             # Dataset loader & hour-by-hour pipeline manager
│   └── api/                   # REST routes
├── frontend/static/
│   ├── index.html             # Control centre (Dashboard, Map, Forecast, Relief, Alerts, Settings)
│   ├── receiver.html          # Resident device view
│   └── js/                    # app, map, alerts, settings, sound, receiver, assistant
├── scripts/generate_72h_dataset.py
├── tests/
└── run_server.py
```
