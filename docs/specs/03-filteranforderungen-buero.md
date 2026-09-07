# Filteranforderungen – Büroprofil und räumliche Relevanz

**Status:** fachliche Spezifikation, noch keine Implementierung  
**Stand:** 2026-09-07  
**Grundlage:** Büroprofil (alle Leistungsphasen; Schwerpunkt Bauen im Bestand,
Sanierung und Fassade) sowie die vorliegenden competitionline-Screenshots zur
Leistungsart.

## 1. Ziel

Die Standardansicht soll nicht sämtliche DÖE-Bekanntmachungen zeigen, sondern
eine prüfbare Vorauswahl für ein Architektur-/Planungsbüro. Jeder Filter muss
umschaltbar bleiben: Die Vorauswahl darf relevante Verfahren nicht endgültig
verwerfen, sondern soll die tägliche Sichtung verkleinern.

## 2. Standort und Radius

| Anforderung | Festlegung |
|---|---|
| Referenzstandort | Olgastraße 69d, Stuttgart-Mitte |
| Raumfilter | konfigurierbarer Radius in Kilometern vom Referenzstandort |
| Eingabe | Radius-Auswahl (z. B. 25, 50, 100, 200 km; „bundesweit“) |
| Bezugspunkt | Erfüllungsort des Projekts, nie nur der Sitz des Auftraggebers |
| Ergebnis bei ungenauem Ort | Kennzeichnung `Ort ungenau`; nicht stillschweigend ausschließen |

Die konkrete Voreinstellung für den Radius ist noch offen. Für die erste
Bewertung wird ein Radius von 100 km als sinnvoller Startwert vorgeschlagen;
er umfasst Stuttgart und die relevante nähere Region, ohne automatisch ganz
Deutschland einzubeziehen.

## 3. Objektart

Der Filter ist eine Mehrfachauswahl mit drei Zuständen:

- **Bauen im Bestand** – Standard aktiviert
- **Neubau** – Standard aktiviert
- **Unklar / Mischprojekt** – standardmäßig sichtbar, damit unvollständige
  Bekanntmachungen nicht verlorengehen

### 3.1 Deterministische Zuordnung

| Objektart | positive Signale in Titel/Beschreibung |
|---|---|
| Bestand | Bestand, Bauen im Bestand, Sanierung, Instandsetzung, Modernisierung, Umbau, Erweiterung, Revitalisierung, Denkmalschutz, Umnutzung, energetische Ertüchtigung, Fassade |
| Neubau | Neubau, Neubauvorhaben, Neubauprojekt, Ersatzneubau, Neuerrichtung |
| Unklar / Mischprojekt | keines der Signale oder beide Signalgruppen |

Der Objektart-Filter ist eine fachliche Klassifikation aus Bekanntmachungstext
und CPV; DÖE liefert dafür kein durchgehend verlässliches eigenes Feld.

## 4. Leistungsarten

Die Screenshots werden nicht als ungefilterte Liste übernommen. Die folgenden
Leistungsarten sind für das Büroprofil priorisiert.

### 4.1 Standard: Kernleistungen

Diese Kategorien sollen in der Standardansicht enthalten sein:

1. **Objektplanung Gebäude**
2. **Generalplanerleistung**
3. **Bauleitung / Objektüberwachung**
4. **Objektplanung Innenräume**
5. **Fassadenplanung**
6. **Energieplanung / -beratung**
7. **Denkmalschutz**
8. **Thermische Bauphysik**

### 4.2 Optional: fachlich naheliegend, aber nicht automatisch zeigen

Diese Kategorien sollen separat zuschaltbar sein, weil sie häufig Spezialisten
oder andere Leistungsbilder betreffen:

- Tragwerksplanung
- Brandschutz
- Schallschutz / Raumakustik
- Projekt- und Objektmanagement, Projektsteuerung
- BIM
- Ausschreibung / Vergabe
- Objektplanung Freianlagen
- Objektplanung Ingenieurbauwerke

### 4.3 Nicht Bestandteil der Standardvorauswahl

Nicht standardmäßig zeigen: Stadt-/Gebietsplanung, Landschaftsplanung,
technische Ausrüstung, Umweltverträglichkeitsstudie, Vermessung, Facility
Management, Kontrolle/Monitoring, Kostenmanagement, Logistikplanung,
Wettbewerbsbetreuung, Bauleistung, Betrieb, Finanzierung, Forschung,
Fotografie, Kunst, Lieferung, Visualisierung/Modellbau und vergleichbare
Beschaffungs- oder Spezialleistungen.

