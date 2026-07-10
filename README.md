# Robots – China vs. Deutschland im Einsatz von Industrierobotern

Projektbericht und interaktive Datenanwendung im Rahmen des Moduls **Datenmanagement**,
Hochschule Aalen, Studiengang User Experience.

**Forschungsfrage:** Wie unterscheiden sich China und Deutschland beim Einsatz von Industrierobotern?

🔗 **Live-Anwendung:** [robots-5jycn2wapcdbq3rkw5tgtr.streamlit.app](https://robots-5jycn2wapcdbq3rkw5tgtr.streamlit.app/)

---

## Über das Projekt

Das Projekt vergleicht China und Deutschland anhand zweier offizieller, frei zugänglicher
Datenquellen aus zwei komplementären Perspektiven:

- **Nutzungsperspektive** – IFR World Robotics: Installationszahlen, operativer Bestand,
  Roboterdichte, Branchenverteilung
- **Innovationsperspektive** – WIPO IP Statistics: Patentveröffentlichungen im
  Technologiefeld *Handling*

Beide Perspektiven werden bewusst nebeneinandergestellt statt kausal verknüpft – ein Land
kann viele Roboter einsetzen und trotzdem wenig selbst patentieren (z. B. durch Import von
Technik), und umgekehrt. Der Bericht versteht sich neben der inhaltlichen Fragestellung
ausdrücklich auch als Übung im Datenmanagement: nachvollziehbare Datenpipeline,
ERM-Modellierung und technische Umsetzung als interaktive Anwendung.

## Datenpipeline

Das Projekt folgt einer klassischen ETL-Logik in vier Phasen:

1. **Beschaffung** – manueller Download der Rohdaten von IFR (PDF/HTML) und WIPO (CSV)
2. **Bereinigung** – Vereinheitlichung von Skalierungen, Branchengranularität und
   widersprüchlichen Berichtsjahrgängen (siehe `Cleaning Log` im Bericht)
3. **Strukturierung** – Entity-Relationship-Modell mit vier Dimensionstabellen
   (Land, Jahr, Branche, Technologiefeld) und mehreren Faktentabellen
4. **Laden & Visualisierung** – strukturierte Daten als JSON-Dateien, eingebunden in eine
   lokal ausführbare Streamlit-Anwendung

### Datendateien

| Datei | Inhalt |
|---|---|
| `dim_land.json` | Dimension Land (DE, CN, WORLD) |
| `dim_jahr.json` | Dimension Jahr (2014–2024) |
| `dim_branche.json` | Dimension Branche inkl. Vergleichbarkeits-Flag |
| `dim_technologiefeld.json` | Dimension WIPO-Technologiefeld |
| `fakt_installationen.json` | Installationszeitreihe + Branchenaufschlüsselung |
| `fakt_bestand.json` | Operativer Bestand, Stichtag 2024 |
| `fakt_dichte.json` | Roboterdichte, Stichtag 2023 |
| `fakt_patente.json` | WIPO-Patentveröffentlichungen 2014–2023 |
| `kontext_robotik_landschaft_welt.json` | Weltweite Kontextdaten (Cobots, Servicerobotik) |

## Tech-Stack

- **Python** – Programmiersprache
- **Streamlit** – Framework für die interaktive Web-Anwendung
- **Pandas** – Datenverarbeitung
- **Plotly** (Express & Graph Objects) – interaktive Diagramme
- **Graphviz** – ERM- und Pipeline-Diagramme
- **GitHub** – Versionsverwaltung
- **Streamlit Community Cloud** – Hosting

## Lokale Ausführung

```bash
git clone https://github.com/EgoJinpachiBL/Robots.git
cd Robots
pip install -r requirements.txt
streamlit run app.py
```

Die Anwendung läuft vollständig lokal und ohne externe API-Abhängigkeiten – alle Daten
liegen bereits als JSON-Dateien im Repository vor.

## Methodische Einschränkungen

- Direkter Branchenvergleich nur für **Automotive** und **Electrical/electronics** zulässig,
  da nur diese Kategorien in identischer Abgrenzung für beide Länder erhoben werden
- Operativer Bestand und Roboterdichte liegen nur als **Stichtag** vor, nicht als Zeitreihe
- Für Servicerobotik-Kategorien existiert keine belastbare Deutschland-China-Aufschlüsselung
  (siehe Bericht, Kap. 2.4 und Anlage 10.4) – diese Daten werden daher nur als globaler
  Kontext, nicht als Ländervergleich dargestellt
- Ländereinheit "China" = Festlandchina (ohne Hongkong SAR, Macao SAR, Chinese Taipei)

Ausführliche Herleitung, Cleaning Log und kritische Würdigung siehe vollständiger
Projektbericht.

## Quellen

- International Federation of Robotics (2025): *World Robotics 2025 – Industrial Robots*
- Deutscher Robotik Verband (2025): *World Robotics Report 2025 – Zusammenfassung*
- World Intellectual Property Organization (2026): *WIPO IP Statistics Data Center*

## Autoren

Gerald Aidoo · Alexander Feller · Valentin Roeck
Hochschule Aalen – Fakultät Optik und Mechatronik, Studiengang User Experience
