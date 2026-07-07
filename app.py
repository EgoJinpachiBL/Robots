"""
Streamlit-Dashboard: Industrieroboter China vs. Deutschland
Datenmanagement-Projektbericht

Zeigt Nutzungsperspektive (IFR World Robotics) und Innovationsperspektive
(WIPO IP Statistics) NEBENEINANDER, ohne Kausalitaetsanspruch (siehe
Anforderungen, Schritt 1 der Projektplanung).

Datenquelle: JSON-Dateien im Ordner data/, erzeugt in Schritt 4
(Datenbereinigung & -strukturierung). Siehe data/cleaning_log.md fuer
alle Bereinigungsentscheidungen.

Ausfuehren mit:  streamlit run app.py
"""

import json
import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

LAND_FARBEN = {"DE": "#1f5c99", "CN": "#b5651d", "WORLD": "#7f7f7f"}
LAND_LABEL = {"DE": "Deutschland", "CN": "China", "WORLD": "Welt"}

st.set_page_config(
    page_title="Industrieroboter China vs. Deutschland",
    page_icon="🤖",
    layout="wide",
)


# ---------------------------------------------------------------------------
# Datenladen (gecacht, damit die JSON-Dateien nicht bei jeder Interaktion
# neu von der Festplatte gelesen werden)
# ---------------------------------------------------------------------------

