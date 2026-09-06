# Eigene Lösung — Anforderungen, Schnittstellen, Architektur

Grundlage für einen schnellen Prototyp. Scope bewusst eng gehalten.

---

## 1. Zielbild und Abgrenzung

**Aufgabe des Systems:** Täglich alle neu veröffentlichten Vergabeverfahren und
Planungswettbewerbe einsammeln, auf die für das Büro relevanten reduzieren, und
je Treffer den direkten Zugang zu den Vergabeunterlagen bereitstellen.

**Nicht Aufgabe dieses Systems:**

- Analyse der Vergabeunterlagen, Anforderungskatalog, Referenzprojekt-Matching,
  Mappenerstellung → läuft in der bestehenden Bewerbungspipeline
- Einreichung → erfolgt zwingend über die Vergabeplattform des Auftraggebers
- Ergebnis-/Entwurfsdatenbank → kein Bedarf

**Übergabepunkt:** Pro ausgewähltem Verfahren liefert das System die
Download-URL der Vergabeunterlagen. Damit entfällt der manuelle Schritt „ZIP im
Portal suchen und in SharePoint laden"; der Ordner `00_Original` der
Bewerbungspipeline wird automatisch befüllt.

```
[Aggregator]                          [Bewerbungspipeline]
Quellen → Filter → Trefferliste → Auswahl → ZIP-Abruf → 00_Original → …
                                   ▲                    │
                                   └── Mensch entscheidet
```

---

## 2. Quellen und Schnittstellen

### 2.1 TED Search API

- **Endpunkt:** `POST https://api.ted.europa.eu/v3/notices/search`
- **Auth:** keine. Lesen und Suchen sind vollständig anonym; nur das
  Einreichen von Bekanntmachungen erfordert Authentifizierung.
- **Doku:** `https://docs.ted.europa.eu/api/latest/search.html`
- **Abfragesprache:** Expert Query mit **eForms-Feldnamen in kebab-case**
  (`classification-cpv`, `buyer-country`, `notice-type`, `publication-date`).
  Die alten zweistelligen TED-Codes aus Blogposts vor 2023 funktionieren nicht
  mehr.
- **Limits:** 250 Notices pro Seite, ca. 15.000 pro Query-Fenster.
  `paginationMode: ITERATION` für Bulk, `PAGE_NUMBER` für Blättern.

```bash
curl -X POST 'https://api.ted.europa.eu/v3/notices/search' \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "buyer-country=DEU AND classification-cpv IN (71200000 71400000) AND PD>=20260901 SORT BY publication-date DESC",
    "fields": ["publication-number","notice-title","buyer-name",
               "classification-cpv","deadline","notice-type","place-of-performance"],
    "limit": 100,
    "scope": "ACTIVE",
    "paginationMode": "ITERATION"
  }'
```

Notice-URL bauen als `https://ted.europa.eu/de/notice/-/detail/<publication-number>`.

Mehrsprachige Felder kommen als Objekt (`{"deu": [...], "eng": [...]}`) — beim
Parsen `deu` bevorzugen, sonst erste vorhandene Sprache.

### 2.2 Datenservice Öffentlicher Einkauf (DÖE)

- **Basis:** `https://www.oeffentlichevergabe.de`
- **Swagger:** `/documentation/swagger-ui/opendata/index.html`
  (bekannte Operation: `getExportAsEforms`)
- **Formate:** eForms-DE (XML/UBL), OCDS (JSON), CSV
- **Auth:** keine
- **Lizenz:** CC0

**Wichtige Warnung zum Format:** Der OCDS-Export ist verlustbehaftet. Nach
Auswertung durch Datennachnutzer enthält er die **Angebotsfrist grundsätzlich
nicht** — die steht nur in der Original-Bekanntmachung hinter der `source_url`.
Da die Frist für dich das zentrale Steuerungsfeld ist: **eForms-DE als
Primärformat verwenden**, OCDS höchstens für schnelle Übersichten.

> **Prototyp-Aufgabe 1:** Swagger im Browser öffnen, die exakten Pfade,
> Query-Parameter und das Delta-Verhalten (Datumsfilter? Paging? tägliche
> Vollexporte?) notieren. Das ist die einzige Unbekannte, die vor dem Bauen
> geklärt sein muss.

**Optional später:** Peppol-Profil „P006 – Search Notices", Peppol-ID
`0204:994-bkms-22`, für tagesaktuellen selektiven Abruf. Erfordert einen
zertifizierten Access Point — für den Prototyp nicht relevant.

### 2.3 Nicht im Prototyp

| Quelle | Warum später |
|---|---|
| Kammer-Wettbewerbslisten (16 Kammern, AKNW als CSV) | manuelle Konnektoren, geringes Volumen |
| Landes-/Kommunalportale (cosinex, AI AG, subreport …) | unterschwellig, AGB-Fragen, XVergabe-Weg |
| Private Auslober | keine strukturierte Quelle |

### 2.4 Überschneidung

