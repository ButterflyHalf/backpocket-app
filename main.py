import streamlit as st
import streamlit.components.v1 as components  # Make sure this is here!
import requests
import os
import base64
from datetime import datetime

# --- 1. CONFIG & SETTINGS ---
# THIS MUST BE THE VERY FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title="BackPocket Deal | Find The Lowest Price For Your Next New Car",
    page_icon="💰",
    layout="wide"
)

# --- 2. GOOGLE ANALYTICS INJECTION ---
# We use a slightly different wrapper to ensure it breaks out of the "iframe"
ga_code = """
<script async src="https://www.googletagmanager.com/gtag/js?id=G-9J79QQ020C"></script>
<script>
  window.parent.dataLayer = window.parent.dataLayer || [];
  function gtag(){window.parent.dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-9J79QQ020C');
</script>
"""
# Note: we use st.components.v1.html directly here
components.html(ga_code, height=0, width=0)

# --- 1a. URL LOGIC ---
# Check if the URL has a page parameter (e.g., backpocketdeal.com/?page=engine)
query_params = st.query_params
if "page" in query_params:
    if query_params["page"] == "engine":
        st.session_state.page = "engine"
    elif query_params["page"] == "guide":
        st.session_state.page = "guide"

# Inject the Impact.com verification tag AND Meta Description for SEO
st.markdown(
    """
    <head>
        <meta name="description" content="Find the lowest priced new car near you. Use our Market Floor tool and Negotiation Playbook to save thousands.">
        <script>
            var meta = document.createElement('meta');
            meta.name = "impact-site-verification";
            meta.content = "9c4dc491-549c-4de6-98ea-84d662dbce49";
            document.getElementsByTagName('head')[0].appendChild(meta);
        </script>
    </head>
    """,
    unsafe_allow_html=True
)

# Hide the top bar and the "Made with Streamlit" footer
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

API_KEY = os.environ.get("MARKETCHECK_API_KEY")
REVIEW_FILE = "reviews.txt"
RADIUS = "100"

# --- 2. SEED INITIAL DATA ---
if not os.path.exists(REVIEW_FILE):
    with open(REVIEW_FILE, "w") as f:
        f.write(f"2026-04-24|Austin J.|Ford Expedition|8000.0|Using the data from BackPocket changed the entire vibe of the deal. I walked in with the Market Floor data and saved $10k on the purchase and another $4k on trade. Felt like I had an action plan instead of just hoping for the best.\n")

# --- 3. SESSION STATE ---
if 'page' not in st.session_state:
    st.session_state.page = "home"
if 'search_results' not in st.session_state:
    st.session_state.search_results = None

