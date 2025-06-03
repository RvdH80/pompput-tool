import streamlit as st
import pandas as pd
import math
import plotly.graph_objects as go
from io import BytesIO
from fpdf import FPDF

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

# Hardcoded K-waardes
k_waardes_dict = {
    100: {'knie': 3.5, 'bocht': 1.8, 'recht T': 2.5, '90° T': 7.5, 'terugslagklep': 10.5, 'terugslagklep veer': 37.2, 'kogelafsluiter': 11.5, 'schuifafsluiter': 0.7, 'schroefafsluiter': 37.0, 'vlinderklep': 6.3},
    150: {'knie': 5.2, 'bocht': 2.6, 'recht T': 3.8, '90° T': 11.2, 'terugslagklep': 14.5, 'terugslagklep veer': 49.3, 'kogelafsluiter': 16.8, 'schuifafsluiter': 1.1, 'schroefafsluiter': 53.4, 'vlinderklep': 9.4},
    200: {'knie': 7.0, 'bocht': 3.5, 'recht T': 5.2, '90° T': 15.4, 'terugslagklep': 18.8, 'terugslagklep veer': 64.0, 'kogelafsluiter': 21.6, 'schuifafsluiter': 1.4, 'schroefafsluiter': 70.4, 'vlinderklep': 12.5}
}

st.set_page_config(layout="wide")
st.title("Pompput Dimensionering Tool")
st.markdown("Berekeningen gebaseerd op standaardformules, RIONED-tabellen en leidingweerstanden.")

rapport_data = []

col1, col2 = st.columns([2, 3])

with col1:
    st.header("1. Invoerparameters")
    aanvoer_type = st.radio("Aanvoerbron", ["Oppervlakte en bui (RIONED)", "Vast debiet in m³/h"])
    if aanvoer_type == "Oppervlakte en bui (RIONED)":
        c = st.number_input("Afvoercoëfficiënt (C)", 0.0, 1.0, 0.9)
        a = st.number_input("Afwaterend oppervlak (m²)", 0.0, 100000.0, 5000.0)
        t_keuze = st.selectbox("Herhalingstijd (T)", list(rioned_data["30 min"].keys()), index=2)
        duur_keuze = st.selectbox("Buiduur", list(rioned_data.keys()), index=1)
        regen_mm = rioned_data[duur_keuze][t_keuze]
        duur_sec = duur_mapping[duur_keuze]
        i = regen_mm / 1000 / duur_sec
        q_in = c * i * a
    else:
        q_m3h = st.number_input("Vast debiet (m³/h)", 0.0, 10000.0, 180.0)
        q_in = q_m3h / 3600

    st.write(f"**Aanvoerdebiet:** {round(q_in*1000, 1)} l/s")
    rapport_data.append(f"Aanvoerdebiet: {round(q_in*1000, 1)} l/s")

    st.header("2. Buffervolume en schakelhoogte")
    eenheid = st.selectbox("Eenheid pomp", ["l/s", "m³/h"])
    q_input = st.number_input("Pompcapaciteit", 0.1, 1000.0, 60.0)
    q_pomp = q_input if eenheid == "l/s" else q_input * 1000 / 3600

    keuze_looptijd = st.radio("Kies wijze van schakelen", ["Pomplooptijd", "Aantal schakelmomenten per uur"])
    if keuze_looptijd == "Pomplooptijd":
        looptijd = st.number_input("Pomplooptijd (s)", 30, 600, 120)
    else:
        schakelingen = st.number_input("Aantal schakelingen per uur", 1, 60, 15)
        looptijd = 3600 / schakelingen

    vorm = st.selectbox("Vorm pompput", ["Rond", "Rechthoekig"])
    if vorm == "Rond":
        d = st.number_input("Diameter (m)", 0.2, 10.0, 1.0)
        opp = math.pi * (d / 2) ** 2
        lengte = breedte = d
    else:
        breedte = st.number_input("Breedte (m)", 0.2, 10.0, 1.0)
        lengte = st.number_input("Lengte (m)", 0.2, 10.0, 1.0)
        opp = lengte * breedte

    mv = st.number_input("Maaiveldhoogte t.o.v. NAP (m)", value=2.00)
    bob = st.number_input("B.O.B. aanvoerleiding (m NAP)", value=1.20)
    diepte = st.number_input("Diepte put vanaf maaiveld (m)", 0.1, 10.0, 2.0)
    veiligheidsmarge = st.number_input("Veiligheidsmarge onder B.O.B. (m)", 0.0, 1.0, 0.01)

    bodem = mv - diepte
    buffervolume = q_pomp / 1000 * looptijd
    hoogte_delta = buffervolume / opp
    inschakel_peil = bodem + hoogte_delta
    max_toegestaan = bob - veiligheidsmarge

    if inschakel_peil > max_toegestaan:
        st.error(f"⚠️ Inschakelpeil ({round(inschakel_peil, 2)} m NAP) ligt boven de toegestane max. ({round(max_toegestaan, 2)} m NAP)! Pas pomp, looptijd of put aan.")
        rapport_data.append(f"WAARSCHUWING: Inschakelpeil ({round(inschakel_peil, 2)} m NAP) boven max. ({round(max_toegestaan, 2)} m NAP)")

    st.write(f"Buffer: {round(buffervolume, 3)} m³ | Δh: {round(hoogte_delta, 3)} m")
    rapport_data.append(f"Buffervolume: {round(buffervolume, 3)} m³")

