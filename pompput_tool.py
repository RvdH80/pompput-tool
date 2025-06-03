import streamlit as st
import pandas as pd
import math
import plotly.graph_objects as go

# RIONED-neerslagtabel (mm neerslag per duur en T-waarde)
rioned_data = {
    "10 min": {2: 17, 5: 21, 10: 27, 25: 33, 50: 38, 100: 43},
    "30 min": {2: 26, 5: 33, 10: 42, 25: 53, 50: 61, 100: 68},
    "60 min": {2: 32, 5: 41, 10: 53, 25: 66, 50: 76, 100: 85},
    "120 min": {2: 37, 5: 48, 10: 62, 25: 78, 50: 90, 100: 100},
}

duur_mapping = {
    "10 min": 600,
    "30 min": 1800,
    "60 min": 3600,
    "120 min": 7200,
}

st.title("Pompput Dimensionering Tool")
st.markdown("Berekeningen gebaseerd op standaardformules en RIONED-neerslagtabellen.")

st.header("1. Invoer parameters")
c = st.number_input("Afvoercoëfficiënt (C)", min_value=0.0, max_value=1.0, value=0.9, step=0.1)
a = st.number_input("Afwaterend oppervlak (m²)", min_value=0.0, value=5000.0)
t_keuze = st.selectbox("Herhalingstijd (T-waarde, in jaren)", options=[2,5,10,25,50,100], index=2)
duur_keuze = st.selectbox("Buiduur", options=list(rioned_data.keys()), index=1)

# Neerslagintensiteit ophalen en omrekenen naar m/s
regen_mm = rioned_data[duur_keuze][t_keuze]
duur_sec = duur_mapping[duur_keuze]
i_m_s = (regen_mm / 1000) / duur_sec

st.write(f"**Neerslagintensiteit:** {regen_mm} mm over {duur_keuze} = {round(i_m_s,6)} m/s")

# Debietberekening
q_in = c * i_m_s * a
st.write(f"**Aanvoerdebiet Qₐ:** {round(q_in,4)} m³/s = {round(q_in*1000,1)} l/s")

st.header("2. Buffervolume en schakelhoogte")
q_pomp_l_s = st.number_input("Pompcapaciteit (l/s)", min_value=0.1, value=60.0)
t_looptijd = st.number_input("Pomplooptijd (sec)", min_value=30, value=120)

put_vorm = st.selectbox("Vorm van de pompput", ["Rond", "Rechthoekig"])

if put_vorm == "Rond":
    diam_put = st.number_input("Diameter pompput (m)", min_value=0.2, value=1.0)
    oppervlakte_put = math.pi * (diam_put / 2) ** 2
    lengte_vis = diam_put
    breedte_vis = diam_put
else:
    breedte_put = st.number_input("Breedte pompput (m)", min_value=0.2, value=1.0)
    lengte_put = st.number_input("Lengte pompput (m)", min_value=0.2, value=1.0)
    oppervlakte_put = breedte_put * lengte_put
    lengte_vis = lengte_put
    breedte_vis = breedte_put

# B.O.B. controle
st.subheader("Controle: Hoogtesysteem")
maaiveld_nap = st.number_input("Hoogte maaiveld t.o.v. NAP (m)", value=2.00)
bob_aanvoer = st.number_input("B.O.B. aanvoerleiding (m t.o.v. NAP)", value=1.20)
diepte_put = st.number_input("Diepte pompput vanaf maaiveld (m)", min_value=0.1, value=2.0)

putbodem_nap = maaiveld_nap - diepte_put
q_pomp_m3_s = q_pomp_l_s / 1000
buffer_v = q_pomp_m3_s * t_looptijd

delta_h = buffer_v / oppervlakte_put
peil_berekening = putbodem_nap + delta_h
peil_max_toegestaan = bob_aanvoer - 0.01

st.write(f"**Bufferinhoud V:** {round(buffer_v,3)} m³")
st.write(f"**Hoogteverschil tussen in- en uitschakeling:** {round(delta_h,3)} m")
st.write(f"**Putbodem t.o.v. NAP:** {round(putbodem_nap,3)} m")
st.write(f"**Maximale berekende waterstand (t.o.v. NAP):** {round(peil_berekening,3)} m")
st.write(f"**Toegestane maximum waterstand (1 cm onder BOB):** {round(peil_max_toegestaan,3)} m")

if peil_berekening >= peil_max_toegestaan:
    st.error("⚠️ Waterpeil komt te hoog! Aanvoerleiding kan onder water komen te staan.")
else:
    st.success("✅ Waterpeil blijft onder B.O.B.")

st.subheader("3D-visualisatie pompput")

fig = go.Figure()

# Pompput
fig.add_trace(go.Mesh3d(
    x=[0, lengte_vis, lengte_vis, 0, 0, lengte_vis, lengte_vis, 0],
    y=[0, 0, breedte_vis, breedte_vis, 0, 0, breedte_vis, breedte_vis],
    z=[putbodem_nap]*4 + [maaiveld_nap]*4,
    color='lightblue', opacity=0.3, name='Pompput', showscale=False
))

# Waterstand
fig.add_trace(go.Mesh3d(
    x=[0, lengte_vis, lengte_vis, 0],
    y=[0, 0, breedte_vis, breedte_vis],
    z=[putbodem_nap + delta_h]*4,
    color='blue', opacity=0.5, name='Waterstand', showscale=False
))

# BOB-leiding
fig.add_trace(go.Scatter3d(
    x=[0, lengte_vis],
    y=[-0.2, -0.2],
    z=[bob_aanvoer, bob_aanvoer],
    mode='lines',
    line=dict(color='red', width=5),
    name='B.O.B. leiding'
))

fig.update_layout(
    scene=dict(
        xaxis_title='Lengte (m)',
        yaxis_title='Breedte (m)',
        zaxis_title='Hoogte t.o.v. NAP (m)',
        zaxis=dict(nticks=10, range=[putbodem_nap-0.1, maaiveld_nap+0.1])
    ),
    margin=dict(l=0, r=0, b=0, t=40),
    height=600,
    title="3D Visualisatie Pompput"
)

st.plotly_chart(fig)

st.header("3. Leidingdimensionering")
l_leiding = st.number_input("Leidinglengte (m)", min_value=1.0, value=20.0)
d_leiding = st.number_input("Leidingdiameter (m)", min_value=0.05, value=0.1)
v = q_pomp_m3_s / (math.pi * (d_leiding/2)**2)
st.write(f"**Snelheid in leiding:** {round(v,2)} m/s")

st.header("4. Drukverlies")
f = st.number_input("Wrijvingsfactor f (Darcy-Weisbach)", min_value=0.01, value=0.03)
g = 9.81
h_f = f * (l_leiding / d_leiding) * (v**2 / (2 * g))
st.write(f"**Drukverlies h_f:** {round(h_f,3)} m")
