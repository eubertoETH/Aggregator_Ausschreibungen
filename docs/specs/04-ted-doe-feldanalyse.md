# TED + DÖE — Feldanalyse und Connector-Vertrag

**Stand: 2026-09-08.** Diese Spezifikation dokumentiert die validierte
Vorarbeit für die TED-Anbindung. Sie schaltet noch keinen produktiven
TED-Import ein.

## Manuelle Referenzprobe

Die TED Search API ist ohne API-Key lesbar. Für einen Veröffentlichungstag
werden ausschließlich Suchmetadaten abgerufen; die verlässliche
Normalisierung erfolgt danach aus dem originalen eForms-XML der jeweiligen
Bekanntmachung.

`scripts/probe_ted.py` macht diese Anfrage reproduzierbar, ist aber bewusst
lesend und schreibt keine Produktivdaten.

| Feld | DÖE | TED | Verwendung |
| --- | --- | --- | --- |
| Bekanntmachung | `noticeIdentifier` | `publication-number` | quellenbezogen |
| Version | `noticeVersion` / XML `VersionID` | TED-Version/Änderungsbezug | versioniert |
| Verfahren | XML `ContractFolderID` | `procedure-identifier` | exakter Cluster-Match |
| Inhalt | CSV + deutsches eForms-XML | Search-Result + TED-eForms-XML | normalisieren |
| Quelle/Unterlagen | DÖE XML | TED Links je Sprache/Format | mit Provenienz |

### Nachgewiesener Match

Am 2026-09-04 enthielt DÖE die Bekanntmachung
`48a398d6-92fb-4f52-af60-d7782f1f87ef` mit der eForms-`ContractFolderID`
`cb6c0f60-837d-4085-99c0-18daf1c23808`. Die TED Search API liefert unter
`procedure-identifier = cb6c0f60-837d-4085-99c0-18daf1c23808` die
Veröffentlichung `611984-2026`.

Damit ist der Match über die Verfahrenskennung belegt; die beiden
Bekanntmachungskennungen selbst sind absichtlich verschieden.

## Produktiver Connector-Vertrag

1. Tägliche TED-Suche nach Veröffentlichungstag, iteriert und paginiert.
2. Nur nötige Suchfelder abrufen: Veröffentlichungsnummer, Verfahren,
   Notice-/Form-Type, Titel, Auftraggeber, Datum und format-/sprachabhängige
   Links.
3. Für jeden Treffer das Original-eForms-XML herunterladen und unverändert als
   `raw_notice` mit Hash speichern.
4. Deutsche Fassung bevorzugen; ist sie nicht vorhanden, bleibt die
   verfügbare Originalsprache samt Sprachcode erhalten.
5. TED schreibt in dieselbe normalisierte `notice`-Form wie DÖE, jedoch mit
   `source_code = ted`.
6. Nach jedem Normalisieren erfolgt die Clusterzuordnung: exakte
   Verfahrenskennung zuerst, später ein ausdrücklich markierter Fallback.

## Nicht Teil dieser Stufe

- Kein Scraping von competitionline oder anderer kommerzieller Plattformen.
- Kein unsicheres, automatisches Fuzzy-Merging.
- Keine UI-Umstellung vor Backfill und Abnahmetests.

## Abnahme der nächsten Stufe

- Ein nachgewiesenes DÖE-/TED-Paar besitzt genau einen Cluster mit zwei
  Mitgliedern.
- Quellenspezifische Bekanntmachungen bleiben jeweils eigenständig sichtbar.
- Wiederholte Abrufe ändern keine Rohdatenhistorie und erzeugen keine
  zusätzlichen Mitgliedschaften.
- Frist-, Link- und Inhaltsabweichungen sind je Quelle sichtbar.