@st.cache_data
def lade_json(dateiname: str):
    pfad = os.path.join(DATA_DIR, dateiname)
    with open(pfad, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def lade_alle_daten():
    return {
        "land": lade_json("dim_land.json"),
        "branche": lade_json("dim_branche.json"),
        "technologiefeld": lade_json("dim_technologiefeld.json"),
        "installationen": lade_json("fakt_installationen.json"),
        "bestand": lade_json("fakt_bestand.json"),
        "bestand_welt_zeitreihe": lade_json("fakt_bestand_welt_zeitreihe.json"),
        "dichte": lade_json("fakt_dichte.json"),
        "patente": lade_json("fakt_patente.json"),
        "kontext_welt": lade_json("kontext_robotik_landschaft_welt.json"),
    }


def branche_name(branche_id, branchen_dim):
    if branche_id is None:
        return "Gesamt"
    for b in branchen_dim:
        if b["Branche_ID"] == branche_id:
            return b["Bezeichnung"]
    return branche_id


def ist_laendervergleichbar(branche_id, branchen_dim):
    if branche_id is None:
        return True
    for b in branchen_dim:
        if b["Branche_ID"] == branche_id:
            return b.get("direkt_laendervergleichbar", False)
    return False


# ---------------------------------------------------------------------------
# Seite: Uebersicht
# ---------------------------------------------------------------------------

def seite_uebersicht(daten):
    st.title("Industrieroboter: China vs. Deutschland")
    st.markdown(
        """
        Dieses Dashboard stellt zwei **getrennte Perspektiven** nebeneinander:

        - **Nutzungsperspektive** (IFR World Robotics): Installationszahlen,
          Branchenverteilung, operativer Bestand, Roboterdichte
        - **Innovationsperspektive** (WIPO IP Statistics): Patentveroeffentlichungen
          im Technologiefeld "Handling" (Naeherung fuer IPC B25J)

        > **Wichtiger Hinweis zur Interpretation:** Die beiden Perspektiven werden
        > bewusst *nicht* kausal miteinander verknuepft. Ein Zusammenhang wie
        > "mehr Patente fuehren zu mehr Robotereinsatz" laesst sich aus diesen
        > Daten nicht ableiten. Alle Diagramme sind rein deskriptiv zu lesen.
        """
    )

    col1, col2, col3 = st.columns(3)
    inst = daten["installationen"]["gesamt_zeitreihe"]
    df_inst = pd.DataFrame(inst)
    letzte = df_inst[df_inst["Jahr_ID"] == 2024]

    for col, land_id in zip([col1, col2, col3], ["DE", "CN", "WORLD"]):
        wert = letzte[letzte["Land_ID"] == land_id]["Anzahl_Einheiten"].values
        if len(wert):
            col.metric(
                f"Installationen {LAND_LABEL[land_id]} (2024)",
                f"{int(wert[0]):,}".replace(",", "."),
            )

    st.caption(
        "Datenstand: World Robotics Report 2025 (IFR) / WIPO IP Statistics Data "
        "Center (Mai 2026). Details zur Datenherkunft und -bereinigung siehe "
        "data/cleaning_log.md."
    )


# ---------------------------------------------------------------------------
# Seite: Installationszahlen (Zeitreihe)
# ---------------------------------------------------------------------------

def seite_installationen(daten):
    st.title("Installationszahlen (Zeitreihe 2014-2024)")
    st.markdown(
        "Jaehrliche Neuinstallationen von Industrierobotern. Quelle: World "
        "Robotics Report 2025 (WR2025-Jahrgang; aeltere Prognosewerte aus "
        "WR2024 wurden bewusst nicht verwendet, siehe Cleaning Log)."
    )

    df = pd.DataFrame(daten["installationen"]["gesamt_zeitreihe"])
    laender = st.multiselect(
        "Laender auswaehlen",
        options=["DE", "CN", "WORLD"],
        default=["DE", "CN"],
        format_func=lambda x: LAND_LABEL[x],
    )

    df_gefiltert = df[df["Land_ID"].isin(laender)].copy()
    df_gefiltert["Land"] = df_gefiltert["Land_ID"].map(LAND_LABEL)

    fig = px.line(
        df_gefiltert,
        x="Jahr_ID",
        y="Anzahl_Einheiten",
        color="Land",
        markers=True,
        color_discrete_map={LAND_LABEL[k]: v for k, v in LAND_FARBEN.items()},
        labels={"Jahr_ID": "Jahr", "Anzahl_Einheiten": "Installationen (Einheiten)"},
    )
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Rohdaten anzeigen"):
        st.dataframe(df_gefiltert[["Land", "Jahr_ID", "Anzahl_Einheiten"]])


# ---------------------------------------------------------------------------
# Seite: Branchenverteilung
# ---------------------------------------------------------------------------

def seite_branchen(daten):
    st.title("Branchenverteilung (2022-2024)")

    branchen_dim = daten["branche"]
    df = pd.DataFrame(daten["installationen"]["branchenaufschluesselung_2022_2024"])

    st.warning(
        "⚠️ **Methodischer Hinweis:** Deutschland/Welt folgen einem "
        "7-Kategorien-Schema, China wird primaer in 3 groeberen Kategorien "
        "berichtet (Electrical/electronics, Automotive, General industry inkl. "
        "Unspecified). Die China-Teilsegmente (Metal, Food, Plastic, Textiles, "
        "Wood) sind Bestandteile von 'General industry' und duerfen NICHT "
        "zusaetzlich zu diesem Aggregat gezaehlt werden. **Direkt "
        "laendervergleichbar sind nur 'Automotive' und 'Electrical/electronics'** "
        "- bei allen anderen Kategorien ist ein 1:1-Vergleich zwischen den "
        "Laendern methodisch nicht sauber moeglich."
    )

    land_wahl = st.selectbox(
        "Land auswaehlen", options=["DE", "CN", "WORLD"],
        format_func=lambda x: LAND_LABEL[x],
    )
    df_land = df[df["Land_ID"] == land_wahl].copy()
    df_land["Branche"] = df_land["Branche_ID"].apply(lambda b: branche_name(b, branchen_dim))
    df_land["Vergleichbar"] = df_land["Branche_ID"].apply(
        lambda b: "Ja" if ist_laendervergleichbar(b, branchen_dim) else "Nein (Vorsicht)"
    )

    fig = px.bar(
        df_land,
        x="Jahr_ID",
        y="Anzahl_Einheiten",
        color="Branche",
        barmode="group",
        labels={"Jahr_ID": "Jahr", "Anzahl_Einheiten": "Installationen (Einheiten)"},
        title=f"Branchenverteilung: {LAND_LABEL[land_wahl]}",
    )
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Rohdaten anzeigen (inkl. Vergleichbarkeits-Flag)"):
        st.dataframe(df_land[["Branche", "Jahr_ID", "Anzahl_Einheiten", "Vergleichbar"]])


# ---------------------------------------------------------------------------
# Seite: Operativer Bestand & Roboterdichte (Stichtag)
# ---------------------------------------------------------------------------

def seite_bestand_dichte(daten):
    st.title("Operativer Bestand & Roboterdichte (Stichtag)")

    st.warning(
        "⚠️ **Methodischer Hinweis:** Fuer operativen Bestand und Roboterdichte "
        "liegen keine Zeitreihen pro Land vor (Scope-Entscheidung, siehe "
        "Anforderungsdokument Schritt 1). Die folgenden Werte sind "
        "**Stichtagsvergleiche** (Bestand: 2024, Dichte: 2023) und erlauben "
        "**keine** Aussage ueber die zeitliche Entwicklung oder Trends."
    )

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Operativer Bestand 2024")
        df_bestand = pd.DataFrame(daten["bestand"]["daten"])
        df_bestand["Land"] = df_bestand["Land_ID"].map(LAND_LABEL)
        fig1 = px.bar(
            df_bestand, x="Land", y="Anzahl_Einheiten",
            color="Land",
            color_discrete_map={LAND_LABEL[k]: v for k, v in LAND_FARBEN.items()},
            labels={"Anzahl_Einheiten": "Bestand (Einheiten)"},
        )
        fig1.update_layout(showlegend=False)
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.subheader("Roboterdichte 2023 (pro 10.000 Beschaeftigte)")
        df_dichte = pd.DataFrame(daten["dichte"]["daten"])
        df_dichte["Land"] = df_dichte["Land_ID"].map(LAND_LABEL)
        fig2 = px.bar(
            df_dichte, x="Land", y="Wert",
            color="Land",
            color_discrete_map={LAND_LABEL[k]: v for k, v in LAND_FARBEN.items()},
            labels={"Wert": "Roboter pro 10.000 Beschaeftigte"},
        )
        fig2.update_layout(showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    with st.expander("Ergaenzung: Weltweite Zeitreihe operativer Bestand (kein Laender-Split)"):
        df_welt = pd.DataFrame(daten["bestand_welt_zeitreihe"])
        fig3 = px.line(
            df_welt, x="Jahr_ID", y="Anzahl_Einheiten", markers=True,
            labels={"Jahr_ID": "Jahr", "Anzahl_Einheiten": "Bestand (Einheiten)"},
        )
        st.plotly_chart(fig3, use_container_width=True)
        st.caption(
            "Diese Zeitreihe existiert nur weltweit aggregiert, nicht "
            "einzeln fuer Deutschland oder China."
        )


# ---------------------------------------------------------------------------
# Seite: Patente (WIPO Innovationsperspektive)
# ---------------------------------------------------------------------------

def seite_patente(daten):
    st.title("Patentveroeffentlichungen (WIPO, Feld 'Handling')")

    st.info(
        "ℹ️ Verwendeter Indikator: 'Patent publications by technology', "
        "Feld '25 - Handling' als **Naeherung** fuer IPC B25J (Roboter/"
        "Manipulatoren) - WIPOs offizielle Statistik bietet keine exakte "
        "IPC-Klassen-Filterung. Zaehlweise: 'Total count by applicant's "
        "origin' (Ursprungsland des Anmelders, nicht Anmeldeamt)."
    )

    df = pd.DataFrame(daten["patente"]["daten"])
    df["Land"] = df["Land_ID"].map(LAND_LABEL)

    fig = px.line(
        df, x="Jahr_ID", y="Anzahl_Patentveroeffentlichungen", color="Land",
        markers=True,
        color_discrete_map={LAND_LABEL[k]: v for k, v in LAND_FARBEN.items() if k in ["DE", "CN"]},
        labels={"Jahr_ID": "Jahr", "Anzahl_Patentveroeffentlichungen": "Patentveroeffentlichungen"},
    )
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

    st.caption(
        "Hinweis: Werte fuer die letzten 1-2 Jahre koennen aufgrund der "
        "WIPO-Publikationsverzoegerung (ca. 18 Monate) unvollstaendig sein."
    )

    with st.expander("Rohdaten anzeigen"):
        st.dataframe(df[["Land", "Jahr_ID", "Anzahl_Patentveroeffentlichungen"]])


# ---------------------------------------------------------------------------
# Navigation / Main
# ---------------------------------------------------------------------------

def main():
    daten = lade_alle_daten()

    st.sidebar.title("Navigation")
    seite = st.sidebar.radio(
        "Abschnitt waehlen",
        [
            "Uebersicht",
            "Installationszahlen (Nutzung)",
            "Branchenverteilung (Nutzung)",
            "Bestand & Dichte (Nutzung, Stichtag)",
            "Patente (Innovation)",
            "Robotik-Landschaft weltweit (Kontext)",
        ],
    )

    if seite == "Uebersicht":
        seite_uebersicht(daten)
    elif seite == "Installationszahlen (Nutzung)":
        seite_installationen(daten)
    elif seite == "Branchenverteilung (Nutzung)":
        seite_branchen(daten)
    elif seite == "Bestand & Dichte (Nutzung, Stichtag)":
        seite_bestand_dichte(daten)
    elif seite == "Patente (Innovation)":
        seite_patente(daten)
    elif seite == "Robotik-Landschaft weltweit (Kontext)":
        seite_kontext_welt(daten)

    st.sidebar.markdown("---")
    st.sidebar.caption(
        "Datenmanagement-Projektbericht | Industrieroboter DE vs. CN\n\n"
        "Nutzungs- und Innovationsperspektive werden bewusst getrennt "
        "dargestellt (keine Kausalverknuepfung)."
    )


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------------
# Seite: Robotik-Landschaft weltweit (Kontext, F7) + Explorations-Regler (F12)
# ---------------------------------------------------------------------------

def seite_kontext_welt(daten):
    st.title("Robotik-Landschaft weltweit (Kontext)")

    st.info(
        "ℹ️ **Diese Seite beantwortet NICHT die Hauptforschungsfrage.** Sie "
        "zeigt ausschliesslich globale IFR-Weltzahlen 2024 zur Einordnung: "
        "Wie verteilt sich der Robotereinsatz insgesamt auf Industrieroboter "
        "(klassisch/Cobot), professionelle Servicerobotik und Medizinroboter? "
        "**Kein Deutschland-China-Vergleich auf dieser Seite** - fuer den "
        "Laendervergleich siehe die anderen Abschnitte."
    )

    kw = daten["kontext_welt"]

    # --- Sunburst: Industrieroboter (Cobot/klassisch) + Servicerobotik + Medizin ---
    labels = ["Robotik gesamt (ohne Consumer)"]
    parents = [""]
    values = [0]  # wird durch Kinder aufsummiert (Plotly Sunburst mit branchvalues="total")

    # Ebene 1: Hauptkategorien
    labels += ["Industrieroboter", "Servicerobotik (professionell)", "Medizinroboter"]
    parents += ["Robotik gesamt (ohne Consumer)"] * 3
    values += [
        kw["industrieroboter"]["gesamt"],
        kw["servicerobotik_professionell"]["gesamt"],
        kw["medizinroboter"]["gesamt"],
    ]

    # Ebene 2: Industrieroboter-Split
    labels += ["Klassischer Industrieroboter", "Cobot"]
    parents += ["Industrieroboter", "Industrieroboter"]
    values += [kw["industrieroboter"]["klassisch"], kw["industrieroboter"]["cobot"]]

    # Ebene 2: Servicerobotik-Kategorien
    for kat in kw["servicerobotik_professionell"]["kategorien"]:
        labels.append(kat["name"])
        parents.append("Servicerobotik (professionell)")
        values.append(kat["einheiten"])

    fig = go.Figure(go.Sunburst(
        labels=labels,
        parents=parents,
        values=values,
        branchvalues="total",
        marker=dict(colorscale="Blues"),
    ))
    fig.update_layout(margin=dict(t=10, l=10, r=10, b=10), height=550)
    st.plotly_chart(fig, use_container_width=True)

    st.caption(
        f"Industrieroboter gesamt: {kw['industrieroboter']['gesamt']:,} Einheiten "
        f"(davon {kw['industrieroboter']['cobot_anteil_prozent']}% Cobots) | "
        f"Servicerobotik professionell: {kw['servicerobotik_professionell']['gesamt']:,} Einheiten | "
        f"Medizinroboter: {kw['medizinroboter']['gesamt']:,} Einheiten. "
        "Alle Werte: World Robotics Report 2025, weltweit."
    )

    st.warning(
        f"⚠️ **Bewusst ausgeklammert:** Consumer-Servicerobotik (z. B. Saugroboter) "
        f"erreichte 2024 rund {kw['consumer_servicerobotik']['gesamt']:,} Einheiten "
        f"weltweit ({kw['consumer_servicerobotik']['wachstum_prozent']}% Wachstum) - "
        "eine andere Groessenordnung (Millionen statt Tausend), die in der obigen "
        "Grafik alle anderen Kategorien optisch verschwinden liesse. Deshalb "
        "separat ausgewiesen, nicht integriert."
    )

    # --- Explorations-Regler (F12) ---
    st.markdown("---")
    st.subheader("🔧 Explorations-Werkzeug: hypothetische Länderaufteilung")

    st.error(
        "🚫 **Kein Messwert, keine Prognose, kein Ergebnis.** Für Servicerobotik-"
        "Kategorien existiert keine kostenlose, methodisch belastbare "
        "Deutschland-China-Aufschlüsselung (siehe Recherche, dokumentiert in "
        "Projektverlauf/Kritische Würdigung). Der folgende Regler dient "
        "ausschliesslich dazu, spielerisch zu erkunden, wie eine BELIEBIG "
        "ANGENOMMENE Verteilung aussehen würde. Die Zahlen unten sind frei "
        "erfunden und dürfen an keiner Stelle im Bericht als reale Befunde "
        "zitiert werden."
    )

    kategorie_wahl = st.selectbox(
        "Kategorie für Exploration wählen",
        options=[k["name"] for k in kw["servicerobotik_professionell"]["kategorien"]]
        + ["Medizinroboter"],
    )

    if kategorie_wahl == "Medizinroboter":
        basis_wert = kw["medizinroboter"]["gesamt"]
    else:
        basis_wert = next(
            k["einheiten"] for k in kw["servicerobotik_professionell"]["kategorien"]
            if k["name"] == kategorie_wahl
        )

    anteil_china = st.slider(
        "Angenommener China-Anteil (%) - frei wählbar, keine reale Grundlage",
        min_value=0, max_value=100, value=50, step=5,
    )

    hyp_china = round(basis_wert * anteil_china / 100)
    hyp_deutschland_anteil = st.slider(
        "Davon angenommener Deutschland-Anteil am Rest (%) - frei wählbar",
        min_value=0, max_value=100, value=15, step=5,
    )
    hyp_deutschland = round((basis_wert - hyp_china) * hyp_deutschland_anteil / 100)

    col1, col2, col3 = st.columns(3)
    col1.metric("Welt (real)", f"{basis_wert:,}".replace(",", "."))
    col2.metric("China (hypothetisch)", f"{hyp_china:,}".replace(",", "."), help="Erfundener Wert")
    col3.metric("Deutschland (hypothetisch)", f"{hyp_deutschland:,}".replace(",", "."), help="Erfundener Wert")

    st.caption(
        "Diese drei Werte ändern sich live mit den Reglern oben. Sie zeigen "
        "ausschliesslich, wie flexibel die App mit granulareren Daten umgehen "
        "könnte, falls diese je verfügbar würden - nicht, wie die reale "
        "Verteilung aussieht."
    )
