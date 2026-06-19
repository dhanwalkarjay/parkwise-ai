import streamlit as st
import pandas as pd
import plotly.express as px
import folium

from streamlit_folium import st_folium
from folium.plugins import HeatMap

from utils.ai_advisor import generate_enforcement_plan

import pickle

import plotly.graph_objects as go

# ── Load all data (cached so it only loads once) ──────────────────────────
@st.cache_data
def load_data():
    df = pd.read_parquet('data/processed/new/impact_scored_data.parquet')
    hotspots = pd.read_csv('data/processed/new/hotspots.csv')
    return df, hotspots

@st.cache_resource
def load_model():
    with open('data/processed/new/model.pkl', 'rb') as f:
        return pickle.load(f)

df, hotspots = load_data()
model_data   = load_model()
model        = model_data['model']

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="ParkWise AI",
    page_icon="🚦",
    layout="wide"
)

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

station_df = pd.read_csv(
    "data/processed/station_risk_scores.csv"
)

vehicle_df = pd.read_csv(
    "data/processed/vehicle_distribution.csv"
)

hotspots = pd.read_csv(
    "data/processed/top_hotspots.csv"
)

recommendations = pd.read_csv(
    "data/processed/station_recommendations_v2.csv"
)

station_hotspots = pd.read_csv(
    "data/processed/station_hotspots.csv"
)

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

st.sidebar.title("🚦 ParkWise AI")

page = st.sidebar.radio(
    "Navigation",
    [
        "Executive Overview",
        "Bengaluru Risk Map",
        "Enforcement Intelligence",
        "AI Patrol Simulator",
        "Impact Simulator",
        "AI Enforcement Advisor",
        "Risk Predictor",
        "Analytics"
    ]
)

# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------

def get_color(v):
    if v > 3000:
        return "red"
    elif v > 1500:
        return "orange"
    elif v > 500:
        return "yellow"
    else:
        return "green"

# --------------------------------------------------
# EXECUTIVE OVERVIEW
# --------------------------------------------------

if page == "Executive Overview":

    st.title("🚦 ParkWise AI")

    st.subheader(
        "AI-Powered Parking Intelligence & Enforcement Recommendation System"
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Violations",
        "298,450",
    )

    col2.metric(
        "Police Stations",
        "54"
    )

    col3.metric(
        "Locations",
        "10,942"
    )

    col4.metric(
        "AI Hotspots",
        "172"
    )

    st.divider()

    st.subheader("Top Police Station Risk Scores")

    fig = px.bar(
        station_df.head(10),
        x="police_station",
        y="risk_score_v2",
        color="risk_score_v2",
        title="Top 10 High Risk Police Stations"
    )

    st.plotly_chart(
        fig,
        width='stretch'
    )

    st.divider()

    st.subheader("Vehicle Distribution")

    fig2 = px.pie(
        vehicle_df,
        names="vehicle_type",
        values="count"
    )

    st.plotly_chart(
        fig2,
        width='stretch'
    )

# --------------------------------------------------
# BENGALURU RISK MAP
# --------------------------------------------------

elif page == "Bengaluru Risk Map":

    st.title("🗺️ Bengaluru Parking Risk Map")

    st.markdown("""
    🔴 Critical Risk  
    🟠 High Risk  
    🟡 Medium Risk  
    🟢 Low Risk
    """)

    station_filter = st.selectbox(
        "Select Police Station",
        ["All"] +
        sorted(
            hotspots["police_station"]
            .dropna()
            .unique()
        )
    )

    m = folium.Map(
        location=[12.9716, 77.5946],
        zoom_start=12
    )

    # HeatMap Layer

    heat_data = hotspots[
        ["latitude", "longitude", "violations"]
    ].values.tolist()

    HeatMap(
        heat_data,
        radius=8,
        blur=10,
        gradient={'0.2':'blue','0.4':'lime','0.6':'orange','1':'red'}
    ).add_to(m)

    # folium.LayerControl().add_to(m)

    # Hotspot Markers

    if station_filter == "All":
        filtered_hotspots = hotspots
    else:
        filtered_hotspots = hotspots[
            hotspots["police_station"]
            == station_filter
        ]
    
    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Total Hotspots",
        len(filtered_hotspots)
    )

    col2.metric(
        "Highest Risk Location",
        int(filtered_hotspots["violations"].max())
    )

    col3.metric(
        "Police Stations",
        filtered_hotspots["police_station"].nunique()
    )

    top50 = filtered_hotspots.head(50)

    for _, row in top50.iterrows():

        folium.CircleMarker(
            location=[
                row["latitude"],
                row["longitude"]
            ],
            radius=min(
                15,
                max(5, row["violations"] / 300)
            ),
            popup=f"""
            <b>{row['location']}</b><br>
            Violations: {row['violations']}<br>
            Station: {row['police_station']}
            """,
            color="white",
            weight=2,
            fill=True,
            fill_color=get_color(row["violations"]),
            fill_opacity=0.9
        ).add_to(m)

    st_folium(
        m,
        width=1200,
        height=550
    )

    st.divider()

    st.subheader("Top 10 High Risk Hotspots")

    st.dataframe(
        hotspots[
            ["location", "violations", "police_station"]
        ].head(10),
        width='stretch'
    )

