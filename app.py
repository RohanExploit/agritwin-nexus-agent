"""AgriTwin Nexus — Botanical Earth & Precision Agro-Telemetry UI."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from agents.orchestrator import AgriTwinOrchestrator
from agents.subagents import CROP_PROFILES
from agents.tools import FARM_HUBS

st.set_page_config(
    page_title="AgriTwin Nexus | Precision Crop & Cold-Chain Twin",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [class*="css"] { font-family: 'Outfit', sans-serif; color: #1B4332; }
code, pre, .mono { font-family: 'JetBrains Mono', monospace !important; }
.stApp { background: linear-gradient(160deg, #F5F7F2 0%, #ECF3EA 100%); }
.agro-banner {
    background: #1B4332;
    color: #F8FAFC;
    border-radius: 14px;
    padding: 1.3rem 1.5rem;
    margin-bottom: 1rem;
}
.agro-bus {
    background: #FFFFFF;
    border-left: 4px solid #2D6A4F;
    border-radius: 0 10px 10px 0;
    padding: 0.7rem 1rem;
    margin-bottom: 0.55rem;
    box-shadow: 0 2px 6px rgba(27, 67, 50, 0.08);
}
</style>
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### Digital Twin Parameters")
    hub_choice = st.selectbox("Maharashtra Farm Cluster", list(FARM_HUBS.keys()))
    crop_choice = st.selectbox("Crop Physiology Model", list(CROP_PROFILES.keys()))
    cold_chain = st.toggle("Refrigerated Reefer Cold-Chain (4°C)", value=True)
    with st.expander("AI Brain Keys (Optional — 90% Keyless)"):
        gemini_key = st.text_input("Gemini API Key Override", type="password")
        groq_key = st.text_input("Groq API Key Override", type="password")
    run_btn = st.button("Simulate Farm-to-Mandi Twin", type="primary", use_container_width=True)
    st.caption("BTCOC701 CAS Activity-I | Precision Agro-AI")

if "agritwin_res" not in st.session_state or run_btn:
    with st.spinner("AgriTwin running Open-Meteo soil sensing + OSRM cold-chain routing..."):
        st.session_state.agritwin_res = AgriTwinOrchestrator().run_twin(
            farm_hub=hub_choice,
            crop=crop_choice,
            cold_chain_enabled=cold_chain,
            gemini_key=gemini_key,
            groq_key=groq_key,
        )

res = st.session_state.agritwin_res
mc = res["microclimate"]
pa = res["pest_assessment"]
da = res["dispatch_advice"]

st.markdown(
    f"""
<div class="agro-banner">
  <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.8rem;">
    <div>
      <h2 style="margin:0; color:#FFFFFF;">AgriTwin Nexus — Precision Crop &amp; Cold-Chain Digital Twin</h2>
      <div style="color:#D8F3DC; margin-top:0.25rem;">Autonomous fusion of Open-Meteo Soil/ET₀ Telemetry, Fungal Blight Physics &amp; OSRM APMC Highway Routing</div>
    </div>
    <div class="mono" style="background:#D97706; color:#FFFFFF; padding:0.35rem 0.8rem; border-radius:8px; font-weight:600;">
      BEST APMC: {da['recommended_mandi'].split()[0].upper()} · ₹{da['net_margin_inr_ton']:,.0f}/t
    </div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Soil Moisture (0–1cm)", f"{mc['soil_moisture']} m³/m³")
c2.metric("Fungal Blight Risk", f"{pa['blight_risk']}/100")
c3.metric("Daily ET₀ Loss", f"{mc['daily_et0_mm']} mm")
c4.metric("10% AI Synthesizer", res["synthesis"]["provider"])

t1, t2, t3 = st.tabs(["Mandi Spoilage & Microclimate", "Sub-Agent Twin Bus", "PEAS & Simulation Memory"])

with t1:
    l, r = st.columns([1.25, 1])
    with l:
        st.subheader("OSRM Cold-Chain Net Realization by APMC Mandi")
        rdf = pd.DataFrame(res["mandi_routes"])
        fig = px.bar(
            rdf,
            x="mandi",
            y="net_realization_inr_ton",
            color="spoilage_loss_pct",
            color_continuous_scale="YlOrRd",
            text_auto=".0f",
            height=300,
        )
        fig.update_layout(paper_bgcolor="rgba(255,255,255,0.7)", plot_bgcolor="#FFFFFF", margin=dict(l=10, r=10, t=20, b=10))
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(rdf, use_container_width=True, hide_index=True)

    with r:
        st.subheader("Orchestrator Dispatch Decision")
        st.success(res["synthesis"]["text"])
        st.markdown(f"**Harvest Window:** `{da['harvest_window']}`")
        st.markdown(f"**Irrigation Guidance:** `{pa['irrigation_action']}`")
        st.markdown(f"**Transport Mode:** `{da['cold_chain_mode']}`")

with t2:
    st.subheader("Sub-Agent Digital Twin Bus")
    for m in res["messages"]:
        st.markdown(
            f'<div class="agro-bus"><div class="mono" style="font-size:0.78rem; color:#2D6A4F;">[{m["phase"]}] {m["sender"]} → {m["recipient"]} (conf={m["confidence"]})</div><div style="margin-top:0.2rem;">{m["content"]}</div></div>',
            unsafe_allow_html=True,
        )

with t3:
    st.subheader("PEAS Specification")
    st.table(
        pd.DataFrame(
            [
                {"Component": "P — Performance Measure", "Description": "Net farmer margin after spoilage/freight, blight prevention lead-time, irrigation water efficiency."},
                {"Component": "E — Environment", "Description": "Open-Meteo agro-weather grid, OSRM highway network, APMC mandis, Streamlit & GitHub Actions."},
                {"Component": "A — Actuators", "Description": "Harvest window scheduler, irrigation advisor, optimal APMC route dispatcher, twin memory logger."},
                {"Component": "S — Sensors", "Description": "Soil moisture/temp, FAO ET₀, relative humidity, OSRM road duration, state/agritwin_memory.json."},
            ]
        )
    )
    if res["memory"].get("twin_history"):
        st.dataframe(pd.DataFrame(res["memory"]["twin_history"]), use_container_width=True, hide_index=True)