DÖE und TED überlappen im oberschwelligen Bereich fast vollständig. Für den
Prototyp genügt **eine** Quelle. Empfehlung: **DÖE zuerst**, weil eForms-DE die
nationalen Zusatzfelder trägt und die Lizenz eindeutig CC0 ist. TED als zweite
Quelle zur Absicherung und für Historie.

---

## 3. Filterkaskade

Drei Stufen, bewusst getrennt, damit jede einzeln nachvollziehbar und
justierbar bleibt.

### Stufe 1 — Harte Filter (deterministisch)

**CPV-Set (gegen die offizielle CPV-Codeliste validieren):**

```
71200000  Dienstleistungen von Architekturbüros
71210000  Beratung im Bereich Architektur
71220000  Architekturentwurf
71221000  … bei Gebäuden
71222000  … bei Außenanlagen
71223000  … bei Gebäudeerweiterungsbauten
71240000  Architektur-, Ingenieur- und Planungsleistungen
71250000  Architektur-, Ingenieur- und Vermessungsleistungen
71320000  Planungsleistungen im Bauwesen
71400000  Stadtplanung und Landschaftsgestaltung
71410000  Stadtplanung
71420000  Landschaftsgestaltung
71530000  Bauberatung
71540000  Bauleitung
```

Für den Prototyp reicht `71200000` und `71400000` als Präfix-Match auf den
ersten vier Stellen. Verfeinerung erst nach Sichtung echter Treffer.

**Weitere harte Kriterien:** Land DE; NUTS-Region (Radius um den Bürostandort
oder Positivliste von Bundesländern); Bekanntmachungsdatum im Delta-Fenster;
Frist noch nicht abgelaufen; Notice-Subtype in der Positivliste.

**Relevante eForms Notice-Subtypes:**

| Subtype | Bedeutung |
|---|---|
| 23 | `cn-desg` Wettbewerbsbekanntmachung, allgemeine Richtlinie |
| 24 | `cn-desg` Wettbewerbsbekanntmachung, Sektorenrichtlinie |
| 16 | Auftragsbekanntmachung, offenes Verfahren |
| 9 | Wettbewerblicher Dialog |
| 29 | Vorinformation (6–12 Monate Vorlauf) |
| 39 | Zuschlagsbekanntmachung (für die spätere Erfolgsstatistik) |
| — | Change Notices für Fristverschiebungen und Korrekturen |

### Stufe 2 — Semantischer Filter

CPV allein reicht nicht: Vergabestellen kodieren unsauber, ein reiner
CPV-Filter erzeugt gleichzeitig Rauschen und Lücken. Zweite Stufe über Titel
und Kurzbeschreibung gegen ein hinterlegtes Büroprofil.

Ausgabe pro Treffer: **Score plus Begründung in einem Satz**, nicht nur eine
Zahl. Nur so lässt sich der Filter überhaupt justieren.

Für den Prototyp genügt ein einfacher LLM-Aufruf pro Notice mit dem Büroprofil
im Prompt. Embeddings und Vektorindex erst, wenn das Volumen es rechtfertigt —
bei wenigen tausend Notices pro Jahr tut es das nicht.

### Stufe 3 — Menschliche Auswahl

Trefferliste mit drei Aktionen: relevant / nicht relevant / später ansehen.
Die Entscheidungen werden gespeichert und sind das Trainingsmaterial für die
spätere Verbesserung von Stufe 2. Ohne diese Rückkopplung bleibt der Filter
statisch.

---

## 4. Datenmodell (minimal)

```sql
source            -- Quelle, Lizenz, letzter erfolgreicher Abruf
raw_notice        -- Rohdokument unverändert, Hash, Abrufzeitpunkt
notice            -- normalisierte Felder (siehe unten)
notice_cluster    -- Zusammenführung derselben Ausschreibung über Quellen
buyer             -- Auftraggeber, aus Notices abgeleitet, mit Alias-Tabelle
assessment        -- Score, Begründung, Modellversion, Zeitpunkt
decision          -- menschliche Auswahl, Nutzer, Zeitpunkt, Notiz
```

**Felder in `notice` für den Prototyp:**

`quelle`, `publication_number`, `notice_subtype`, `veroeffentlicht_am`,
`titel`, `beschreibung`, `auftraggeber_name`, `auftraggeber_id`,
`erfuellungsort_nuts`, `erfuellungsort_text`, `cpv_haupt`, `cpv_neben[]`,
`verfahrensart`, `auftragswert`, `frist_teilnahmeantrag`, `frist_angebot`,
`unterlagen_url`, `notice_url`, `version`, `ersetzt_durch`

**Drei Anforderungen, die man nicht nachträglich einbaut:**

1. **Rohdaten unverändert aufbewahren.** `raw_notice` ist immutable. Wenn die
   Normalisierung später falsch war, lässt sich nur so reparieren.
2. **Versionierung.** Fristen werden verschoben, Verfahren aufgehoben. Eine
   neue Version ersetzt die alte, löscht sie aber nicht. Feld `ersetzt_durch`.