# --------------------------------------------------
# ENFORCEMENT INTELLIGENCE
# --------------------------------------------------

elif page == "Enforcement Intelligence":

    st.title("🚔 Enforcement Intelligence")

    selected_station = st.selectbox(
        "Select Police Station",
        sorted(recommendations["police_station"].unique())
    )

    station_data = recommendations[
        recommendations["police_station"]
        == selected_station
    ].iloc[0]

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Risk Score",
        round(station_data["risk_score_v2"], 1)
    )

    col2.metric(
        "Priority",
        station_data["priority"]
    )

    col3.metric(
        "Recommended Officers",
        station_data["recommended_officers"]
    )

    st.success(
        f"Recommended Patrol Window: "
        f"{station_data['recommended_patrol_window']}"
    )

    st.metric(
        "Expected Violation Reduction",
        f"{station_data['expected_reduction']}%"
    )

    st.divider()

    st.subheader("Top Hotspots")

    top_hotspots = (
        station_hotspots[
            station_hotspots["police_station"]
            == selected_station
        ]
        .head(10)
    )

    hotspot_names = ""

    for _, row in top_hotspots.head(5).iterrows():

        hotspot_names += (
            f"- {row['location']}\n"
        )

    report_text = f"""
    PARKWISE AI ENFORCEMENT REPORT

    Police Station:
    {selected_station}

    Risk Score:
    {round(station_data['risk_score_v2'],2)}

    Priority:
    {station_data['priority']}

    Recommended Officers:
    {station_data['recommended_officers']}

    Patrol Window:
    {station_data['recommended_patrol_window']}

    Expected Reduction:
    {station_data['expected_reduction']}%

    Top Hotspots:

    {hotspot_names}

    Generated By:
    ParkWise AI
    """

    st.download_button(
        label="📄 Download Enforcement Report",
        data=report_text,
        file_name=f"{selected_station}_report.txt",
        mime="text/plain"
    )

    st.dataframe(
        top_hotspots,
        width='stretch'
    )




# --------------------------------------------------
# AI PATROL SIMULATOR
# --------------------------------------------------


elif page == "AI Patrol Simulator":

    st.title("🤖 AI Patrol Simulator")

    total_officers = st.slider(
        "Available Traffic Officers",
        5,
        100,
        20
    )

    allocation_df = recommendations.copy()

    total_risk = allocation_df["risk_score_v2"].sum()

    allocation_df["allocated_officers"] = (
        allocation_df["risk_score_v2"]
        / total_risk
        * total_officers
    )

    allocation_df["allocated_officers"] = (
        allocation_df["allocated_officers"]
        .clip(lower=1)
        .round()
    )

    allocation_df = allocation_df.sort_values(
        "allocated_officers",
        ascending=False
    )

    st.subheader(
        "Recommended Officer Allocation"
    )

    st.dataframe(
        allocation_df[
            [
                "police_station",
                "risk_score_v2",
                "allocated_officers"
            ]
        ],
        width='stretch'
    )

    expected_impact = (
        allocation_df["allocated_officers"].sum()
        * 120
    )

    st.success(
        f"Estimated Monthly Violations Prevented: "
        f"{int(expected_impact):,}"
    )


# --------------------------------------------------
# IMPACT SIMULATOR
# --------------------------------------------------


elif page == "Impact Simulator":

    st.title("📈 Impact Simulator")

    station = st.selectbox(
        "Police Station",
        recommendations["police_station"]
    )

    station_data = recommendations[
        recommendations["police_station"] == station
    ].iloc[0]

    extra_officers = st.slider(
        "Additional Officers",
        0,
        20,
        5
    )

    impact = extra_officers * 3

    new_risk = max(
        0,
        station_data["risk_score_v2"] - impact
    )

    st.metric(
        "Current Risk",
        round(station_data["risk_score_v2"],1)
    )

    st.metric(
        "Predicted Risk",
        round(new_risk,1)
    )

    st.metric(
        "Improvement",
        f"{impact}%"
    )


# --------------------------------------------------
# ANALYTICS
# --------------------------------------------------


elif page == "AI Enforcement Advisor":

    st.title("🤖 AI Enforcement Advisor")

    selected_station = st.selectbox(
        "Select Police Station",
        recommendations["police_station"]
    )

    station_data = recommendations[
        recommendations["police_station"]
        == selected_station
    ].iloc[0]

    top_hotspots = (
        station_hotspots[
            station_hotspots["police_station"]
            == selected_station
        ]
        .head(5)
    )

    if st.button("Generate AI Strategy"):
        with st.spinner("Generating AI recommendation..."):

            hotspots_text = "\n".join(
                top_hotspots["location"].tolist()
            )

            advice = generate_enforcement_plan(
                station=selected_station,
                risk_score=station_data["risk_score_v2"],
                priority=station_data["priority"],
                officers=station_data["recommended_officers"],
                patrol_window=station_data["recommended_patrol_window"],
                reduction=station_data["expected_reduction"],
                hotspots=hotspots_text
            )

            st.markdown(advice)


