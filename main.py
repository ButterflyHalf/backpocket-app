import streamlit as st
import requests
import os
import base64
from datetime import datetime

# --- 1. CONFIG & SETTINGS ---
# This must be the very first Streamlit command in your script
st.set_page_config(
    page_title="Lowest Priced Ford Expedition Austin",
    page_icon="🚗",
    layout="wide"
)

# Inject the Impact.com verification tag into the <head>
st.markdown(
    f"""
    <script>
        var meta = document.createElement('meta');
        meta.name = "impact-site-verification";
        meta.content = "9c4dc491-549c-4de6-98ea-84d662dbce49";
        document.getElementsByTagName('head')[0].appendChild(meta);
    </script>
    """,
    unsafe_allow_html=True
)

# Hide the top bar and the "Made with Streamlit" footer
hide_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """
st.markdown(hide_style, unsafe_allow_html=True)

API_KEY = os.environ.get("MARKETCHECK_API_KEY")
REVIEW_FILE = "reviews.txt"
RADIUS = "100"

# --- 2. SEED INITIAL DATA ---
if not os.path.exists(REVIEW_FILE):
    with open(REVIEW_FILE, "w") as f:
        f.write(f"2026-04-24|Austin J.|Ford Expedition|8000.0|Using the data from BackPocket changed the entire vibe of the deal. I walked in with the Market Floor data and saved $7k on the purchase and another $1k on trade. Felt like I had an action plan instead of just hoping for the best.\n")

# --- 3. SESSION STATE ---
if 'page' not in st.session_state:
    st.session_state.page = "home"
if 'search_results' not in st.session_state:
    st.session_state.search_results = None

# --- 4. STYLING (CSS) ---
st.markdown("""
    <style>
    div.stButton > button {
        background: none !important; border: none !important; padding: 0 !important;
        color: #555 !important; text-decoration: underline !important;
        font-weight: 600 !important; font-size: 16px !important; box-shadow: none !important;
    }
    div.stButton > button:hover { color: #000 !important; background: none !important; }
    .block-container { padding-top: 1.5rem !important; }
    
    .car-card {
        background-color: white; 
        padding: 20px; 
        border-radius: 12px;
        border: 1px solid #eee; 
        box-shadow: 2px 2px 12px rgba(0,0,0,0.06);
        height: 550px; 
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        margin-bottom: 20px;
    }
    
    .car-image-container {
        height: 180px;
        overflow: hidden;
        border-radius: 8px;
        margin-bottom: 15px;
    }
    
    .car-image-container img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }

    .review-card {
        background-color: #f9f9f9; padding: 20px; border-radius: 10px;
        border-left: 5px solid #333; margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 5. TOP NAVIGATION ---
pages = [("BACKPOCKET", "home"), ("SEARCH ENGINE", "engine"), ("NEGOTIATION GUIDE", "guide"), ("SUCCESS STORIES", "reviews")]
# Changed to equal column weights to ensure equal spacing
nav_cols = st.columns(len(pages) + 1) 

for i, (label, pg) in enumerate(pages):
    if nav_cols[i].button(label, key=f"nav_{pg}"):
        st.session_state.page = pg
        st.rerun()
st.divider()

# --- 6. DATA ENGINE HELPERS ---
def get_clean_name(raw):
    if not raw: return ""
    fluff = [" Metallic", " Tri-Coat", " Tricoat", " Clearcoat", " Clear Coat", " Pearl", " Tintcoat"]
    for word in fluff: raw = raw.replace(word, "").replace(word.lower(), "")
    return raw.strip().title()

@st.cache_data(ttl=3600)
def get_options(field, user_zip, make=None, model=None, trim=None):
    url = "https://api.marketcheck.com/v2/search/car/active"
    actual_field = field
    if field == "exterior_color" and not model:
        actual_field = "base_exterior_color"
    
    params = {
        "api_key": API_KEY, 
        "car_type": "new", 
        "miles_range": "0-500", 
        "price_range": "1-500000",
        "zip": user_zip,
        "radius": RADIUS,
        "facets": actual_field, 
        "rows": 0
    }
    if make: params["make"] = make
    if model: params["model"] = model
    if trim: params["trim"] = trim
    try:
        res = requests.get(url, params=params).json()
        facet_list = res.get('facets', {}).get(actual_field, [])
        return {get_clean_name(i['item']): i['item'] for i in facet_list}
    except: return {}

# --- 7. PAGE: HOME ---
if st.session_state.page == "home":
    banner_path = "Banner.png"
    if os.path.exists(banner_path):
        with open(banner_path, "rb") as f:
            data = base64.b64encode(f.read()).decode("utf-8")
            st.markdown(f'<div style="background-image: url(\'data:image/png;base64,{data}\'); background-size: cover; background-position: center 60%; height: 180px; border-radius: 10px; margin-bottom: 10px;"></div>', unsafe_allow_html=True)
    
    # --- AUSTIN SEO HEADERS ---
    st.markdown("# Lowest Priced Ford Expedition near Austin, TX")
    st.markdown("### 2026 Price Audit & Trade-In Value Analysis")
    
    st.write("""
        Buying a Ford Expedition in Central Texas right now is tricky. With MSRPs 
        fluctuating and Austin dealers adding 'market adjustments,' you need to know 
        the real numbers. 
        
        **BackPocket** analyzes the latest data for Ford Expeditions in Austin, 
        Round Rock, and Georgetown to show you the actual 'Drive-Away' price.
    """)

    # --- AGGREGATOR BUSTER CONTENT ---
    with st.container():
        st.info("💡 **Austin Market Insight (April 2026):**")
        st.write("""
            * **Target Price:** Look for the 'Active' trim starting at **$62,700**.
            * **Dealer Warning:** Watch out for 'Ceramic Tint' or 'Pro-Pack' add-ons at local dealerships like Leif Johnson or Covert Ford (common $600-$1,200 hidden fees).
            * **The Savings:** Trading in your vehicle in Travis or Williamson County can save you up to **$5,000 in sales tax** on a new Expedition.
        """)

    st.divider()
    
    # ORIGINAL HOME PAGE PILLARS
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("### 🎯 Find the Anchor")
        st.write("The dealer's sticker price is an anchor meant to narrow your vision. We find the **Market Floor** so you can re-anchor the deal on your terms.")
    with c2:
        st.markdown("### 🏷️ Label the Reality")
        st.write("Identify hidden margins. We give you the data to label dealer behaviors: *'It seems like this price is based on scarcity that doesn't exist.'*")
    with c3:
        st.markdown("### 💎 The Cash Gap")
        st.write("Never negotiate the monthly payment. We calculate the **Cash Gap**—the only number that matters. If that number doesn't move, you walk.")
    _, center_col, _ = st.columns([1, 1.2, 1])
    if center_col.button("START YOUR NEGOTIATION", type="primary", use_container_width=True):
        st.session_state.page = "engine"; st.rerun()

# --- 8. PAGE: NEGOTIATION GUIDE ---
elif st.session_state.page == "guide":
    st.title("The BackPocket Playbook")
    st.write("### How the Game is Played (and how to win it)")
    
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("""
        #### 1. The Setup
        You walk in, find the car, and go for a test drive. The dealer is building **rapport** and **emotional attachment**. They want you to visualize that car in your driveway.
        
        #### 2. The 'Desk' Phase
        They take your keys to 'value your trade.' You are now stuck. They return with a four-square or a sheet showing:
        * **MSRP:** Their primary anchor.
        * **Markups:** 'Market adjustments' or 'Pro-packs.'
        * **Low-Ball Trade:** Often thousands of dollars below the actual floor.
        """)
    
    with col_r:
        st.markdown("""
        #### 3. The BackPocket Counter
        This is where you change the game. 
        * **Label the adjustment:** *"It seems like this 'Market Adjustment' is a way to see how much over the actual market price I'm willing to pay."*
        * **Use the Market Floor:** Show them the lowest listed price for that car within 100 miles. *"I've seen the floor for this trim. How am I supposed to pay $4k more than that?"*
        * **The Cash Gap:** Ignore the monthly payment. Focus only on: *(Target Car Price) - (Actual Trade Value)*.
        """)

    st.info("💡 **Pro Tip:** The person who talks less wins. After you ask a 'How' question, **wait for them to talk.** Let the silence do the work.")
    
    if st.button("READY? GO TO SEARCH"):
        st.session_state.page = "engine"
        st.rerun()

# --- 9. PAGE: SUCCESS STORIES ---
elif st.session_state.page == "reviews":
    st.title("Success Stories")
    if os.path.exists(REVIEW_FILE):
        for r in open(REVIEW_FILE).readlines()[::-1]:
            parts = r.strip().split("|")
            if len(parts) == 5:
                st.markdown(f'<div class="review-card"><div class="review-header">{parts[1]} saved ${float(parts[3]):,.0f}</div><div class="review-sub">Vehicle: {parts[2]} | Posted: {parts[0]}</div><div class="review-body">"{parts[4]}"</div></div>', unsafe_allow_html=True)

# --- 10. PAGE: SEARCH ENGINE ---
elif st.session_state.page == "engine":
    st.title("Search Engine")
    
    # 1. SEARCH FILTERS
    st.subheader("Step 1: Find the Market Floor")
    
    # Tightened Zip Code Field using columns
    z1, _ = st.columns([1, 5]) # 1/6th of the screen width
    with z1:
        user_zip = st.text_input("Zip Code", value="78642", max_chars=5)
    st.caption(f"Searching within {RADIUS} miles of {user_zip}")
    
    f1, f2, f3, f4 = st.columns(4)
    make_map = get_options("make", user_zip)
    make_sel = f1.selectbox("Vehicle Make", ["— Select All —"] + sorted(make_map.keys()))
    
    model_map = get_options("model", user_zip, make=make_map.get(make_sel)) if make_sel != "— Select All —" else {}
    model_sel = f2.selectbox("Vehicle Model", ["— Select All —"] + sorted(model_map.keys()))
    
    trim_map = get_options("trim", user_zip, make=make_map.get(make_sel), model=model_map.get(model_sel)) if model_sel != "— Select All —" else {}
    trim_sel = f3.selectbox("Vehicle Trim", ["— Select All —"] + sorted(trim_map.keys()))
    
    color_map = get_options("exterior_color", user_zip, make=make_map.get(make_sel), model=model_map.get(model_sel), trim=trim_map.get(trim_sel))
    color_sel = f4.selectbox("Paint Color", ["— Select All —"] + sorted(color_map.keys()))

    if st.button("See Results", type="primary", use_container_width=True):
        params = {"api_key": API_KEY, "car_type": "new", "miles_range": "0-500", "price_range": "1-500000", "zip": user_zip, "radius": RADIUS, "sort_by": "price", "rows": 3}
        if make_sel != "— Select All —": params["make"] = make_map[make_sel]
        if model_sel != "— Select All —": params["model"] = model_map[model_sel]
        if trim_sel != "— Select All —": params["trim"] = trim_map[trim_sel]
        if color_sel != "— Select All —": params["exterior_color" if model_sel != "— Select All —" else "base_exterior_color"] = color_map[color_sel]
        
        with st.spinner(f"Scanning within {RADIUS} miles of {user_zip}..."):
            res = requests.get("https://api.marketcheck.com/v2/search/car/active", params=params).json()
            st.session_state.search_results = res.get('listings', [])

    # 2. DISPLAY RESULTS
    if st.session_state.search_results:
        st.divider()
        st.markdown(f"### 🏆 Top {len(st.session_state.search_results)} Lowest Priced Matches")
        cols = st.columns(3)
        floor_price = st.session_state.search_results[0].get('price', 0)
        
        for idx, car in enumerate(st.session_state.search_results):
            with cols[idx]:
                img = car.get('media', {}).get('photo_links', [None])[0]
                img_html = f'<div class="car-image-container"><img src="{img}"></div>' if img else '<div class="car-image-container" style="background:#eee;display:flex;align-items:center;justify-content:center;">No Photo</div>'
                
                st.markdown(f"""
                    <div class="car-card">
                        <div>
                            {img_html}
                            <h2 style="margin:0;">${car.get('price', 0):,}</h2>
                            <p style="color:#666;font-size:0.9rem;margin-bottom:10px;">{car.get('miles', 0)} miles</p>
                            <p><b>{car.get('heading')}</b></p>
                            <p style="font-size:0.9rem;">🏢 {car.get('dealer', {}).get('name')}<br>
                            📍 {car.get('dealer', {}).get('city')}, {car.get('dealer', {}).get('state')}<br>
                            📏 {car.get('dist', 0)} miles away</p>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                st.link_button("View Listing", car.get('vdp_url'), use_container_width=True)

        # 3. TRADE-IN & CALCULATOR
        st.divider()
        st.subheader("Step 2: Value Your Trade & Cash Gap")
        tc1, tc2 = st.columns(2)
        with tc1:
            trade_val = st.number_input("Estimated Trade-In Value ($)", value=0, step=500)
            st.link_button("KBB Baseline", "https://www.kbb.com/whats-my-car-worth/", use_container_width=True)
            st.link_button("CarMax Baseline", "https://www.carmax.com/sell-my-car", use_container_width=True)
        with tc2:
            tax_rate = 0.0625
            cash_gap = (floor_price - trade_val) * (1 + tax_rate)
            st.metric("Estimated Cash Gap (After Tax)", f"${cash_gap:,.2f}")

        st.divider()
        st.subheader("Step 3: Payment Calculator")
        pc1, pc2, pc3 = st.columns(3)
        term = pc1.selectbox("Term (Months)", [36, 48, 60, 72, 84], index=2)
        apr = pc2.number_input("Interest Rate (APR %)", value=5.5, step=0.1)
        down = pc3.number_input("Additional Down Payment ($)", value=0, step=500)
        
        loan_amount = cash_gap - down
        if loan_amount > 0:
            m_rate = (apr / 100) / 12
            pmt = loan_amount * (m_rate * (1 + m_rate)**term) / ((1 + m_rate)**term - 1)
            st.metric("Estimated Monthly Payment", f"${pmt:,.2f}")
    elif st.session_state.search_results == []:
        st.error(f"No units found matching this criteria within {RADIUS} miles of {user_zip}.")
