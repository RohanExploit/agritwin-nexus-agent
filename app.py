"""AgriTwin Nexus — Botanical Earth Twin UI with Live n8n Workflow Animation."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from agents.orchestrator import AgriTwinOrchestrator
from agents.subagents import CROP_PROFILES
from agents.tools import FARM_HUBS
from agents.workflow_viz import render_n8n_workflow

st.set_page_config(
    page_title="AgriTwin Nexus | Autonomous Crop & Cold-Chain Twin",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

HUB_KEYS = list(FARM_HUBS.keys())
CROP_KEYS = list(CROP_PROFILES.keys())

SAMPLES = {
    "Satara Strawberry Cold-Chain (Default)": {"hub": HUB_KEYS[0], "crop": "Strawberry", "cold": True},
    "Mahabaleshwar Berry — Ambient Risk": {"hub": HUB_KEYS[1], "crop": "Strawberry", "cold": False},
    "Nashik Onion Dry-Route Dispatch": {"hub": HUB_KEYS[2], "crop": "Onion", "cold": False},
    "Baramati Pomegranate Reefer Mesh": {"hub": HUB_KEYS[3], "crop": "Pomegranate", "cold": True},
}

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
html, body, [class*="css"] { font-family: 'Outfit', sans-serif; }
code, pre, .mono { font-family: 'JetBrains Mono', monospace !important; }
.stApp { background: linear-gradient(155deg, #F4F7F2 0%, #FAFDF8 60%, #ECFDF5 100%); }
@keyframes growIn { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:translateY(0); } }
.hero-ag {
    animation: growIn .4s ease-out;
    background: #FFFFFF;
    border: 1px solid #BBF7D0;
    border-left: 6px solid #15803D;
    border-radius: 14px;
    padding: 1.05rem 1.35rem;
    margin-bottom: 0.9rem;
    box-shadow: 0 10px 26px rgba(21,128,61,0.08);
}
.kpi-ag {
    background: #FFFFFF;
    border: 1px solid #DCFCE7;
    border-radius: 12px;
    padding: 0.85rem 1rem;
    transition: transform .2s ease, border-color .2s ease;
    box-shadow: 0 4px 12px rgba(20,83,45,0.05);
}
.kpi-ag:hover { transform: translateY(-2px); border-color: #16A34A; }
.kpi-l { color:#4B5563; font-size:0.72rem; text-transform:uppercase; letter-spacing:0.06em; font-weight:700; }
.kpi-v { color:#14532D; font-size:1.35rem; font-weight:700; margin-top:0.15rem; }
.ag-pill-hi { background:#FEE2E2; color:#B91C1C; border:1px solid #F87171; padding:4px 12px; border-radius:999px; font-weight:700; font-size:0.78rem; }
.ag-pill-ok { background:#DCFCE7; color:#15803D; border:1px solid #4ADE80; padding:4px 12px; border-radius:999px; font-weight:700; font-size:0.78rem; }
</style>
""",
    unsafe_allow_html=True,
)

if "ag_hub" not in st.session_state:
    s0 = SAMPLES["Satara Strawberry Cold-Chain (Default)"]
    st.session_state.ag_hub = s0["hub"]
    st.session_state.ag_crop = s0["crop"]
    st.session_state.ag_cold = s0["cold"]


def _apply_sample() -> None:
    s = SAMPLES[st.session_state.ag_sample]
    st.session_state.ag_hub = s["hub"]
    st.session_state.ag_crop = s["crop"]
    st.session_state.ag_cold = s["cold"]
    st.session_state.ag_force = True


