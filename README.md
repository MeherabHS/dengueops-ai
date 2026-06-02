# DengueOps AI

### Simulation-Based Dengue Surge Preparedness Decision Support for Dhaka South

> **IEEE ICADHI 2025 — Track 06: Health Data Analytics & Predictive Systems**

---

## The Problem

Dengue response in Dhaka South has historically been reactive. By the time a hospital runs out of NS1 test kits or a ward fills its dengue beds, the surge has already arrived. There is no operational layer that converts outbreak forecasts into preparedness signals — no tool telling a health officer *where* the next pressure will emerge, *how long* supplies will last, or *which zone* needs vector-control teams first.

**DengueOps AI is built for that gap.**

---

## What It Does

DengueOps AI is a **simulation-based public health decision-support prototype**. It ingests dengue case trends and climate signals, runs a lag-aware machine learning forecast, and translates the output into a set of operational preparedness metrics:

| Output | What it answers |
|--------|----------------|
| **Uncertainty Scenarios** | How many cases should we plan for — best, expected, worst? |
| **Supply Depletion Horizon (SDH)** | How many days before NS1 kits or IV fluids run out? |
| **LOS-Based Bed Pressure** | How many dengue beds will be occupied? Where is the gap? |
| **Zone Priority Score** | Which of the five operational zones needs attention most urgently? |
| **Operational Directives** | What action should each zone and facility take right now? |
| **Surge Simulation** | What would happen if a specific area surged by 25–40%? |

Everything is surfaced through an interactive dashboard — not a spreadsheet, not a terminal. A dashboard that a public health analyst, hospital administrator, or city health officer can actually read and act on.

---

## Why It Is Different

Most dengue dashboards stop at case counts and trend lines. DengueOps AI goes further:

- **Forecast → preparedness translation.** The ML forecast is not the product. The operational directives derived from it are.
- **Uncertainty is shown, not hidden.** Every forecast is presented as three scenarios (best/expected/worst) built from validation RMSE.
- **Role-based outputs.** A hospital administrator sees bed gaps and SDH. A public health analyst sees zone priorities. A technical evaluator sees MAE, RMSE, and feature importance. The same data, presented appropriately.
- **Scenario simulation.** Five surge scenarios let planners rehearse response before a crisis, not during one.
- **Transparent by design.** Every assumption, limitation, and ethical boundary is documented and displayed in the app itself.

---

## Live Routes

| Route | Purpose |
|-------|---------|
| `/` | Landing page — problem, solution, workflow, roles |
| `/dashboard` | Main operational dashboard |
| `/methodology` | Full technical documentation — formulas, pipeline, logic |
| `/validation` | Model evidence — backtesting, MAE/RMSE/MAPE, AVP charts |
| `/ethics` | Ethical design principles and data boundaries |
| `/assumptions` | All assumptions, limitations, and future validation roadmap |
| `/about` | Project overview and authors |

---

## Quick Start

**Requirements:** Node.js 18+, Python 3.10+

```bash
# 1. Install dependencies
npm install
pip install -r requirements.txt

# 2. Run the analytics pipeline
#    Default: uses controlled synthetic Dhaka South demo data (2024–2026)
python analytics/run_pipeline.py

# 3. Start the dashboard
npm run dev
```

**Optional real-data pathways (experimental — not the active demo mode)**

```bash
# Replace synthetic dengue_cases.csv with real OpenDengue Bangladesh national data
python analytics/run_pipeline.py --use-opendengue

# Replace synthetic climate_data.csv with NASA POWER data
python analytics/run_pipeline.py --use-nasa-power-climate

# Use both real data sources
python analytics/run_pipeline.py --use-opendengue --use-nasa-power-climate
```

Open [http://localhost:3000](http://localhost:3000)

> The Python pipeline generates JSON outputs in `data/`. The Next.js dashboard reads those files. The terminal output is not the product — the dashboard is.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16, App Router |
| Language | TypeScript |
| Styling | Tailwind CSS |
| Charts | Recharts |
| Icons | Lucide React |
| Analytics | Python — Pandas, NumPy, Scikit-learn |
| Data | Static JSON (pipeline output) |

---

## Key Formulas at a Glance

```
Growth Factor         = Forecast Cases / 4-Week Rolling Average

Risk Score            = Piecewise linear scale (0–100) from growth factor

SDH                   = Current Stock / Dynamic Daily Demand

Projected Bed Load    = Current Dengue Beds Occupied + (Daily Surge Cases × Avg LOS)

Bed Gap               = Projected Bed Load − Available Dengue Beds

Exposure Index        = Population × 0.40 + Density × 0.30 + Facility Pressure × 0.20 + Mobility × 0.10

Priority Score (0–100) = structural + forecast_driven
                        structural     = exposure × vulnerability × 200 + exposure × 80
                        forecast_driven = risk_score × (0.60 + vulnerability × 0.30)
                        Categories: 0–25 Routine, 26–50 Moderate, 51–75 High, 76–100 Critical

Uncertainty Band      = Best: max(0, Forecast − RMSE)
                        Expected: Forecast
                        Worst: Forecast + RMSE
```

---

## Data Transparency

The active demonstration uses **controlled weekly Dhaka South synthetic/demo data** to test the forecast-to-preparedness workflow. OpenDengue and NASA POWER integration are retained as optional future real-data validation pathways, but they are not the default demonstration dataset.

| Data Layer | Source | Status |
|-----------|--------|--------|
| Dengue case data | **Synthetic/demo** — `generate_demo_data.py` | Controlled weekly Dhaka South pattern, 2024–2026. Seasonal surge + early 2026 warning. |
| Climate data | **Synthetic/demo** — `generate_demo_data.py` | Weekly rainfall, temperature, humidity. Aligned to 2024–2026 dengue period for lagged features. |
| Facility names | Public anchor | Real public hospital names as credible location anchors |
| Bed capacity (general) | Public reference | General published figures only |
| Dengue beds, stock, occupancy | Synthetic demonstration | Not real operational data |
| Patient-level records | Not used, not stored | — |

**Optional real-data integration (experimental — not active by default):**

| Optional Source | Flag | Coverage |
|----------------|------|----------|
| OpenDengue V1.3 (Clarke et al. 2024, *Sci Data*) | `--use-opendengue` | Bangladesh national, 2014–2024 |
| NASA POWER (meteorological API) | `--use-nasa-power-climate` | Dhaka South, configurable date range |

---

## Authors

**Meherab Hossain Shafin**
Department of Software Engineering, Daffodil International University

**Jannatul Tazri Aohona**
Department of Software Engineering, Daffodil International University

---

## Important Disclaimers

- This is a **prototype** — not a validated clinical or operational system
- All outputs are **advisory** — human review is required before any action
- The system does **not diagnose dengue** or recommend individual treatment
- Real deployment requires official data, institutional approval, and validation

---

## Documentation

Full technical documentation is in [`docs/DOCUMENTATION.md`](docs/DOCUMENTATION.md)

| Doc | Contents |
|-----|---------|
| `docs/DOCUMENTATION.md` | Complete technical, architectural, and user documentation |
| `docs/GUIDELINE.md` | Story-based user guide for non-technical readers |
| `docs/ASSUMPTIONS_AND_LIMITATIONS.md` | Detailed assumption disclosures |
| `data/README.md` | Data directory and schema reference |

---

*For research and educational demonstration purposes only.
Not for clinical or operational deployment without validated data and institutional oversight.*
