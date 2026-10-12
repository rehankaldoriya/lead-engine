import streamlit as st
import pandas as pd
from datetime import datetime
from modules.database import DatabaseManager
from modules.discovery import DiscoveryEngine
from modules.csv_manager import CSVManager
from modules.deduplication import Deduplicator
from modules.scoring import ScoringEngine
from modules.research import ResearchManager
from modules.outreach import OutreachManager
from modules.backup import BackupManager
from modules.utils import fetch_public_website

# Initialize application state
st.set_page_config(page_title="ALOREX Lead Engine", layout="wide", page_icon="🚀")

# Persistent managers
if 'db' not in st.session_state:
    st.session_state.db = DatabaseManager()
    st.session_state.discovery = DiscoveryEngine(st.session_state.db)
    st.session_state.csv = CSVManager(st.session_state.db)
    st.session_state.dedup = Deduplicator(st.session_state.db)
    st.session_state.scoring = ScoringEngine(st.session_state.db)
    st.session_state.research = ResearchManager(st.session_state.db)
    st.session_state.outreach = OutreachManager(st.session_state.db)
    st.session_state.backup = BackupManager()

db = st.session_state.db

# Sidebar Navigation
st.sidebar.title("ALOREX Lead Engine")
st.sidebar.markdown("---")
page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Business Discovery",
        "All Leads",
        "Lead Profile",
        "Add Lead",
        "Research & Qualification",
        "Follow-ups",
        "Outreach Generator",
        "Import / Export",
        "Backups",
        "Settings & Data Info"
    ]
)

# -----------------------------------------------------------------------------
# 1. Dashboard
# -----------------------------------------------------------------------------
if page == "Dashboard":
    st.title("🚀 Executive Dashboard")

    # KPIs
    total_leads = db.fetch_one("SELECT COUNT(*) as count FROM leads")['count']
    ahmedabad_leads = db.fetch_one("SELECT COUNT(*) as count FROM leads WHERE city = 'Ahmedabad'")['count']
    gandhinagar_leads = db.fetch_one("SELECT COUNT(*) as count FROM leads WHERE city = 'Gandhinagar'")['count']
    high_priority = db.fetch_one("SELECT COUNT(*) as count FROM leads WHERE lead_priority = 'High'")['count']

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Leads", total_leads)
    col2.metric("Ahmedabad", ahmedabad_leads)
    col3.metric("Gandhinagar", gandhinagar_leads)
    col4.metric("High Priority", high_priority)

    st.markdown("---")

    # Analytics
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Leads by City")
        city_data = db.fetch_all("SELECT city, COUNT(*) as count FROM leads GROUP BY city")
        if city_data:
            df_city = pd.DataFrame(city_data)
            st.bar_chart(df_city.set_index('city'))
        else:
            st.write("No data available.")

    with c2:
        st.subheader("Priority Distribution")
        priority_data = db.fetch_all("SELECT lead_priority, COUNT(*) as count FROM leads GROUP BY lead_priority")
        if priority_data:
            df_priority = pd.DataFrame(priority_data)
            st.bar_chart(df_priority.set_index('lead_priority'))
        else:
            st.write("No data available.")

# -----------------------------------------------------------------------------
# 2. Business Discovery
# -----------------------------------------------------------------------------
elif page == "Business Discovery":
    st.title("🔍 Business Discovery")
    st.info("Discover cafés and restaurants in Ahmedabad and Gandhinagar using OpenStreetMap data.")

    col1, col2 = st.columns(2)
    with col1:
        mode = st.selectbox("Discovery Mode", [
            "Entire Ahmedabad",
            "Entire Gandhinagar",
            "Ahmedabad + Gandhinagar",
            "Area / Locality",
            "Radius Search"
        ])

    with col2:
        category = st.selectbox("Category", [
            "All Restaurants & Cafés",
            "Cafés", "Coffee shops", "Specialty coffee", "Restaurants",
            "Fine dining", "Casual dining", "Fast casual", "Bakeries",
            "Patisseries", "Dessert cafés", "Boutique dining", "Hotel restaurants",
            "Bars/pubs with food", "Food courts"
        ])

    custom_area = ""
    if mode == "Area / Locality":
        custom_area = st.text_input("Enter area name (e.g., Bodakdev, SG Highway)")

    if st.button("Run Discovery"):
        if mode == "Area / Locality" and not custom_area:
            st.error("Please enter an area name.")
        else:
            cities_to_search = []
            if mode == "Entire Ahmedabad": cities_to_search = ["Ahmedabad"]
            elif mode == "Entire Gandhinagar": cities_to_search = ["Gandhinagar"]
            elif mode == "Ahmedabad + Gandhinagar": cities_to_search = ["Ahmedabad", "Gandhinagar"]
            elif mode == "Area / Locality": cities_to_search = [custom_area]

            # Simple categories handling
            cats = [category] if category != "All Restaurants & Cafés" else ["All Restaurants & Cafés"]

            with st.status("Running Discovery Engine...") as status:
                for city in cities_to_search:
                    result = st.session_state.discovery.discover(
                        city, cats,
                        progress_callback=lambda msg: status.write(msg)
                    )
                    if result['status'] == 'success':
                        st.write(f"✅ {city}: Found {result['total_found']}, New: {result['new_leads']}")
                    else:
                        st.error(f"❌ {city}: {result['message']}")
                status.update(label="Discovery Completed!", state="complete")