with st.sidebar:
    st.markdown("### Sample Twin Scenarios")
    st.selectbox("Load Farm-to-Mandi Preset", list(SAMPLES.keys()), key="ag_sample", on_change=_apply_sample)
    st.markdown("### Farm Twin Controls")
    hub_choice = st.selectbox("Maharashtra Farm Hub", HUB_KEYS, key="ag_hub")
    crop_choice = st.selectbox("Harvest Crop", CROP_KEYS, key="ag_crop")
    cold_chain = st.toggle("Refrigerated Reefer Van (4°C)", key="ag_cold")

    with st.expander("AI Brain Keys (Optional)"):
        gemini_key = st.text_input("Gemini API Key Override", type="password", placeholder="Auto via Secrets / Env")
        groq_key = st.text_input("Groq API Key Override", type="password", placeholder="Auto-fallback")

    run_btn = st.button("Simulate Harvest & APMC Route", type="primary", width="stretch")
    st.caption("Student 07 · BTCOC701 · AgriTwin Nexus")

if "ag_result" not in st.session_state or run_btn or st.session_state.pop("ag_force", False):
    with st.spinner("Polling Open-Meteo Soil/ET0 & OSRM Highway Corridor Routing..."):
        st.session_state.ag_result = AgriTwinOrchestrator().run_twin(
            farm_hub=hub_choice,
            crop=crop_choice,
            cold_chain_enabled=cold_chain,
            gemini_key=gemini_key,
            groq_key=groq_key,
        )

res = st.session_state.ag_result
mc = res["microclimate"]
pest = res["pest_assessment"]
disp = res["dispatch_advice"]
msgs = res["messages"]
blight = float(pest["blight_risk"])
pill_cls = "ag-pill-hi" if blight >= 55 else "ag-pill-ok"