# --------------------------------------------------
# ANALYTICS
# --------------------------------------------------


# ── TAB 4: Risk Predictor (interactive what-if tool) ──────────────────────
elif page == "Risk Predictor":
    st.subheader("Predict Violation Risk for Any Location & Time")
    st.markdown("""
    Use the trained model to estimate the probability of a high-impact 
    parking violation occurring at a given location and time — useful 
    for proactive enforcement planning.
    """)

    col1, col2, col3 = st.columns(3)
    with col1:
        station_options = sorted(df['police_station'].unique())
        sel_station = st.selectbox("Police Station", station_options)
    with col2:
        sel_hour = st.slider("Hour of Day", 0, 23, 21)
    with col3:
        sel_day  = st.selectbox("Day of Week",
                                 ['Monday','Tuesday','Wednesday','Thursday',
                                  'Friday','Saturday','Sunday'])

    day_map  = {'Monday':0,'Tuesday':1,'Wednesday':2,'Thursday':3,
                'Friday':4,'Saturday':5,'Sunday':6}
    day_num  = day_map[sel_day]

    vehicle_options = sorted(df['vehicle_type'].unique())
    sel_vehicle = st.selectbox("Vehicle Type", vehicle_options)

    if st.button("Predict Risk", type="primary"):

        with st.spinner(
            "Running AI Risk Prediction..."
        ):
            station_rows = df[df['police_station'] == sel_station]
            avg_lat = station_rows['latitude'].mean()
            avg_lon = station_rows['longitude'].mean()

            is_weekend = 1 if day_num in [5,6] else 0
            is_night   = 1 if (sel_hour >= 21 or sel_hour <= 6) else 0

            le_station = model_data['le_station']
            le_vehicle = model_data['le_vehicle']
            le_junction= model_data['le_junction']

            try:
                station_enc = le_station.transform([sel_station])[0]
            except ValueError:
                station_enc = 0
            try:
                vehicle_enc = le_vehicle.transform([sel_vehicle])[0]
            except ValueError:
                vehicle_enc = 0
            junction_enc = 0  # default "No Junction" encoding

            input_df = pd.DataFrame([{
                'hour': sel_hour, 'day_num': day_num, 'is_weekend': is_weekend,
                'is_night': is_night, 'police_station_enc': station_enc,
                'vehicle_type_enc': vehicle_enc, 'junction_enc': junction_enc,
                'latitude': avg_lat, 'longitude': avg_lon
            }])[model_data['feature_cols']]

            risk = model.predict_proba(input_df)[0][1]

            risk_percent = round(risk * 100, 1)

            fig = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=risk_percent,
                    title={
                        "text":"Predicted Violation Risk"
                    },
                    gauge={
                        "axis":{"range":[0,100]},
                        "bar":{"thickness":0.35},
                        "steps":[
                            {"range":[0,30]},
                            {"range":[30,60]},
                            {"range":[60,100]}
                        ]
                    }
                )
            )

            st.plotly_chart(
                fig,
                width='stretch'
            )

        st.subheader("Why this Prediction?")

        reasons = []

        if is_night:
            reasons.append(
                "🌙 Night-time hours historically show higher violation frequency."
            )

        if is_weekend:
            reasons.append(
                "📅 Weekend activity increases parking pressure."
            )

        reasons.append(
            f"🚔 {sel_station} historical violation patterns contribute to the score."
        )

        reasons.append(
            f"🚗 Vehicle category: {sel_vehicle}"
        )

        for r in reasons:
            st.write(r)

        if risk > 0.6:
            st.error("⚠️ HIGH RISK — Recommend proactive enforcement deployment")
        elif risk > 0.3:
            st.warning("⚡ MODERATE RISK — Consider periodic patrol")
        else:
            st.success("✅ LOW RISK — Standard monitoring sufficient")


        confidence = abs(risk - 0.5) * 2 * 100

        st.metric(
            "Model Confidence",
            f"{confidence:.1f}%"
        )



# --------------------------------------------------
# ANALYTICS
# --------------------------------------------------

elif page == "Analytics":

    st.title("📊 Analytics")

    st.subheader("Vehicle Distribution")

    fig1 = px.bar(
        vehicle_df,
        x="vehicle_type",
        y="count",
        color="count"
    )

    st.plotly_chart(
        fig1,
        width='stretch'
    )

    st.divider()

    st.subheader("Top Police Stations")

    fig2 = px.bar(
        station_df.head(15),
        x="police_station",
        y="violations",
        color="violations"
    )

    st.plotly_chart(
        fig2,
        width='stretch'
    )

    st.divider()

    st.subheader("Top Hotspots")

    st.dataframe(
        hotspots.head(20),
        width='stretch'
    )