# -----------------------------------------------------------------------------
# 3. All Leads
# -----------------------------------------------------------------------------
elif page == "All Leads":
    st.title("📋 Lead Database")

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        search_query = st.text_input("Search by Name/Area/Phone")
    with col2:
        filter_city = st.selectbox("City", ["All"] + list(set([r['city'] for r in db.fetch_all("SELECT city FROM leads")])))
    with col3:
        filter_priority = st.selectbox("Priority", ["All", "High", "Medium", "Low"])

    query = "SELECT * FROM leads WHERE 1=1"
    params = []

    if search_query:
        query += " AND (business_name LIKE ? OR area LIKE ? OR phone LIKE ?)"
        params.extend([f"%{search_query}%"] * 3)
    if filter_city != "All":
        query += " AND city = ?"
        params.append(filter_city)
    if filter_priority != "All":
        query += " AND lead_priority = ?"
        params.append(filter_priority)

    leads = db.fetch_all(query, tuple(params))
    if leads:
        df = pd.DataFrame(leads)
        st.dataframe(df[['lead_id', 'business_name', 'area', 'city', 'lead_priority', 'outreach_status', 'phone']])
    else:
        st.write("No leads found.")

# -----------------------------------------------------------------------------
# 4. Lead Profile
# -----------------------------------------------------------------------------
elif page == "Lead Profile":
    st.title("👤 Lead Profile")
    lead_id = st.number_input("Enter Lead ID", min_value=1, step=1)

    if lead_id:
        lead = db.get_lead(lead_id)
        if lead:
            tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Research", "Qualification", "Sales"])

            with tab1:
                st.subheader("Business Details")
                col1, col2 = st.columns(2)
                with col1:
                    st.text(f"Name: {lead['business_name']}")
                    st.text(f"Category: {lead['business_category']}")
                    st.text(f"City: {lead['city']}")
                    st.text(f"Area: {lead['area']}")
                with col2:
                    st.text(f"Phone: {lead['phone']}")
                    st.text(f"Website: {lead['website']}")
                    st.text(f"Instagram: {lead['instagram_url']}")

                if lead['website']:
                    if st.button("Fetch Public Website"):
                        with st.spinner("Fetching..."):
                            content = fetch_public_website(lead['website'])
                            if content:
                                st.text_area("Website Content Snippet", content, height=300)
                            else:
                                st.error("Could not fetch website content.")

            with tab2:
                st.subheader("Research Checklist")
                checklist = st.session_state.research.get_checklist(lead_id)
                for item in checklist:
                    is_checked = st.checkbox(item['item_key'].replace('_', ' ').title(), value=item['is_checked'], key=f"check_{item['item_key']}")
                    if is_checked != item['is_checked']:
                        st.session_state.research.update_checklist_item(lead_id, item['item_key'], is_checked)

                notes = st.text_area("Research Notes", value=lead['research_notes'] or "")
                v_status = st.selectbox("Verification Status", ["Unverified", "Partially Verified", "Verified", "Needs Reverification"], index=0)
                if st.button("Save Research"):
                    st.session_state.research.update_research_notes(lead_id, notes, v_status)
                    st.success("Saved!")

            with tab3:
                st.subheader("Lead Scoring")
                # Preliminary scores input
                factors = ["Premium positioning", "Ambience/Experience", "Specialty Concept", "Independent/Boutique", "Digital Opportunity", "Expansion Potential"]
                evidence_data = {}

                with st.form("scoring_form"):
                    for f in factors:
                        col1, col2 = st.columns([1, 3])
                        with col1:
                            s = st.number_input(f"{f} (0-25)", 0, 25, key=f"score_{f}")
                        with col2:
                            e = st.text_input(f"Evidence for {f}", key=f"ev_{f}")
                        evidence_data[f] = {"score": s, "evidence": e, "source": "Manual", "confidence": "High"}

                    manual_adj = st.number_input("Manual Adjustment", -100, 100, 0)
                    adj_reason = st.text_input("Adjustment Reason")

                    if st.form_submit_button("Calculate & Save Score"):
                        score, breakdown = st.session_state.scoring.calculate_preliminary_score(evidence_data)
                        st.session_state.scoring.save_score(lead_id, breakdown, manual_adj, adj_reason)
                        st.success(f"Score updated! Final Score: {score + manual_adj}")

            with tab4:
                st.subheader("Sales Pipeline")
                curr_status = lead['outreach_status']
                new_status = st.selectbox("Status", ["New", "Researching", "Qualified", "Ready to Contact", "Contacted", "Replied", "Meeting Scheduled", "Proposal Sent", "Won", "Lost", "Not a Fit"], index=0)
                if st.button("Update Status"):
                    st.session_state.outreach.update_pipeline_status(lead_id, new_status)
                    st.success("Status updated!")

                st.markdown("---")
                st.subheader("Activity Log")
                history = st.session_state.outreach.get_outreach_history(lead_id)
                if history:
                    st.table(pd.DataFrame(history))
                else:
                    st.write("No activity logged yet.")
        else:
            st.error("Lead not found.")