st.markdown(
    f"""
<div class="hero-ag">
  <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.6rem;">
    <div>
      <div style="font-size:1.6rem; font-weight:700; color:#14532D;">AgriTwin Nexus — Autonomous Harvest & Cold-Chain Twin</div>
      <div class="mono" style="color:#4B5563; font-size:0.82rem;">Open-Meteo Soil Moisture & ET₀ · Fungal Blight Model · OSRM Highway APMC Optimizer</div>
    </div>
    <div><span class="{pill_cls}">BLIGHT RISK {blight:.0f}/100 · {disp['recommended_mandi']}</span></div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

k1, k2, k3, k4 = st.columns(4)
k1.markdown(f'<div class="kpi-ag"><div class="kpi-l">Top APMC Mandi</div><div class="kpi-v" style="font-size:1.05rem;">{disp["recommended_mandi"]}</div></div>', unsafe_allow_html=True)
k2.markdown(f'<div class="kpi-ag"><div class="kpi-l">Best Net Margin</div><div class="kpi-v">₹{disp["net_margin_inr_ton"]:,.0f}/t</div></div>', unsafe_allow_html=True)
k3.markdown(f'<div class="kpi-ag"><div class="kpi-l">Soil Moisture / ET₀</div><div class="kpi-v">{mc["soil_moisture"]} · {mc["daily_et0_mm"]}mm</div></div>', unsafe_allow_html=True)
k4.markdown(f'<div class="kpi-ag"><div class="kpi-l">AI Layer ({res["synthesis"]["latency_ms"]}ms)</div><div class="kpi-v" style="font-size:1.0rem;">{res["synthesis"]["model"]}</div></div>', unsafe_allow_html=True)

st.markdown("")
wf_nodes = [
    {"title": "AgriTwin Orchestrator", "role": "Orchestrator", "phase": "TRIGGER", "metric": crop_choice, "payload": f"Launched farm-to-mandi twin at {hub_choice} (Reefer={cold_chain})", "confidence": 0.98, "color": "#15803D", "icon": "🚜"},
    {"title": "AgroMicroclimateScout", "role": "Scout 1", "phase": "SENSE", "metric": f"ET₀ {mc['daily_et0_mm']}mm", "payload": msgs[1]["content"] if len(msgs) > 1 else "Polled Open-Meteo Soil/ET0", "confidence": msgs[1]["confidence"] if len(msgs) > 1 else 0.95, "color": "#0284C7", "icon": "🌦️"},
    {"title": "ColdChainOptimizer", "role": "Scout 2", "phase": "ROUTE", "metric": f"{len(res['mandi_routes'])} mandis", "payload": msgs[3]["content"] if len(msgs) > 3 else "Computed OSRM spoilage vs net INR", "confidence": msgs[3]["confidence"] if len(msgs) > 3 else 0.94, "color": "#0D9488", "icon": "🚛"},
    {"title": "PestBlightModeler", "role": "Critic", "phase": "BLIGHT", "metric": f"Risk {blight:.0f}/100", "payload": msgs[2]["content"] if len(msgs) > 2 else pest["irrigation_action"], "confidence": msgs[2]["confidence"] if len(msgs) > 2 else 0.91, "color": "#D97706", "icon": "🍄"},
    {"title": "HarvestDispatch", "role": "Planner", "phase": "DISPATCH", "metric": f"₹{disp['net_margin_inr_ton']:,.0f}/t", "payload": msgs[4]["content"] if len(msgs) > 4 else disp["harvest_window"], "confidence": msgs[4]["confidence"] if len(msgs) > 4 else 0.95, "color": "#16A34A", "icon": "📦"},
    {"title": "AgroMemory + UI", "role": "Persister", "phase": "SYNC", "metric": res["synthesis"]["provider"].split()[0], "payload": f"Stored {res['memory'].get('total_simulations', 1)} twin runs to state/agritwin_memory.json", "confidence": 0.97, "color": "#15803D", "icon": "💾"},
]
render_n8n_workflow(
    wf_nodes,
    theme={"mode": "light", "bg": "#F2F8F3", "card_bg": "#FFFFFF", "border": "#BBF7D0", "accent": "#15803D", "text": "#14532D", "muted": "#4B5563", "bar_bg": "#ECFDF5", "dot": "#CBD5E1"},
    engine_label=f"AgriTwin DAG · {res['synthesis']['provider']}",
)

t1, t2, t3 = st.tabs(["Mandi Net Margin & Risk", "Soil Microclimate & Dispatch", "Agent Bus & Memory"])

with t1:
    g_l, g_r = st.columns([1.45, 1])
    routes_df = pd.DataFrame(res["mandi_routes"])
    with g_l:
        if not routes_df.empty:
            fig_m = go.Figure()
            fig_m.add_trace(go.Bar(name="Net Realization (₹/ton)", x=routes_df["mandi"], y=routes_df["net_realization_inr_ton"], marker_color="#16A34A", text=routes_df["net_realization_inr_ton"], textposition="auto"))
            fig_m.add_trace(go.Bar(name="Freight Cost (₹/ton)", x=routes_df["mandi"], y=routes_df["freight_inr_ton"], marker_color="#D97706"))
            fig_m.update_layout(barmode="group", title="APMC Mandi Net Realization vs Freight Cost", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(255,255,255,0.7)", height=295, margin=dict(l=10, r=10, t=38, b=10))
            st.plotly_chart(fig_m, width="stretch")

    with g_r:
        gauge = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=blight,
                title={"text": f"Canopy Blight Risk ({pest['heat_stress']} Heat)", "font": {"size": 15, "color": "#14532D"}},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": "#DC2626" if blight >= 65 else ("#D97706" if blight >= 40 else "#16A34A")},
                    "steps": [
                        {"range": [0, 40], "color": "#DCFCE7"},
                        {"range": [40, 70], "color": "#FEF3C7"},
                        {"range": [70, 100], "color": "#FEE2E2"},
                    ],
                },
            )
        )
        gauge.update_layout(paper_bgcolor="rgba(0,0,0,0)", height=295, margin=dict(l=15, r=15, t=42, b=10))
        st.plotly_chart(gauge, width="stretch")

    if not routes_df.empty:
        st.dataframe(
            routes_df,
            width="stretch",
            hide_index=True,
            column_config={
                "distance_km": st.column_config.NumberColumn("Dist (km)", format="%.1f km"),
                "transit_hr": st.column_config.NumberColumn("Transit", format="%.2f hr"),
                "spoilage_loss_pct": st.column_config.ProgressColumn("Spoilage %", min_value=0, max_value=25, format="%.2f%%"),
                "freight_inr_ton": st.column_config.NumberColumn("Freight ₹/t", format="₹%d"),
                "net_realization_inr_ton": st.column_config.NumberColumn("Net ₹/t", format="₹%d"),
            },
        )

    with st.expander(f"AI Agronomist & Dispatch Brief ({res['synthesis']['provider']} · {res['synthesis']['model']})", expanded=False):
        st.write(res["synthesis"]["text"])

with t2:
    c_a, c_b = st.columns([1.2, 1])
    with c_a:
        env_rows = [
            {"Sensor": "Air Temperature (°C)", "Reading": mc["mean_temp_c"], "Threshold": mc["max_temp_c"]},
            {"Sensor": "Relative Humidity (%)", "Reading": mc["mean_humidity_pct"], "Threshold": CROP_PROFILES[crop_choice]["blight_hum_thresh"]},
            {"Sensor": "Rain Probability (%)", "Reading": mc["max_rain_prob_pct"], "Threshold": 50},
            {"Sensor": "Soil Moisture (% vol)", "Reading": round(float(mc["soil_moisture"]) * 100, 1), "Threshold": round(CROP_PROFILES[crop_choice]["opt_moisture"] * 100, 1)},
        ]
        fig_env = go.Figure()
        e_df = pd.DataFrame(env_rows)
        fig_env.add_trace(go.Bar(name="Observed Reading", x=e_df["Sensor"], y=e_df["Reading"], marker_color="#0284C7"))
        fig_env.add_trace(go.Bar(name="Crop Target / Threshold", x=e_df["Sensor"], y=e_df["Threshold"], marker_color="#16A34A"))
        fig_env.update_layout(barmode="group", title=f"Open-Meteo Microclimate vs {crop_choice} Profile ({mc['source']})", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(255,255,255,0.7)", height=270, margin=dict(l=10, r=10, t=38, b=10))
        st.plotly_chart(fig_env, width="stretch")

    with c_b:
        st.markdown("#### Autonomous Dispatch Plan")
        st.dataframe(
            pd.DataFrame(
                [
                    {"Directive": "Harvest Window", "Value": disp["harvest_window"]},
                    {"Directive": "Recommended APMC", "Value": disp["recommended_mandi"]},
                    {"Directive": "Logistics Mode", "Value": disp["cold_chain_mode"]},
                    {"Directive": "Irrigation Action", "Value": pest["irrigation_action"]},
                    {"Directive": "Moisture Gap", "Value": f"{pest['moisture_gap']:+.3f} m³/m³"},
                ]
            ),
            width="stretch",
            hide_index=True,
        )

with t3:
    msg_df = pd.DataFrame(msgs)
    if not msg_df.empty:
        fig_m = px.bar(msg_df, x="sender", y="confidence", color="phase", title="Sub-Agent Execution Confidence", height=240)
        fig_m.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(255,255,255,0.7)", margin=dict(l=10, r=10, t=35, b=10))
        st.plotly_chart(fig_m, width="stretch")
        st.dataframe(msg_df[["phase", "sender", "recipient", "confidence", "content"]], width="stretch", hide_index=True)

    hist = res["memory"].get("twin_history", [])
    if hist:
        st.plotly_chart(px.line(pd.DataFrame(hist), x="timestamp_utc", y="net_margin_inr_per_ton", markers=True, title="Persistent Net Mandi Margin History (₹/ton)", height=220), width="stretch")

    st.table(
        pd.DataFrame(
            [
                {"PEAS": "Performance", "Spec": "Post-harvest rupee margin minus spoilage, blight loss & freight"},
                {"PEAS": "Environment", "Spec": "Open-Meteo soil moisture/ET0 & OSRM Maharashtra corridors"},
                {"PEAS": "Actuators", "Spec": "Botanical Twin UI, APMC Dispatch, state/agritwin_memory.json"},
                {"PEAS": "Sensors", "Spec": "Soil temp/moisture, canopy RH, ET0 mm/day, OSRM duration"},
            ]
        )
    )
