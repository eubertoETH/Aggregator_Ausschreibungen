# Analyse competitionline

Was die Plattform leistet, woher ihre Daten stammen, und wofür konkret
bezahlt wird.

---

## 1. Was competitionline ist — und was nicht

competitionline ist eine **Fach- und Medienplattform** der competitionline
Verlags GmbH für Architektur, Landschaftsarchitektur und Stadtplanung.

Sie ist **keine Vergabeplattform**. Das ist die wichtigste Abgrenzung
überhaupt: Die Teilnahme am Verfahren — Vergabeunterlagen herunterladen,
Bieterfragen stellen, Teilnahmeantrag einreichen — läuft ausnahmslos über die
elektronische Vergabeplattform des jeweiligen Auftraggebers. Typische
Formulierung in Auslobungen: „Die Kommunikation erfolgt ausschließlich über die
elektronische Vergabeplattform"; der Teilnahmeantrag ist elektronisch über diese
Plattform einzureichen.

competitionline sitzt also ausschließlich in der **Discovery-Schicht**: sie
sagt dir, dass ein Verfahren existiert, und verlinkt weiter.

---

## 2. Produktschichten

Die Plattform besteht aus vier klar trennbaren Schichten mit sehr
unterschiedlichem Aufwand und Schutz.

### Schicht A — Ausschreibungsverzeichnis

Wettbewerbe, VgV-Verfahren, Ausschreibungen. Filterbar nach Objekttyp,
Region, Verfahrensart. Vollständige Auslobung nur für zahlende Mitglieder
einsehbar — bestätigt auch die Architektenkammer Baden-Württemberg in ihrer
Übersicht der Ausschreibungsquellen.

*Aufwand: Aggregation aus Fremdquellen. Schutz: gering.*

### Schicht B — Redaktionelle Anreicherung

Eigene Objekttyp-Taxonomie mit rund 30 Kategorien (Bibliotheken,
Feuerwehr/Polizei/Vollzug, Sakralbauten, Landschaft und Freiraum,
Städtebauliche Projekte, Lichtgestaltung …), redaktionelle Einordnung,
Fachnews, Rechts- und Marktberichterstattung.

*Aufwand: hoch, personengebunden. Schutz: mittel.*

### Schicht C — Ergebnis- und Büro-Datenbank

Wettbewerbsergebnisse mit Preisträgern, Entwürfen, Bildmaterial und
Jury-Kontext; Büroprofile; das competitionline-Ranking. Diese Daten gibt es
nirgends amtlich — sie werden redaktionell erhoben bzw. von Auslobern und
Büros eingemeldet.

*Aufwand: sehr hoch. Schutz: hoch — der eigentliche Burggraben.*

### Schicht D — Analysedienste

Der „Auftragsagent Pro" beschafft und analysiert Vergabeunterlagen und
extrahiert Eckdaten, Bewertungsmatrix, Eignungs- und Ausschlusskriterien
automatisch. Neu und offensichtlich als Reaktion auf genau die Automatisierung
gebaut, die Büros sonst selbst bauen.

*Aufwand: mittel. Schutz: gering — reine Technik.*

---

## 3. Woher die Daten kommen

### Quelle 1 — Amtliche Bekanntmachungen (der Großteil)

Planungswettbewerbe und VgV-Verfahren öffentlicher Auslober werden im
EU-Amtsblatt bekannt gemacht, sobald der geschätzte Auftragswert der
Planungsleistungen den EU-Schwellenwert erreicht — seit 1.1.2026 bei 216.000 €
für die meisten öffentlichen Auftraggeber, 140.000 € für oberste
Bundesbehörden.

Da bei Planungsleistungen das **Honorar** zählt und nicht die Bausumme, liegt
praktisch jedes wirtschaftlich relevante Verfahren oberhalb dieser Schwelle.
Das heißt: Der Löwenanteil des competitionline-Ausschreibungsverzeichnisses
stammt aus Quellen, die frei und lizenzfrei zugänglich sind:

- **TED** — Search API, ausdrücklich an Datennachnutzer gerichtet, ohne
  Authentifizierung; Weiterverwendung frei nach Beschluss 2011/833/EU