with col2:
    st.subheader("Visualisatie pompput")
    fig = go.Figure()
    fig.add_trace(go.Mesh3d(x=[0, lengte, lengte, 0, 0, lengte, lengte, 0],
                            y=[0, 0, breedte, breedte, 0, 0, breedte, breedte],
                            z=[bodem]*4 + [mv]*4, opacity=0.3, color='blue'))
    fig.add_trace(go.Mesh3d(x=[0, lengte, lengte, 0], y=[0, 0, breedte, breedte],
                            z=[inschakel_peil]*4, opacity=0.6, color='cyan'))
    fig.update_layout(scene=dict(zaxis_title='NAP (m)'), margin=dict(l=0, r=0, b=0, t=40))
    st.plotly_chart(fig, use_container_width=True)

    st.header("3. Leiding en drukverlies")
    leidinglengte = st.number_input("Leidinglengte (m)", 1.0, 1000.0, 20.0)
    dn = st.selectbox("Leidingdiameter DN (mm)", sorted(k_waardes_dict.keys()))
    d_m = dn / 1000
    v = q_pomp / 1000 / (math.pi * (d_m / 2)**2)

    f = st.number_input("Wrijvingsfactor f", 0.01, 0.1, 0.03)
    g = 9.81
    h_frecht = f * (leidinglengte / d_m) * (v**2 / (2 * g))

    st.subheader("Appendages")
    totaal_k = 0.0
    for appendage, k in k_waardes_dict[dn].items():
        aantal = st.number_input(f"Aantal {appendage}", 0, 10, 0)
        totaal_k += aantal * k

    st.subheader("Balkeerklep")
    gebruik_bal = st.radio("Balkeerklep aanwezig?", ["Ja", "Nee"])
    if gebruik_bal == "Ja":
        keuze_bal = st.radio("K-waarde balkeerklep", ["Automatisch", "Handmatig"])
        if keuze_bal == "Handmatig":
            k_bal = st.number_input("K-waarde balkeerklep", 0.0, 100.0, 10.0)
        else:
            k_bal = 25 if v < 0.6 else 15 if v < 1.2 else 8 if v < 2.0 else 5
            st.write(f"Automatische waarde: {k_bal}")
        totaal_k += k_bal

    h_k = totaal_k * (v**2 / (2 * g))
    htot = h_frecht + h_k

    st.write(f"Rechte leidingverlies: {round(h_frecht, 3)} m")
    st.write(f"Appendageverlies incl. balkeerklep: {round(h_k, 3)} m")
    st.write(f"Totale drukverlies: {round(htot, 3)} m")

    rapport_data.append(f"Totale drukverlies: {round(htot, 3)} m")

    st.header("4. Advies")
    max_v = 1.5  # m/s
    benodigde_d = math.sqrt((4 * (q_pomp / 1000)) / (math.pi * max_v)) * 1000  # in mm

    st.write(f"**Advies leidingdiameter bij max snelheid {max_v} m/s:** {int(round(benodigde_d))} mm")
    rapport_data.append(f"Advies leidingdiameter: {int(round(benodigde_d))} mm")

    st.write(f"**Advies pompcapaciteit (voorlooptijd {int(looptijd)} s):** {round(q_pomp, 1)} l/s")
    rapport_data.append(f"Pompcapaciteit: {round(q_pomp, 1)} l/s")

    st.header("5. Rapport export")
    if st.button("Genereer PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Pompput Dimensionering Rapport", ln=True, align='C')
        pdf.ln(10)
        for regel in rapport_data:
            pdf.multi_cell(0, 10, regel)
        pdf_output = BytesIO()
        pdf.output(pdf_output)
        st.download_button("Download rapport als PDF", data=pdf_output.getvalue(), file_name="rapport_pompput.pdf", mime="application/pdf")
