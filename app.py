import os
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime

# Page Configuration
st.set_page_config(
    page_title="VIT Bhopal — Unified Campus Helpdesk",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for Streamlit App
st.markdown("""
<style>
    .main-header {
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        font-size: 2.2rem;
        color: #172033;
        margin-bottom: 0px;
    }
    .sub-header {
        color: #657083;
        font-size: 1rem;
        margin-bottom: 20px;
    }
    .status-pill {
        background-color: #eefdf3;
        color: #1da851;
        border: 1px solid #cdf3dc;
        padding: 4px 12px;
        border-radius: 100px;
        font-size: 0.85rem;
        font-weight: 700;
        display: inline-block;
    }
    .card-box {
        background-color: #ffffff;
        border: 1px solid #dbe3ee;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
    }
    .wa-btn {
        background-color: #25d366;
        color: white !important;
        padding: 10px 16px;
        border-radius: 8px;
        text-decoration: none;
        font-weight: 800;
        display: inline-block;
        text-align: center;
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# App Header
col_title, col_stat = st.columns([3, 1])
with col_title:
    st.markdown('<div class="main-header">🎓 VIT Bhopal Campus Helpdesk</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Single Unified Platform for Campus Map, AI Assistant, Cabs & Lost & Found</div>', unsafe_allow_html=True)
with col_stat:
    st.markdown('<br><div class="status-pill">● Help Desk Open — 24 Hours</div>', unsafe_allow_html=True)

# Main Navigation Tabs
tab_map, tab_chat, tab_community, tab_cabs, tab_lf = st.tabs([
    "🗺️ Campus Map",
    "🤖 AI Assistant",
    "💬 Community Chat",
    "🚗 Car Service",
    "🔍 Lost & Found"
])

# ================= TAB 1: CAMPUS MAP =================
with tab_map:
    st.subheader("🗺️ VIT Bhopal Interactive Campus Map")
    st.caption("Search places, inspect buildings, or calculate walking routes with Pathfinder.")
    
    # Read map index HTML or embed standalone SVG map
    map_html_path = os.path.join("campus_map", "index.html")
    if os.path.exists(map_html_path):
        with open(map_html_path, "r", encoding="utf-8") as f:
            map_html = f.read()
        components.html(map_html, height=720, scrolling=True)
    else:
        st.info("Interactive Map Canvas active in primary web interface.")

# ================= TAB 2: AI CHATBOT =================
with tab_chat:
    st.subheader("🤖 University AI Campus Assistant")
    st.caption("Ask questions about admissions, hostels, examinations, fee structures, or campus rules.")

    # Initialize RAG chatbot lazily
    if "rag" not in st.session_state:
        try:
            from chatbot import initialize_chatbot
            with st.spinner("Initializing AI Assistant..."):
                rag, config, vector_db = initialize_chatbot()
                st.session_state.rag = rag
        except Exception:
            st.session_state.rag = None

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {"role": "assistant", "content": "Hello! I am your VIT Bhopal AI Campus Assistant. Ask me anything about hostels, cabs, library, or academics!"}
        ]

    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_query = st.chat_input("Ask your question...")
    if user_query:
        st.session_state.chat_messages.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        with st.chat_message("assistant"):
            if st.session_state.rag:
                with st.spinner("Searching university documents..."):
                    try:
                        res = st.session_state.rag.query(user_query)
                        answer = res["answer"]
                        dept = res.get("predicted_department", "General")
                        sources = res.get("sources", [])
                        
                        resp = f"**[{dept}]**\n\n{answer}"
                        if sources:
                            resp += "\n\n**Sources:**\n" + "\n".join([f"- {s}" for s in sources])
                    except Exception as e:
                        resp = "I am processing your query. For official help desk inquiries, contact +91 96307 41753."
            else:
                # Fallback campus knowledge
                q = user_query.lower()
                if "hostel" in q or "mess" in q:
                    resp = "**[Hostel Admin]** Boys Hostels 1-6 and Girls Hostels offer 4 daily mess meals, Wi-Fi, and 24/7 security."
                elif "cab" in q or "auto" in q or "ride" in q:
                    resp = "**[Transport Desk]** Cabs (Creta, Ertiga, Brezza, Fronx) operate 24/7. Book directly via the Car Service tab."
                elif "ab1" in q or "ab2" in q or "library" in q:
                    resp = "**[Academic Affairs]** AB1 houses CS labs and 600-seat Auditorium. Central Library is open 8 AM to 10 PM."
                elif "lost" in q or "found" in q:
                    resp = "**[Help Desk]** You can report lost/found items in the Lost & Found tab to trigger AI TF-IDF matching."
                else:
                    resp = f"**[Campus Info]** Thanks for asking about '{user_query}'. For admissions, exams, or fee details, contact campus support at +91 96307 41753."

            st.markdown(resp)
            st.session_state.chat_messages.append({"role": "assistant", "content": resp})

# ================= TAB 3: COMMUNITY CHAT =================
with tab_community:
    st.subheader("💬 Live Student Community Chat")
    st.caption("Approved student chat room for real-time discussions, cab sharing, and campus announcements.")

    chat_json_path = os.path.join("college_chat", "chat_data.json")

    def load_community_chat():
        if os.path.exists(chat_json_path):
            try:
                import json
                with open(chat_json_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"users": [], "messages": []}

    def save_community_chat(data):
        try:
            import json
            with open(chat_json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            st.error(f"Error saving message: {e}")

    chat_data = load_community_chat()

    # Community Chat Feed
    st.write("#### 💬 Student Chat Feed")
    chat_container = st.container(height=380)
    with chat_container:
        if chat_data["messages"]:
            for m in chat_data["messages"]:
                st.markdown(f"**👤 {m['user_name']}** <span style='font-size:11px; color:#657083;'>[{m.get('created_at', 'Now')}]</span><br>{m['text']}", unsafe_allow_html=True)
                st.divider()
        else:
            st.info("No messages in community chat yet. Start the conversation below!")

    # Post Message Form
    with st.form("community_post_form", clear_on_submit=True):
        c_col1, c_col2 = st.columns([1, 3])
        with c_col1:
            student_name = st.text_input("Your Name", value="Student")
        with c_col2:
            post_text = st.text_input("Message text...", placeholder="Type your message to the campus community...")
        
        post_btn = st.form_submit_button("Post to Community Chat 💬")
        if post_btn and post_text.strip():
            new_msg = {
                "user_name": student_name.strip() or "Student",
                "text": post_text.strip(),
                "created_at": datetime.now().strftime("%I:%M %p")
            }
            chat_data["messages"].append(new_msg)
            save_community_chat(chat_data)
            st.success("Message posted to community chat!")
            st.rerun()

# ================= TAB 3: CAR SERVICE & CABS =================
with tab_cabs:
    st.subheader("🚗 Campus Cab & Car Service")
    st.caption("Browse 24/7 campus vehicles, compare rates, and book directly on WhatsApp.")

    WA_NUMBER = "919630741753"
    cars = [
        {"name": "Ertiga", "fuel": "Petrol", "price": 2800, "img": "/cab-assets/WhatsApp Image 2026-07-30 at 16.13.24.jpeg"},
        {"name": "Punch Petrol", "fuel": "Petrol", "price": 3000, "img": "/cab-assets/WhatsApp Image 2026-07-30 at 15.57.18.jpeg"},
        {"name": "Creta Diesel", "fuel": "Diesel", "price": 4200, "img": "/cab-assets/WhatsApp Image 2026-07-30 at 15.57.23.jpeg"},
        {"name": "Creta Petrol", "fuel": "Petrol", "price": 4100, "img": "/cab-assets/WhatsApp Image 2026-07-30 at 15.57.34.jpeg"},
        {"name": "Exter CNG", "fuel": "CNG", "price": 3200, "img": "/cab-assets/WhatsApp Image 2026-07-30 at 15.57.36.jpeg"},
        {"name": "Baleno Delta Petrol+CNG", "fuel": "Petrol+CNG", "price": 3500, "img": "/cab-assets/WhatsApp Image 2026-07-30 at 16.10.03.jpeg"},
        {"name": "Fronx", "fuel": "Petrol", "price": 3550, "img": "/cab-assets/WhatsApp Image 2026-07-30 at 15.57.23.jpeg"},
        {"name": "Brezza LXI", "fuel": "Petrol", "price": 3100, "img": "/cab-assets/WhatsApp Image 2026-07-30 at 16.10.03.jpeg"},
    ]

    col_search, col_fuel = st.columns([2, 1])
    with col_search:
        search_q = st.text_input("Search vehicle by name...", "").strip().lower()
    with col_fuel:
        fuel_filter = st.selectbox("Fuel Type", ["All", "Petrol", "Diesel", "CNG"])

    filtered_cars = [
        c for c in cars
        if (not search_q or search_q in c["name"].lower()) and
           (fuel_filter == "All" or fuel_filter.lower() in c["fuel"].lower())
    ]

    grid_cols = st.columns(3)
    for idx, car in enumerate(filtered_cars):
        with grid_cols[idx % 3]:
            st.markdown(f"""
            <div class="card-box">
                <h4>🚗 {car['name']}</h4>
                <p><strong>Fuel:</strong> {car['fuel']}</p>
                <h3 style="color:#3457d5; margin: 4px 0;">₹{car['price']:,} <span style="font-size:12px; color:#657083;">/ 24 Hours</span></h3>
                <a href="https://wa.me/{WA_NUMBER}?text=Hi%2C%20I'd%20like%20to%20book%20the%20{car['name']}%20(24%20Hours)%20through%20Campus%20Helpdesk" target="_blank" class="wa-btn">Book on WhatsApp 💬</a>
            </div>
            """, unsafe_allow_html=True)

# ================= TAB 4: LOST & FOUND =================
with tab_lf:
    st.subheader("🔍 Lost & Found Desk")
    st.caption("Report lost/found items and run automatic AI match suggestions.")

    from lost_found.database import SessionLocal, engine, Base
    from lost_found.models import Item
    from lost_found.matcher import find_matches

    Base.metadata.create_all(bind=engine)

    with st.expander("📝 Report a Lost or Found Item", expanded=True):
        with st.form("lf_report_form"):
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                item_type = st.selectbox("Report Type", ["lost", "found"])
                item_title = st.text_input("Item Name *", placeholder="e.g. Boat Airdopes, Blue Laptop Bag")
                item_cat = st.selectbox("Category", ["Electronics", "Documents/Cards", "Clothing/Bags", "Keys/Wallets", "Others"])
            with f_col2:
                item_location = st.text_input("Location *", placeholder="e.g. AB1 Lab 204")
                contact_info = st.text_input("Contact Email / Phone / WhatsApp *")
            item_desc = st.text_area("Item Description *", placeholder="Color, stickers, distinct features...")

            submitted = st.form_submit_button("Submit & Run AI Matcher")

            if submitted and item_title and item_desc and contact_info:
                db = SessionLocal()
                try:
                    new_item = Item(
                        type=item_type,
                        status="open",
                        title=item_title,
                        location=item_location,
                        description=item_desc,
                        contact=contact_info
                    )
                    db.add(new_item)
                    db.commit()
                    db.refresh(new_item)

                    st.success(f"✓ Item '{item_title}' registered successfully!")

                    # Run TF-IDF Matcher
                    opposite_type = "found" if item_type == "lost" else "lost"
                    candidates = db.query(Item).filter(Item.type == opposite_type, Item.status == "open").all()
                    matches = find_matches(new_item, candidates)

                    if matches:
                        st.info(f"🎯 Found {len(matches)} potential AI match suggestions!")
                        for m in matches:
                            st.write(f"- **{m['matched_item'].title}** (Similarity: {int(m['score']*100)}%) — {m['matched_item'].description}")
                finally:
                    db.close()

    st.markdown("---")
    st.write("### 📋 Reported Campus Items")
    filter_status = st.radio("Filter", ["All", "lost", "found", "resolved"], horizontal=True)

    db = SessionLocal()
    try:
        q = db.query(Item)
        if filter_status != "All":
            q = q.filter(Item.type == filter_status if filter_status in ["lost", "found"] else Item.status == "resolved")
        items = q.order_by(Item.id.desc()).all()

        if items:
            for item in items:
                with st.container():
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        badge_color = "🔴" if item.type == "lost" else "🟢"
                        st.markdown(f"**{badge_color} [{item.type.upper()}] {item.title}** • *{item.status.upper()}*")
                        st.write(f"{item.description}")
                        st.caption(f"📍 {item.location} | 👤 Contact: {item.contact}")
                    with c2:
                        wa_clean = ''.join(filter(str.isdigit, item.contact))
                        target_link = f"https://wa.me/{wa_clean}" if wa_clean else f"mailto:{item.contact}"
                        st.markdown(f'<a href="{target_link}" target="_blank" class="wa-btn">Connect 💬</a>', unsafe_allow_html=True)
                    st.divider()
        else:
            st.write("No items found.")
    finally:
        db.close()