# -----------------------------------------------------------------------------
# 5. Add Lead
# -----------------------------------------------------------------------------
elif page == "Add Lead":
    st.title("➕ Add New Lead")

    with st.form("add_lead_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Business Name *")
            city = st.text_input("City *")
            category = st.text_input("Category")
            area = st.text_input("Area")
        with col2:
            phone = st.text_input("Phone")
            website = st.text_input("Website")
            instagram = st.text_input("Instagram URL")
            email = st.text_input("Email")

        address = st.text_area("Full Address")
        notes = st.text_area("Research Notes")

        if st.form_submit_button("Save Lead"):
            if not name or not city:
                st.error("Name and City are required.")
            else:
                lead_data = {
                    "business_name": name, "city": city, "business_category": category,
                    "area": area, "full_address": address, "phone": phone,
                    "website": website, "instagram_url": instagram, "email": email,
                    "research_notes": notes, "verification_status": "Unverified"
                }
                # Check duplicates
                dups = st.session_state.dedup.find_duplicates(lead_data)
                if dups:
                    st.warning(f"Possible duplicates found: {len(dups)}")
                    st.write(dups)
                    if st.button("Create anyway"):
                        db.insert_lead(lead_data)
                        st.success("Lead added!")
                else:
                    db.insert_lead(lead_data)
                    st.success("Lead added!")

# -----------------------------------------------------------------------------
# 6. Research & Qualification
# -----------------------------------------------------------------------------
elif page == "Research & Qualification":
    st.title("🎯 Research & Qualification")
    st.info("Focus on high-potential leads and qualify them for ALOREX.")

    unreviewed = db.fetch_all("SELECT * FROM leads WHERE lead_score = 0")
    if unreviewed:
        st.write(f"There are {len(unreviewed)} unreviewed leads.")
        df_unreviewed = pd.DataFrame(unreviewed)
        st.dataframe(df_unreviewed[['lead_id', 'business_name', 'city', 'area']])
    else:
        st.write("All leads have been scored!")

# -----------------------------------------------------------------------------
# 7. Follow-ups
# -----------------------------------------------------------------------------
elif page == "Follow-ups":
    st.title("📅 Follow-up Management")

    # This is a simplified view. In a full version, we'd filter by date.
    leads = db.fetch_all("SELECT * FROM leads WHERE next_follow_up_date IS NOT NULL")
    if leads:
        st.table(pd.DataFrame(leads)[['lead_id', 'business_name', 'next_follow_up_date', 'outreach_status']])
    else:
        st.write("No follow-ups scheduled.")

# -----------------------------------------------------------------------------
# 8. Outreach Generator
# -----------------------------------------------------------------------------
elif page == "Outreach Generator":
    st.title("✍️ Outreach Message Generator")

    lead_id = st.number_input("Lead ID", min_value=1, step=1)
    if lead_id:
        lead = db.get_lead(lead_id)
        if lead:
            msg_type = st.selectbox("Message Type", ["Instagram DM", "WhatsApp", "Email", "Follow-up"])
            draft = st.session_state.outreach.generate_message_draft(lead, msg_type)
            st.text_area("Draft Message", value=draft, height=300)
            st.info("Copy the draft above and send it via the respective channel.")
        else:
            st.error("Lead not found.")

