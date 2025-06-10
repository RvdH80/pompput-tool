import streamlit as st
import math

st.set_page_config(layout="wide")

st.title("Pompput Berekeningstool")

# --- Keuzemenu bovenaan ---
keuze = st.selectbox("Wat wil je berekenen?", [
    "1. Totaal afvalwaterproductie",
    "2. Advies pompcapaciteit",
    "3. Benodigd buffervolume onder BOB",
    "4. Advies leidingdiameter",
    "5. Inhoud pompput boven BOB",
    "6. In- en uitschakelhoogtes pomp"
])

# === 1. AFVALWATERPRODUCTIE ===
if keuze == "1. Totaal afvalwaterproductie":
    methode = st.radio("Kies invoermethode", ["Aantal bewoners", "Afwaterend oppervlak"])

    if methode == "Aantal bewoners":
        bewoners = st.number_input("Aantal bewoners", min_value=1, value=4)
        productie = st.number_input("Afvalwaterproductie per persoon (L/dag)", value=120)
        totaal = bewoners * productie / 1000
    else:
        oppervlak = st.number_input("Afwaterend oppervlak (m²)", value=100.0)
        T_waarde = st.number_input("T-waarde (mm/jr)", value=800.0)
        totaal = oppervlak * T_waarde / 1_000_000  # m³/jaar

    st.success(f"Totaal afvalwater: {totaal:.2f} m³ {'per dag' if methode == 'Aantal bewoners' else 'per jaar'}")

# === 2. ADVIES POMPCAPACITEIT ===
elif keuze == "2. Advies pompcapaciteit":
    totaal_m3_per_dag = st.number_input("Totaal afvalwater (m³/dag)", value=1.2)
    schakelmethode = st.radio("Bepaling schakelmoment", ["Aantal schakelingen per uur", "Looptijd per cyclus (s)"])

    if schakelmethode == "Aantal schakelingen per uur":
        schakel_freq = st.number_input("Aantal schakelingen per uur", value=4)
        inhoud_per_schakeling = totaal_m3_per_dag / 24 / schakel_freq * 1000  # liter
    else:
        looptijd = st.number_input("Looptijd per cyclus (seconden)", value=60)
        cycli_per_dag = st.number_input("Aantal cycli per dag", value=48)
        inhoud_per_schakeling = totaal_m3_per_dag * 1000 / cycli_per_dag

    advies_lps = inhoud_per_schakeling / looptijd
    st.success(f"Advies pompcapaciteit: {advies_lps:.2f} L/s  ({advies_lps * 3.6:.2f} m³/u)")

# === 3. BUFFERVOLUME ONDER BOB ===
elif keuze == "3. Benodigd buffervolume onder BOB":
    capaciteit = st.number_input("Pompcapaciteit (L/s)", value=1.5)
    looptijd = st.number_input("Looptijd pomp (s)", value=60)
    marge = st.number_input("Veiligheidsmarge (m)", value=0.3)
    diameter = st.number_input("Putdiameter (m)", value=1.0)

    volume = capaciteit * looptijd  # liter
    extra_volume = math.pi * (diameter/2)**2 * marge * 1000
    totaal = volume + extra_volume

    st.success(f"Benodigd buffervolume onder BOB: {totaal:.2f} liter")

# === 4. ADVIES LEIDINGDIAMETER (placeholder) ===
elif keuze == "4. Advies leidingdiameter":
    st.warning("Deze optie wordt nog uitgewerkt. Voor nu handmatig bepalen.")

# === 5. INHOUD POMPPUT BOVEN BOB ===
elif keuze == "5. Inhoud pompput boven BOB":
    hoogte = st.number_input("Hoogte tussen BOB en max waterniveau (m)", value=0.5)
    diameter = st.number_input("Putdiameter (m)", value=1.0)
    inhoud = math.pi * (diameter / 2)**2 * hoogte * 1000

    st.success(f"Inhoud boven BOB: {inhoud:.2f} liter")

# === 6. IN- EN UITSCHAKELHOOGTES ===
elif keuze == "6. In- en uitschakelhoogtes pomp":
    capaciteit = st.number_input("Pompcapaciteit (L/s)", value=1.5)
    looptijd = st.number_input("Looptijd pomp (s)", value=60)
    diameter = st.number_input("Putdiameter (m)", value=1.0)
    marge = st.number_input("Veiligheidsmarge (m)", value=0.3)

    volume = capaciteit * looptijd  # liter
    hoogte_delta = (volume / 1000) / (math.pi * (diameter/2)**2)

    max_niveau = st.number_input("Maximaal waterniveau (m t.o.v. BOB)", value=0.5)
    inschakel = max_niveau - hoogte_delta
    uitschakel = max_niveau

    st.success(f"Inschakelhoogte pomp: {inschakel:.2f} m boven BOB")
    st.success(f"Uitschakelhoogte pomp: {uitschakel:.2f} m boven BOB")
