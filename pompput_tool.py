import streamlit as st
import math

st.set_page_config(layout="wide")

st.title("Pompput Dimensionering Tool voor Monteurs")

# === Functies ===
def bereken_afvalwater_per_persoon(aantal_bewoners, productie_per_persoon):
    return aantal_bewoners * productie_per_persoon / 1000  # m³/dag

def bereken_afvalwater_regen(opp_m2, t_waarde, c_factor):
    return opp_m2 * t_waarde * c_factor / 1000  # m³/dag

def bereken_inhoud_put_afhankelijk_van_loopduur(pomp_capaciteit_lps, looptijd_s):
    return pomp_capaciteit_lps * looptijd_s  # liter

def bereken_in_uit_schakelhoogtes(put_diameter, buffervolume):
    oppervlakte = math.pi * (put_diameter / 2)**2
    hoogte = buffervolume / (oppervlakte * 1000)
    return hoogte

# === Keuze menu ===
opties = {
    "1. Totaal afvalwaterproductie": 1,
    "2. Advies pompcapaciteit": 2,
    "3. Benodigd buffervolume onder BOB": 3,
    "7. Advies leidingdiameter": 7,
    "8. Inhoud pompput boven BOB": 8,
    "9. In- en uitschakelhoogtes pomp": 9
}

keuze = st.sidebar.selectbox("Welke berekening wil je uitvoeren?", list(opties.keys()))
st.sidebar.markdown("_Kies een optie en vul de benodigde gegevens in._")

col1, col2 = st.columns([1, 1])

with col1:
    st.header("Invoerwaarden")
    afvalbron = st.radio("Afvalwaterbron", ["Huishoudelijk", "Regenwaterafvoer"])

    if afvalbron == "Huishoudelijk":
        bewoners = st.number_input("Aantal bewoners", min_value=1, value=4)
        productie_persoon = st.number_input("Afvalwaterproductie per persoon (L/dag)", value=120)
        afvalwater = bereken_afvalwater_per_persoon(bewoners, productie_persoon)
    else:
        opp = st.number_input("Oppervlakte (m²)", value=100)
        t_waarde = st.number_input("T-waarde (bijv. 0.03 voor T10)", value=0.03)
        c_factor = st.number_input("Afvoercoëfficiënt C", value=0.9)
        afvalwater = bereken_afvalwater_regen(opp, t_waarde, c_factor)

    pomp_capaciteit = st.number_input("Pomp capaciteit (L/s)", value=1.5)
    loopduur = st.number_input("Pomploopduur (s)", value=60)
    put_diameter = st.number_input("Diameter put (m)", value=1.2)
    hoogte_bob = st.number_input("Hoogte BOB (m)", value=0.5)

with col2:
    st.header("Resultaten")

    if keuze.startswith("1"):
        st.subheader("Totaal afvalwaterproductie")
        st.markdown(f"**Afvalwaterproductie:** {afvalwater:.2f} m³/dag")

    if keuze.startswith("2"):
        st.subheader("Advies pompcapaciteit")
        st.markdown(f"**Ingevoerde capaciteit:** {pomp_capaciteit:.2f} L/s ({pomp_capaciteit * 3.6:.2f} m³/h)")

    if keuze.startswith("3"):
        st.subheader("Benodigd buffervolume onder BOB")
        buffervolume = bereken_inhoud_put_afhankelijk_van_loopduur(pomp_capaciteit, loopduur)
        st.markdown(f"**Benodigd volume:** {buffervolume:.2f} liter")

    if keuze.startswith("8"):
        st.subheader("Inhoud pompput boven BOB")
        hoogte_rest = 2.0 - hoogte_bob
        inhoud_boven_bob = math.pi * (put_diameter/2)**2 * hoogte_rest * 1000
        st.markdown(f"**Volume boven BOB:** {inhoud_boven_bob:.1f} liter")

    if keuze.startswith("9"):
        st.subheader("In-/uitschakelhoogte van pomp")
        buffervolume = bereken_inhoud_put_afhankelijk_van_loopduur(pomp_capaciteit, loopduur)
        inschakel = hoogte_bob
        uitschakel = hoogte_bob + bereken_in_uit_schakelhoogtes(put_diameter, buffervolume)
        st.markdown(f"**Inschakelhoogte:** {inschakel:.2f} m")
        st.markdown(f"**Uitschakelhoogte:** {uitschakel:.2f} m")