3. **Idempotenz.** Der Job muss beliebig oft mit demselben Zeitfenster laufen
   können, ohne Duplikate zu erzeugen. Schlüssel: Quelle + publication_number
   + Version.

Deduplizierung über Quellen (`notice_cluster`) erst, wenn die zweite Quelle
dazukommt. Im Ein-Quellen-Prototyp nicht nötig.

---

## 5. Architektur

```
Scheduler (täglich)
   │
   ├─► Connector DÖE ──┐
   └─► Connector TED ──┤ (Phase 2)
                       ▼
                  raw_notice  ──────► Objektspeicher (später: ZIPs)
                       │
                       ▼
              Normalisierung (eForms-DE → notice)
                       │
                       ▼
            Stufe 1: harte Filter (SQL)
                       │
                       ▼
            Stufe 2: semantische Bewertung (LLM)
                       │
                       ▼
              Trefferliste / Benachrichtigung
                       │
                       ▼
            Stufe 3: Auswahl durch Nutzer
                       │
                       ▼
          ZIP-Abruf über unterlagen_url  ──► 00_Original
```

**Technikvorschlag Prototyp:** PostgreSQL als einziger Speicher (relational +
JSONB für die Rohdaten), Python-Job im Container, Cron oder n8n als
Scheduler, Ausgabe zunächst als Markdown-Mail oder einfache Tabelle. Kein
Frontend in Phase 1.

**Dimensionierung:** Deutschlandweit grob 100.000–150.000 Bekanntmachungen pro
Jahr, davon nach Architektur-CPV-Filter nur wenige Tausend. Metadaten sind
trivial klein. Volumen entsteht erst bei den ZIPs — Wettbewerbsauslobungen
liegen bei 50–500 MB pro Verfahren, aber nur für die tatsächlich ausgewählten.

---

## 6. Rechtliche Leitplanken

| Quelle | Nutzung |
|---|---|
| DÖE Open Data | CC0, uneingeschränkt |
| TED Search API | frei, kommerziell eingeschlossen (Beschluss 2011/833/EU) |
| Vergabeunterlagen oberschwellig | § 41 Abs. 1 VgV: unentgeltlich, uneingeschränkt, vollständig, direkt — nach Verordnungsbegründung ausdrücklich ohne vorherige Registrierung |
| competitionline, wettbewerbe aktuell | **nicht** scrapen — AGB und Datenbankherstellerrecht §§ 87a ff. UrhG |
| Kommerzielle Vergabeportale | AGB prüfen, offizieller Weg über XVergabe/Betreiber |

Beim Abruf: identifizierbarer User-Agent mit Kontaktadresse, konservative
Rate-Limits, robots.txt respektieren, keine Umgehung von Zugangsschranken.

---

## 7. Prototyp-Umfang (Phase 1)

**Ziel:** In einer Woche eine tägliche Trefferliste, die man neben
competitionline legen und vergleichen kann.

1. Swagger des DÖE lesen, Endpunkte und Delta-Mechanik festhalten
2. Ein Tagesabzug ziehen, roh speichern, eine Handvoll eForms-XML von Hand
   ansehen — welche Felder sind wirklich gefüllt?
3. Schema für `raw_notice` und `notice` anlegen, Normalisierung schreiben
4. Harte Filter über CPV + NUTS + Frist
5. Semantische Stufe mit Büroprofil im Prompt
6. Ausgabe als Liste mit Titel, Auftraggeber, Ort, Frist, Score, Begründung,
   Link zur Bekanntmachung, Link zu den Unterlagen
7. Täglicher Lauf

**Abnahmekriterium:** Vier Wochen parallel zu competitionline laufen lassen.
Die Differenzmenge in beide Richtungen ist die Entscheidungsgrundlage für
alles Weitere.

## 8. Ausbaustufen danach

- **Phase 2** — TED als zweite Quelle, Deduplizierung über `notice_cluster`
- **Phase 3** — automatischer ZIP-Abruf, Übergabe an `00_Original`
- **Phase 4** — Kammerlisten für unterschwellige Wettbewerbe
- **Phase 5** — Zuschlagsbekanntmachungen (Subtype 39) einlesen, eigene
  Erfolgsstatistik nach Auftraggeber, Objekttyp und Wettbewerbsbetreuer;
  speist Stufe 2 zurück

---

## 9. Offene Punkte

- Exakte DÖE-Endpunktpfade und Delta-Parameter — nur aus dem Swagger
- Ob der DÖE-Export das Feld für die Unterlagen-URL zuverlässig füllt oder ob
  dafür das vollständige eForms-XML gezogen werden muss
- CPV-Set gegen echte Treffer verifizieren: welche Codes verwenden Auslober
  für Planungswettbewerbe tatsächlich?
- Regionsdefinition: Radius, Bundesländer oder freie Positivliste?
- Schwelle für die semantische Stufe — lieber zu viele Treffer am Anfang