# -----------------------------------------------------------------------------
# 9. Import / Export
# -----------------------------------------------------------------------------
elif page == "Import / Export":
    st.title("📂 Data Import / Export")

    tab1, tab2 = st.tabs(["Import CSV", "Export Data"])

    with tab1:
        st.subheader("Import Leads")
        if st.button("Download Template"):
            path = st.session_state.csv.create_template()
            with open(path, "rb") as f:
                st.download_button("Download CSV Template", f, "lead_import_template.csv", "text/csv")

        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
        if uploaded_file:
            # Save temporarily to file because CSVManager expects path
            with open("data/imports/temp_import.csv", "wb") as f:
                f.write(uploaded_file.getbuffer())

            df, errors = st.session_state.csv.parse_csv("data/imports/temp_import.csv")
            if errors:
                for e in errors: st.error(e)
            else:
                mapping = st.session_state.csv.map_columns(df.columns)
                st.write("Column Mapping:", mapping)

                analysis = st.session_state.csv.analyze_import(df, mapping)
                st.write(f"Total: {analysis['total']} | New: {analysis['new']} | Updates: {analysis['updates']}")
                st.dataframe(pd.DataFrame(analysis['preview']))

                if st.button("Confirm Import"):
                    new_c, up_c = st.session_state.csv.safe_import(df, mapping)
                    st.success(f"Import complete! {new_c} new, {up_c} updated.")

    with tab2:
        st.subheader("Export Leads")
        leads = db.fetch_all("SELECT * FROM leads")
        if leads:
            export_path = "data/export_leads.csv"
            st.session_state.csv.export_leads(leads, export_path)
            with open(export_path, "rb") as f:
                st.download_button("Download All Leads CSV", f, "alorex_leads_export.csv", "text/csv")
        else:
            st.write("No data to export.")

# -----------------------------------------------------------------------------
# 10. Backups
# -----------------------------------------------------------------------------
elif page == "Backups":
    st.title("💾 Database Backups")

    if st.button("Create Now"):
        path = st.session_state.backup.create_backup()
        st.success(f"Backup created: {path}")

    st.markdown("---")
    st.subheader("Available Backups")
    backups = st.session_state.backup.list_backups()
    if backups:
        df_backups = pd.DataFrame(backups)
        st.table(df_backups[['filename', 'created', 'size']])

        selected_backup = st.selectbox("Select backup to restore", [b['filename'] for b in backups])
        if st.button("Restore Backup"):
            backup_path = next(b['path'] for b in backups if b['filename'] == selected_backup)
            if st.session_state.backup.restore_backup(backup_path):
                st.success("Database restored successfully!")
                st.warning("Please restart the application to ensure all connections are fresh.")
            else:
                st.error("Restore failed.")
    else:
        st.write("No backups found.")

# -----------------------------------------------------------------------------
# 11. Settings & Data Info
# -----------------------------------------------------------------------------
elif page == "Settings & Data Info":
    st.title("⚙️ Settings & Info")
    st.markdown('''
    ### Application Information
    - **Database**: SQLite (`data/leads.db`)
    - **Discovery Source**: OpenStreetMap (Overpass API)
    - **Target Cities**: Ahmedabad, Gandhinagar

    **Data Integrity Note**:
    OpenStreetMap coverage is community-maintained and incomplete. Businesses absent from OSM will not appear in these results.
    ''')

    st.markdown("---")
    st.subheader("Data Completeness View")
    total = db.fetch_one("SELECT COUNT(*) as count FROM leads")['count']
    if total > 0:
        with phone := db.fetch_one("SELECT COUNT(*) as count FROM leads WHERE phone IS NOT NULL AND phone != ''"):
            st.write(f"Phone coverage: {phone['count']/total:.1%}")
        with web := db.fetch_one("SELECT COUNT(*) as count FROM leads WHERE website IS NOT NULL AND website != ''"):
            st.write(f"Website coverage: {web['count']/total:.1%}")
        with insta := db.fetch_one("SELECT COUNT(*) as count FROM leads WHERE instagram_url IS NOT NULL AND instagram_url != ''"):
            st.write(f"Instagram coverage: {insta['count']/total:.1%}")
    else:
        st.write("No data available to analyze.")
