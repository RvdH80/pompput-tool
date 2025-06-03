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

# Inlezen van externe K-waardes uit Excel
@st.cache_data

def load_k_waardes():
    df = pd.read_excel("k_waardes_invulsheet.xlsx", index_col=0)
    return df.transpose().to_dict()

k_waardes_dict = load_k_waardes()

st.title("Pompput Dimensionering Tool")
st.markdown("Berekeningen gebaseerd op standaardformules, RIONED-tabellen en leidingweerstanden.")

st.header("1. Invoer parameters")
aanvoer_type = st.radio("Kies type aanvoerberekening", ["Oppervlakte en bui (RIONED)", "Vaste waarde in m³/h"])

if aanvoer_type == "Oppervlakte en bui (RIONED)":
    c = st.number_input("Afvoercoëfficiënt (C)", min_value=0.0, max_value=1.0, value=0.9, step=0.1)
    a = st.number_input("Afwaterend oppervlak (m²)", min_value=0.0, value=5000.0)
    t_keuze = st.selectbox("Herhalingstijd (T-waarde, in jaren)", options=[2,5,10,25,50,100], index=2)
    duur_keuze = st.selectbox("Buiduur", options=list(rioned_data.keys()), index=1)

    regen_mm = rioned_data[duur_keuze][t_keuze]
    duur_sec = duur_mapping[duur_keuze]
    i_m_s = (regen_mm / 1000) / duur_sec
    st.write(f"**Neerslagintensiteit:** {regen_mm} mm over {duur_keuze} = {round(i_m_s,6)} m/s")

    q_in = c * i_m_s * a
else:
    vaste_q_m3h = st.number_input("Vaste aanvoer (m³/h)", min_value=0.0, value=180.0)
    q_in = vaste_q_m3h / 3600

st.write(f"**Aanvoerdebiet Qₐ:** {round(q_in,4)} m³/s = {round(q_in*1000,1)} l/s")

st.header("2. Buffervolume en schakelhoogte")
eenheid = st.selectbox("Eenheid pompcapaciteit", ["l/s", "m³/h"])
q_pomp_input = st.number_input(f"Pompcapaciteit ({eenheid})", min_value=0.1, value=60.0)

if eenheid == "l/s":
    q_pomp_l_s = q_pomp_input
else:
    q_pomp_l_s = q_pomp_input * 1000 / 3600

q_pomp_l_s = st.number_input("Bevestig/aangepaste pompcapaciteit (l/s)", min_value=0.1, value=q_pomp_l_s)

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
st.write(f"**Hoogteverschil Δh:** {round(delta_h,3)} m")
st.write(f"**Uitschakelhoogte (putbodem):** {round(putbodem_nap,3)} m")
st.write(f"**Inschakelhoogte:** {round(inschakel_peil := putbodem_nap + delta_h,3)} m")
st.write(f"**Toegestane max waterstand (1 cm onder B.O.B.):** {round(peil_max_toegestaan,3)} m")

if inschakel_peil >= peil_max_toegestaan:
    st.error("⚠️ Waterpeil komt te hoog! Aanvoerleiding kan onder water komen te staan.")
else:
    st.success("✅ Waterpeil blijft onder B.O.B.")

st.subheader("3D-visualisatie pompput")

fig = go.Figure()
fig.add_trace(go.Mesh3d(x=[0, lengte_vis, lengte_vis, 0, 0, lengte_vis, lengte_vis, 0], y=[0, 0, breedte_vis, breedte_vis, 0, 0, breedte_vis, breedte_vis], z=[putbodem_nap]*4 + [maaiveld_nap]*4, color='lightblue', opacity=0.3, name='Pompput'))
fig.add_trace(go.Mesh3d(x=[0, lengte_vis, lengte_vis, 0], y=[0, 0, breedte_vis, breedte_vis], z=[inschakel_peil]*4, color='blue', opacity=0.5, name='Waterstand'))
fig.add_trace(go.Scatter3d(x=[0, lengte_vis], y=[-0.2, -0.2], z=[bob_aanvoer, bob_aanvoer], mode='lines', line=dict(color='red', width=5), name='B.O.B. leiding'))
fig.update_layout(scene=dict(xaxis_title='Lengte (m)', yaxis_title='Breedte (m)', zaxis_title='Hoogte t.o.v. NAP (m)', zaxis=dict(nticks=10, range=[putbodem_nap-0.1, maaiveld_nap+0.1])), margin=dict(l=0, r=0, b=0, t=40), height=600, title="3D Visualisatie Pompput")
st.plotly_chart(fig)

st.header("3. Leidingdimensionering naar bestaande leiding")
l_leiding = st.number_input("Leidinglengte tot aansluiting op bestaande leiding (m)", min_value=1.0, value=20.0)

# Gebruiker kiest vaste DN maat uit Excel
dn_keuze = st.selectbox("Kies leidingdiameter (DN mm)", options=sorted(k_waardes_dict.keys()))
d_mm = int(dn_keuze)
d_leiding = d_mm / 1000  # omzetten naar meter

v = q_pomp_m3_s / (math.pi * (d_leiding/2)**2)
st.write(f"**Snelheid in leiding:** {round(v,2)} m/s")

max_v = 1.5  # m/s
benodigde_d = math.sqrt((4 * q_pomp_m3_s) / (math.pi * max_v))
st.write(f"**Advies minimale diameter bij v={max_v} m/s:** {round(benodigde_d,3)} m")

st.header("4. Drukverlies")
f = st.number_input("Wrijvingsfactor f (Darcy-Weisbach)", min_value=0.01, value=0.03)
g = 9.81
h_frecht = f * (l_leiding / d_leiding) * (v**2 / (2 * g))

st.subheader("Appendages in persleiding tussen pomp en bestaande leiding")
totaal_k = 0.0
for appendage in k_waardes_dict[dn_keuze]:
    aantal = st.number_input(f"Aantal {appendage}", min_value=0, value=0, step=1)
    k = k_waardes_dict[dn_keuze][appendage] or 0
    totaal_k += aantal * k

st.subheader("Balkeerklep (optioneel)")
keuze_bal = st.radio("Bepaling K-waarde balkeerklep", ["Automatisch op basis van snelheid", "Handmatig invoeren"])
if keuze_bal == "Handmatig invoeren":
    k_bal = st.number_input("K-waarde balkeerklep (handmatig)", min_value=0.0, value=10.0)
else:
    if v < 0.6:
        k_bal = 25
    elif v < 1.2:
        k_bal = 15
    elif v < 2.0:
        k_bal = 8
    else:
        k_bal = 5
    st.write(f"Gekozen K-waarde balkeerklep (automatisch): {k_bal}")

totaal_k += k_bal

h_k = totaal_k * (v**2 / (2 * g))
htot = h_frecht + h_k

st.write(f"**Drukverlies leiding (recht):** {round(h_frecht,3)} m")
st.write(f"**Drukverlies appendages incl. balkeerklep:** {round(h_k,3)} m")
st.write(f"**Totaal drukverlies h_tot:** {round(htot,3)} m")