Sie bleiben über „Alle DÖE-Bekanntmachungen“ recherchierbar.

## 5. Fachliche Filterlogik

Die Vorauswahl besteht aus einer nachvollziehbaren OR-Verknüpfung:

```text
Kernleistung ODER optional gewählte Leistung ODER
Objektart Bestand/Neubau mit Architektur-/Planungs-CPV
```

Danach werden Raumfilter, offene Frist und Nutzerfilter angewendet.

### 5.1 CPV-Basis

Als Architektur-/Planungsbasis dienen mindestens die vorhandenen CPV-Präfixe:

- `712` Architekturleistungen
- `7132` Planungsleistungen im Bauwesen
- `714` Stadtplanung und Landschaftsgestaltung
- `7153` Bauberatung
- `7154` Bauleitung

CPV ist nur ein Eingangssignal. Die spätere Leistungsart-Zuordnung wird aus
CPV **und** Titel/Beschreibung abgeleitet, weil die DÖE-Daten keine
competitionline-Kategorie „Objektplanung Gebäude“ liefern.

### 5.2 Weitere Standardfilter

- offene Teilnahme- oder Angebotsfrist
- Veröffentlichung im frei wählbaren Zeitraum
- Deutschland
- Radius vom Erfüllungsort
- Objektart: Bestand, Neubau und unklar/mischbar
- Leistungsarten gemäß Abschnitten 4.1 und 4.2

## 6. Abgleich mit dem aktuellen DÖE-Abruf

| Anforderung | Im aktuellen Import vorhanden | Direkt filterbar | Bewertung |
|---|---|---|---|
| Titel und Beschreibung | ja | ja, deutscher Volltextindex | deckt sich |
| CPV-Codes | ja | ja, GIN-Index | deckt sich; gute Basis |
| Ort als Stadt | ja | ja | für Anzeige und grobe Region geeignet |
| NUTS-Region | ja | ja | für Regionsfilter geeignet |
| Erfüllungsort-Adresse / Koordinaten | nein, aktuell nicht normalisiert | nein | für exakten Radius fehlt Geocoding |
| Radius in km | nein | nein | neue Geocoding-/Distanzschicht nötig |
| Bestand / Neubau | nein | teilweise über bestehende Schlüsselwörter | eigene Klassifikation nötig |
| Leistungsart nach Screenshots | nein | teilweise über CPV und Text | Mapping-Tabelle nötig |
| Fristen | ja, aus eForms-XML | ja | deckt sich |
| Auftraggeber | ja | ja | deckt sich |
| geschätzter Wert | teilweise, Datenqualität uneinheitlich | eingeschränkt | nicht als Pflichtfilter verwenden |

## 7. Fachliche Schlussfolgerung

Die gewünschte Vorauswahl ist mit dem aktuellen DÖE-Abruf **größtenteils
erreichbar**:

- Architektur-/Planungsbezug, Frist, Auftraggeber, Stadt/NUTS und
  Bestands-/Sanierungssignale lassen sich schon heute regelbasiert filtern.
- Die Screenshots liefern eine sinnvolle fachliche Ziel-Taxonomie, aber keine
  direkt aus DÖE übernehmbare Feldstruktur. Dafür wird eine versionierte
  Mapping-Tabelle aus CPV- und Textsignalen benötigt.
- Ein Kilometer-Radius ist erst belastbar, wenn der Erfüllungsort geocodiert
  wird. Bis dahin ist NUTS/Stadt eine grobe, transparente Zwischenlösung.

## 8. Abnahmekriterien für eine spätere Umsetzung

1. Nutzer kann Radius, Objektart und Leistungsarten unabhängig kombinieren.
2. Jeder Treffer zeigt die Gründe seiner Vorauswahl (CPV, Textsignal,
   Leistungsart, Objektart, Entfernung bzw. Ortsgenauigkeit).
3. Unklare Orte und unklare Objektart sind sichtbar markiert und nicht
   unbemerkt ausgeschlossen.
4. „Alle DÖE-Bekanntmachungen“ bleibt als Kontrollansicht verfügbar.
5. Die Klassifikationsregeln sind in Konfiguration versioniert, nicht im
   Frontend versteckt.
