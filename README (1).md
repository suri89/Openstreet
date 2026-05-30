# 🗺️ Competitor Finder

Find all nearby competitors by **search term**, **location**, and **radius** — powered by OpenStreetMap. Free, no API key needed.

## ✨ Features

- 🔍 Natural language search — type "dentist near me" or "pharmacy near Hyderabad"
- 📍 Auto GPS detection when you type "near me"
- 📏 Adjustable radius (1–200 miles)
- 🗺️ Interactive map with all results pinned
- 📋 Sorted list with name, distance, phone, website
- 📥 Download results as CSV
- 🗑️ Clear Memory button — frees RAM instantly
- 🔄 Auto memory clear on every tab refresh

## 🚀 Run Locally

```bash
git clone https://github.com/YOUR_USERNAME/competitor-finder.git
cd competitor-finder
pip install -r requirements.txt
streamlit run app.py
```

## ☁️ Deploy on Streamlit Community Cloud (Free)

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click **New app**
4. Select your repo → branch `main` → file `app.py`
5. Click **Deploy** — done!

## 🔍 Supported Search Terms

| You type | Finds |
|---|---|
| `dentist near me` | All dental clinics nearby (GPS) |
| `pharmacy near Hyderabad` | Pharmacies in Hyderabad |
| `gym` | Fitness centres (manual location) |
| `hospital` | Hospitals |
| `restaurant` | Restaurants |
| Any keyword | Name-based search |

## 🧠 Memory Management

- Every tab refresh **automatically clears** session memory
- The **🗑️ Clear Memory** button wipes cache + RAM manually
- Footer shows live session key count

## 📦 Tech Stack

- [Streamlit](https://streamlit.io) — UI
- [OpenStreetMap Overpass API](https://overpass-api.de) — Map data
- [Folium](https://python-visualization.github.io/folium/) — Interactive map
- [Geopy](https://geopy.readthedocs.io) — Geocoding
- [streamlit-js-eval](https://github.com/aghasemi/streamlit_js_eval) — Browser GPS

## 📄 License

MIT — free to use and modify.