- **Datenservice Öffentlicher Einkauf (oeffentlichevergabe.de)** — OpenData-
  Schnittstelle in eForms, CSV und OCDS; Lizenz **CC0**, ausdrücklich zur
  Nachnutzung freigegeben; enthält alle EU-weiten Bekanntmachungen von Bund,
  Ländern und Kommunen plus nationale Bekanntmachungen der Bundesplattform
  e-Vergabe, der Freien Hansestadt Bremen und aus service.bund.de

### Quelle 2 — Direkteinstellungen durch Auslober

Über „Ausschreibung veröffentlichen" und „Ergebnis veröffentlichen" nehmen sie
Auslobungen und Ergebnisse direkt entgegen. Die Architektenkammer
Mecklenburg-Vorpommern verweist ihre Mitglieder ausdrücklich darauf, dass dort
Auslobungen und Ergebnisse kostenlos veröffentlicht werden können.

Das ist der Teil, den ein reiner Open-Data-Aggregator strukturell nicht
abdeckt: private Auslober, unterschwellige Wettbewerbe, Verfahren ohne
Bekanntmachungspflicht.

### Quelle 3 — Kammern und Verbände

Die 16 Architektenkammern registrieren RPW-konforme Planungswettbewerbe und
führen Listen; die AK Nordrhein-Westfalen stellt ihre landesweite
Wettbewerbsliste sogar als CSV bereit. Mehrere Kammern verlinken im Gegenzug
aktiv auf competitionline — die Beziehung ist symbiotisch.

### Quelle 4 — Redaktion

Recherche, Kontakte zu Auslobern und Wettbewerbsbetreuern, Bauherren-Interviews,
Nachverfolgung von Verfahren über Jahre. Nicht reproduzierbar, aber auch nicht
Teil des Ausschreibungs-Feeds.

---

## 4. Wofür konkret bezahlt wird

| Schicht | Zahlungsgegenstand | Alternative |
|---|---|---|
| A | Zugriff auf die vollständige Auslobung, Filter, Merkliste, Newsletter | TED + DÖE Open Data |
| B | Kuratierte Objekttyp-Taxonomie, Vorfilterung durch Menschen | eigener CPV-Filter + semantische Stufe |
| C | Ergebnisse, Entwürfe, Ranking, Büroprofile | keine — nicht ersetzbar |
| D | KI-Analyse der Vergabeunterlagen | Eigenentwicklung |

Entscheidend: **Wer nur Schicht A und B nutzt, zahlt für Aggregation und
Kuratierung von Daten, die zu großen Teilen CC0 bzw. frei nachnutzbar sind.**
Wer Schicht C braucht, hat keine Alternative.

---

## 5. Bewertung der Ersetzbarkeit

**Gut ersetzbar:**

- Vollständigkeit im oberschwelligen Bereich — beide Primärquellen sind
  dieselben, aus denen competitionline schöpft
- Aktualität — man liegt eher vor als hinter der Plattform
- Betriebskosten — zwei keylose HTTP-Endpunkte

**Aufwand, aber machbar:**

- Filterqualität. Vergabestellen kodieren CPV unsauber, ein reiner CPV-Filter
  produziert gleichzeitig Rauschen und Lücken. Die redaktionelle
  Objekttyp-Taxonomie ist der Teil, wo competitionline tatsächlich Arbeit
  leistet.

**Nicht ersetzbar:**

- Direkt eingestellte Auslobungen privater und unterschwelliger Auslober
- Die Ergebnis- und Ranking-Datenbank
- Redaktioneller Vorlauf, bevor eine Bekanntmachung erscheint

---

## 6. Offene empirische Frage

Wie groß die Lücke zwischen „was competitionline zeigt" und „was in TED + DÖE
steht" für ein konkretes Büroprofil tatsächlich ist, lässt sich nicht
schätzen — nur messen.

**Messverfahren:** Zwei bis drei Monate der eigenen competitionline-Trefferliste
gegen einen DÖE/TED-Abzug mit dem eigenen CPV-Set halten. Die Differenzmenge
in beide Richtungen ist das Ergebnis:

- in competitionline, nicht im Abzug → echte Quellenlücke
- im Abzug, nicht in competitionline → Filterproblem auf deren Seite oder
  Rauschen auf der eigenen

Diese Messung sollte vor jeder Ausbaustufe stehen.