# --- 4. STYLING (CSS) ---
st.markdown("""
    <style>
    /* Make buttons use the theme's text color */
    div.stButton > button {
        background: none !important; border: none !important; padding: 0 !important;
        color: var(--text-color) !important; text-decoration: underline !important;
        font-weight: 600 !important; font-size: 16px !important; box-shadow: none !important;
        opacity: 0.8;
    }
    div.stButton > button:hover { color: var(--primary-color) !important; opacity: 1; }
    
    .block-container { padding-top: 0rem !important; }
    
    /* Car cards now adapt to dark/light mode background */
    .car-card {
        background-color: var(--secondary-background-color); 
        color: var(--text-color);
        padding: 20px; 
        border-radius: 12px;
        border: 1px solid rgba(128, 128, 128, 0.2); 
        box-shadow: 2px 2px 12px rgba(0,0,0,0.1);
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
        background-color: rgba(128, 128, 128, 0.1);
    }
    
    .car-image-container img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }

    /* Review cards now adapt to dark/light mode background */
    .review-card {
        background-color: var(--secondary-background-color); 
        color: var(--text-color);
        padding: 20px; border-radius: 10px;
        border-left: 5px solid var(--primary-color); 
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 5. TOP NAVIGATION ---
pages = [("BACKPOCKET", "home"), ("SEARCH ENGINE", "engine"), ("NEGOTIATION GUIDE", "guide"), ("SUCCESS STORIES", "reviews")]

# We've increased the decimal values to give the text more horizontal room.
# [0.18, 0.22, 0.25, 0.22, 1.5]
# The first four numbers are for your links, the '1.5' is the empty space on the right.
nav_cols = st.columns([0.3, 0.25, 0.29, 0.22, 1.5]) 

for i, (label, pg) in enumerate(pages):
    if nav_cols[i].button(label, key=f"nav_{pg}"):
        st.session_state.page = pg
        st.rerun()
st.markdown("<hr style='margin: 0px;'>", unsafe_allow_html=True)

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
    st.markdown("# Lowest Priced New Cars Near You")
    st.markdown("### 2026 Buyers Guide & Deal Analysis")
    
    st.write("""
        Buying a new car in America right now is tricky. With MSRPs 
        fluctuating and dealers adding 'market adjustments,' you need to know 
        the real numbers. 
        
        **BackPocket** analyzes the latest data for new cars near you to show the actual 'Drive-Away' price.
    """)

    # --- AGGREGATOR BUSTER CONTENT ---
    with st.container():
        st.info("💡 **Austin Market Insight (April 2026):**")
        st.write("""
            * **Dealer Warning:** Watch out for any Dealer add-ons at local dealerships (common for $2k in hidden fees).
            * **The Savings:** Trading in your vehicle can save you up to thousands on a new vehcile.
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
    st.title("The 2026 Car Negotiation Playbook")
    st.markdown("#### How to secure the best new car deal and avoid hidden dealer fees.")
    
    st.info("💡 **Pro Tip:** Dealers negotiate every day. You only do it every few years. This guide levels the playing field using the **Market Floor** data you found on BackPocket.")

    # Phase 1: Preparation
    st.subheader("Phase 1: Preparation")
    
    with st.expander("Step 1: Weaponize Your Data", expanded=True):
        st.write("""
        **Get your data before you set foot on the lot.** * Use [**KBB**](https://www.kbb.com/whats-my-car-worth/) or [**CarMax**](https://www.carmax.com/sell-my-car) to establish a baseline for your **car trade-in value**.
        * Use the **BackPocket Search Engine** to find the absolute **Market Floor** (the lowest price) for your specific trim within 100 miles.
        """)

    with st.expander("Step 2: The 10% Affordability Rule", expanded=True):
        st.write("""
        **Verify your budget.**
        * Use our calculator to ensure your total vehicle costs (payment, insurance, maintenance) fit within the **10% of monthly income bucket**. 
        * Knowing your limit prevents you from being "upsold" into a debt trap.
        """)

    # Phase 2: The Negotiation
    st.divider()
    st.subheader("Phase 2: At the Dealership")
    
    with st.expander("Step 3: Master the Sales Rapport", expanded=True):
        st.write("""
        **Be the buyer they want to work with.**
        * Visit your local dealer and be professional. The salesman is there to help you, but they are also there to make a profit. 
        * Let them value your trade-in, but don't discuss numbers yet. Focus on the vehicle's fit for your lifestyle first.
        """)

    with st.expander("Step 4: Focus on the Out-the-Door (OTD) Price", expanded=True):
        st.write("""
        **Don't negotiate the monthly payment.**
        * Dealers love to hide costs in a "monthly payment." Instead, ask for the **Out-the-Door (OTD) Price** sheet. 
        * Compare their number to the [**lowest car prices**](/?page=engine) you found on BackPocket. 
        * If they are higher, ask: *"I'm seeing this exact trim for $X nearby—how are we supposed to close the gap?"*
        """)

    with st.expander("Step 5: The Power to Walk Away", expanded=True):
        st.write("""
        **You are in control.**
        * If the dealer won't budge on **market adjustments** or high doc fees, leave. 
        * You have the data—you know there is a better price out there. Often, walking toward the door is the only way to get their "final, final" offer.
        """)

    with st.expander("Step 6: Digital Price Matching", expanded=True):
        st.write("""
        **Text multiple dealerships at once.**
        * You don't have to visit 10 stores. Get a salesman's cell number and text them: *"I'm buying a Ford Expedition today. My current best OTD offer is $X. If you can beat it without hidden dealer add-ons, I’ll come sign now."*
        * Insist on removing "Pro-Packs," window tints, or nitrogen tires that add zero value.
        """)

    # Phase 3: The Close
    st.divider()
    st.subheader("Phase 3: Closing the Deal")
    
    with st.expander("Step 7: Be Patient", expanded=True):
        st.write("""
        **Hold the line.**
        * Wait for the final adjustment. Let them know you are ready to close **today** if they can shave off that last few hundred dollars to hit your target.
        """)

    with st.expander("Step 8: Choose the Best Deal", expanded=True):
        st.write("""
        **Reward transparency.**
        * Go to the dealership that provided the most transparent numbers and the lowest **Cash Gap** (the difference between the new car and your trade).
        """)

    with st.expander("Step 9: F&I Room Strategy", expanded=True):
        st.write("""
        **Navigate the finance box.**
        * Are **extended car warranties** negotiable? **YES.** If you want one, negotiate the price down just like the car. If not, politely decline all add-ons.
        """)

    st.write("---")
    st.subheader("📩 Don't go in unprepared - check out our Substack")
    st.write("Get the latest car buying negotiation playbooks and market updates sent straight to your mailbox.")

# This creates a clean, clickable button that opens in a new tab
    st.link_button(
    "👉 Follow our Substack", 
    "https://backpocketdeal.substack.com/?r=8ahpfw&utm_campaign=pub-share-checklist"
)

    st.divider()
    if st.button("← BACK TO SEARCH ENGINE"):
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
