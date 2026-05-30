import streamlit as st
import requests
import pandas as pd
import math
import folium
import gc
import re
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from streamlit_js_eval import get_geolocation

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Competitor Finder",
    page_icon="🗺️",
    layout="wide"
)

# ─────────────────────────────────────────────
# AUTO-CLEAR ON FRESH TAB LOAD
# Every time page loads fresh (no session yet), wipe everything
# ─────────────────────────────────────────────
if "session_initialized" not in st.session_state:
    # This is a brand new tab load — clear everything
    st.session_state.clear()
    st.cache_data.clear()
    gc.collect()
    st.session_state["session_initialized"] = True

# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; }
    .main-title { font-size: 2.2rem; font-weight: 700; color: #1a1a2e; }
    .sub-title  { font-size: 1rem; color: #666; margin-bottom: 1.5rem; }
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; border: none; border-radius: 8px;
        padding: 0.6rem 1.5rem; font-weight: 600;
        width: 100%; transition: opacity 0.2s;
    }
    .stButton > button:hover { opacity: 0.85; color: white; }
    .clear-btn > button {
        background: linear-gradient(135deg, #ff6b6b, #ee5a24) !important;
    }
    .result-card {
        background: #f8f9ff; border-left: 4px solid #667eea;
        border-radius: 8px; padding: 1rem 1.2rem; margin-bottom: 0.8rem;
    }
    .result-name   { font-weight: 700; font-size: 1.05rem; color: #1a1a2e; }
    .result-detail { font-size: 0.88rem; color: #555; margin-top: 0.2rem; }
    .badge {
        display: inline-block; background: #667eea22; color: #667eea;
        border-radius: 20px; padding: 2px 10px; font-size: 0.78rem; font-weight: 600;
    }
    .near-me-banner {
        background: #e8f4fd; border: 1px solid #90caf9;
        border-radius: 8px; padding: 0.7rem 1rem;
        font-size: 0.9rem; color: #1565c0; margin-bottom: 1rem;
    }
    .ram-status {
        background: #f0fff4; border: 1px solid #68d391;
        border-radius: 8px; padding: 0.5rem 1rem;
        font-size: 0.85rem; color: #276749;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# OSM TAG MAP
# ─────────────────────────────────────────────
OSM_TAG_MAP = {
    "dentist":       ("amenity", "dentist"),
    "dental":        ("amenity", "dentist"),
    "pharmacy":      ("amenity", "pharmacy"),
    "hospital":      ("amenity", "hospital"),
    "clinic":        ("amenity", "clinic"),
    "doctor":        ("amenity", "doctors"),
    "gym":           ("leisure", "fitness_centre"),
    "fitness":       ("leisure", "fitness_centre"),
    "restaurant":    ("amenity", "restaurant"),
    "cafe":          ("amenity", "cafe"),
    "coffee":        ("amenity", "cafe"),
    "hotel":         ("tourism", "hotel"),
    "school":        ("amenity", "school"),
    "bank":          ("amenity", "bank"),
    "supermarket":   ("shop", "supermarket"),
    "optician":      ("shop", "optician"),
    "veterinary":    ("amenity", "veterinary"),
    "physiotherapy": ("amenity", "physiotherapist"),
}

# ─────────────────────────────────────────────
# MEMORY CLEAR FUNCTION
# ─────────────────────────────────────────────
def clear_all_memory():
    """Clears session state, cache, and forces garbage collection."""
    st.session_state.clear()
    st.cache_data.clear()
    gc.collect()
    # Re-initialize so the app doesn't loop
    st.session_state["session_initialized"] = True
    st.session_state["memory_cleared"] = True

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def parse_search_term(raw):
    text = raw.strip().lower()
    match_in = re.search(r"(.+?)\s+near\s+me\s+in\s+(.+)", text)
    if match_in:
        return match_in.group(1).strip(), False, match_in.group(2).strip()
    match_me = re.search(r"(.+?)\s+near\s+me", text)
    if match_me:
        return match_me.group(1).strip(), True, None
    match_loc = re.search(r"(.+?)\s+near\s+(.+)", text)
    if match_loc:
        return match_loc.group(1).strip(), False, match_loc.group(2).strip()
    return text, False, None

@st.cache_data(show_spinner=False)
def geocode_address(address):
    geolocator = Nominatim(user_agent="competitor_finder_v2")
    try:
        loc = geolocator.geocode(address, timeout=10)
        if loc:
            return loc.latitude, loc.longitude, loc.address
    except Exception:
        pass
    return None, None, None

@st.cache_data(show_spinner=False)
def reverse_geocode(lat, lon):
    geolocator = Nominatim(user_agent="competitor_finder_v2")
    try:
        loc = geolocator.reverse(f"{lat}, {lon}", timeout=10)
        if loc:
            return loc.address
    except Exception:
        pass
    return f"{lat:.4f}, {lon:.4f}"

def miles_to_meters(miles):
    return miles * 1609.34

def haversine_miles(lat1, lon1, lat2, lon2):
    R = 3958.8
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat/2)**2
         + math.cos(math.radians(lat1))
         * math.cos(math.radians(lat2))
         * math.sin(dlon/2)**2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def get_osm_tag(keyword):
    kw = keyword.lower().strip()
    for k, tag in OSM_TAG_MAP.items():
        if k in kw:
            return tag
    return None

@st.cache_data(show_spinner=False)
def fetch_competitors(lat, lon, keyword, radius_miles):
    radius_m = miles_to_meters(radius_miles)
    osm_tag  = get_osm_tag(keyword)
    if osm_tag:
        k, v = osm_tag
        query = f"""
        [out:json][timeout:30];
        (
          node["{k}"="{v}"](around:{radius_m},{lat},{lon});
          way["{k}"="{v}"](around:{radius_m},{lat},{lon});
        );
        out center tags;
        """
    else:
        query = f"""
        [out:json][timeout:30];
        (
          node["name"~"{keyword}",i](around:{radius_m},{lat},{lon});
          way["name"~"{keyword}",i](around:{radius_m},{lat},{lon});
        );
        out center tags;
        """
    try:
    resp = requests.post(
        "https://overpass.kumi.systems/api/interpreter",
        data=query,
        timeout=35,
        headers={
            "Accept": "application/json",
            "User-Agent": "CompetitorFinder/1.0"
        }
    )

    resp.raise_for_status()
    data = resp.json()

except Exception as e:
    return [], str(e))

    results = []
    for el in data.get("elements", []):
        tags = el.get("tags", {})
        name = tags.get("name", "").strip()
        if not name:
            continue
        if el["type"] == "node":
            el_lat, el_lon = el.get("lat"), el.get("lon")
        else:
            center = el.get("center", {})
            el_lat, el_lon = center.get("lat"), center.get("lon")
        if not el_lat or not el_lon:
            continue
        dist    = haversine_miles(lat, lon, el_lat, el_lon)
        street  = tags.get("addr:street", "")
        city    = tags.get("addr:city", "")
        address = f"{street}, {city}".strip(", ") or "N/A"
        results.append({
            "Name":             name,
            "Address":          address,
            "Phone":            tags.get("phone", tags.get("contact:phone", "N/A")),
            "Website":          tags.get("website", tags.get("contact:website", "N/A")),
            "Opening Hours":    tags.get("opening_hours", "N/A"),
            "Distance (miles)": round(dist, 2),
            "lat":              el_lat,
            "lon":              el_lon,
        })
    results.sort(key=lambda x: x["Distance (miles)"])
    return results, None

def build_map(center_lat, center_lon, results, radius_miles):
    m = folium.Map(location=[center_lat, center_lon], zoom_start=12, tiles="CartoDB positron")
    folium.Marker(
        [center_lat, center_lon],
        popup="📍 Your Location",
        tooltip="Your Location",
        icon=folium.Icon(color="blue", icon="home", prefix="fa")
    ).add_to(m)
    folium.Circle(
        location=[center_lat, center_lon],
        radius=radius_miles * 1609.34,
        color="#667eea", fill=True, fill_opacity=0.06, weight=1.5
    ).add_to(m)
    for r in results:
        popup_html = f"""
        <b>{r['Name']}</b><br>
        📍 {r['Address']}<br>📞 {r['Phone']}<br>
        🌐 {r['Website']}<br>📏 {r['Distance (miles)']} miles
        """
        folium.CircleMarker(
            location=[r["lat"], r["lon"]],
            radius=7, color="#764ba2", fill=True,
            fill_color="#667eea", fill_opacity=0.8,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=r["Name"]
        ).add_to(m)
    return m

# ─────────────────────────────────────────────
# HEADER ROW — Title + Clear Memory Button
# ─────────────────────────────────────────────
title_col, spacer, clear_col = st.columns([3, 2, 1])

with title_col:
    st.markdown('<div class="main-title">🗺️ Competitor Finder</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Type naturally — "dentist near me", "pharmacy near Hyderabad", or just "gym"</div>', unsafe_allow_html=True)

with clear_col:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="clear-btn">', unsafe_allow_html=True)
    if st.button("🗑️ Clear Memory"):
        clear_all_memory()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# Show cleared confirmation
if st.session_state.get("memory_cleared"):
    st.success("✅ Memory cleared — RAM freed & cache wiped!")
    del st.session_state["memory_cleared"]

st.divider()

# ─────────────────────────────────────────────
# INPUTS
# ─────────────────────────────────────────────
col1, col2, col3 = st.columns([2.5, 2, 1])
with col1:
    raw_search = st.text_input(
        "🔍 Search",
        placeholder="dentist near me  /  pharmacy near Banjara Hills  /  gym",
    )
with col2:
    location_input = st.text_input(
        "📍 Your Location (optional if using 'near me')",
        placeholder="Leave blank to auto-detect",
    )
with col3:
    radius_miles = st.number_input(
        "📏 Radius (miles)",
        min_value=1, max_value=200, value=10, step=5
    )

search_clicked = st.button("🔍 Find Competitors", type="primary")

# ─────────────────────────────────────────────
# SEARCH LOGIC
# ─────────────────────────────────────────────
if search_clicked and raw_search:

    keyword, needs_gps, inline_location = parse_search_term(raw_search)
    final_lat, final_lon, display_address = None, None, None

    if location_input.strip():
        with st.spinner("📍 Geocoding your location..."):
            final_lat, final_lon, display_address = geocode_address(location_input.strip())

    elif inline_location:
        with st.spinner(f"📍 Finding '{inline_location}'..."):
            final_lat, final_lon, display_address = geocode_address(inline_location)

    elif needs_gps:
        st.markdown("""
        <div class="near-me-banner">
            📡 <b>"near me"</b> detected — requesting your browser GPS location. Please allow access when prompted.
        </div>
        """, unsafe_allow_html=True)
        geo = get_geolocation()
        if geo and "coords" in geo:
            final_lat = geo["coords"]["latitude"]
            final_lon = geo["coords"]["longitude"]
            with st.spinner("Reverse geocoding..."):
                display_address = reverse_geocode(final_lat, final_lon)
        else:
            st.warning("⚠️ Could not get browser location. Please type your location manually.")

    else:
        st.warning("⚠️ Please enter a location or add 'near me' to your search.")

    if final_lat and final_lon:
        st.success(f"📍 {display_address}")
        st.info(f"🔎 Searching **{keyword}** within **{radius_miles} miles**...")

        results, error = fetch_competitors(final_lat, final_lon, keyword, radius_miles)

        if error:
            st.error(f"API Error: {error}")
        elif not results:
            st.warning("No results found. Try a broader term or increase the radius.")
        else:
            # Store in session so it survives reruns
            st.session_state["last_results"] = results
            st.session_state["last_keyword"] = keyword

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Found",  len(results))
            m2.metric("Nearest",      f"{results[0]['Distance (miles)']} mi")
            m3.metric("Avg Distance", f"{round(sum(r['Distance (miles)'] for r in results)/len(results),1)} mi")
            m4.metric("Have Phone",   sum(1 for r in results if r["Phone"] != "N/A"))

            st.markdown("<br>", unsafe_allow_html=True)
            map_col, list_col = st.columns([1.2, 1])

            with map_col:
                st.markdown("#### 🗺️ Map View")
                comp_map = build_map(final_lat, final_lon, results, radius_miles)
                st_folium(comp_map, width=None, height=480)

            with list_col:
                st.markdown(f"#### 📋 {len(results)} Results")
                for r in results[:15]:
                    phone = f"📞 {r['Phone']}" if r["Phone"] != "N/A" else ""
                    web   = f"🌐 {r['Website']}" if r["Website"] != "N/A" else ""
                    st.markdown(f"""
                    <div class="result-card">
                        <div class="result-name">{r['Name']}</div>
                        <div class="result-detail">
                            <span class="badge">📏 {r['Distance (miles)']} mi</span>
                            {r['Address']}
                        </div>
                        <div class="result-detail">{phone} &nbsp; {web}</div>
                    </div>
                    """, unsafe_allow_html=True)
                if len(results) > 15:
                    st.info(f"Showing top 15. Download CSV for all {len(results)}.")

            df_export = pd.DataFrame(results).drop(columns=["lat", "lon"])
            st.download_button(
                label=f"📥 Download All {len(results)} as CSV",
                data=df_export.to_csv(index=False),
                file_name=f"{keyword}_competitors.csv",
                mime="text/csv"
            )

elif search_clicked:
    st.warning("⚠️ Please enter a search term.")

# ─────────────────────────────────────────────
# FOOTER RAM STATUS
# ─────────────────────────────────────────────
st.divider()
session_keys = len(st.session_state.keys())
st.markdown(f"""
<div class="ram-status">
    🟢 Session active &nbsp;|&nbsp; 
    Keys in memory: <b>{session_keys}</b> &nbsp;|&nbsp;
    Hit <b>🗑️ Clear Memory</b> to free RAM &nbsp;|&nbsp;
    Refreshing the tab also clears memory automatically
</div>
""", unsafe_allow_html=True)
