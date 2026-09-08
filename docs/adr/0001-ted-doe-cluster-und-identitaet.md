# 0001 — Quellennotices und Vergabeverfahren getrennt modellieren

- **Datum:** 2026-09-08
- **Status:** angenommen

## Kontext

DÖE und TED veröffentlichen für deutsche oberschwellige Vergaben teilweise
dieselbe eForms-Bekanntmachung. Die bisherigen Tabellen speichern eine
Bekanntmachung bewusst quellenbezogen: `source_code + publication_number +
version`. Das ist für Rohdaten und Wiederholungen richtig, würde aber dieselbe
Vergabe in der Oberfläche doppelt zeigen, sobald TED angebunden wird.

Die erste Feldanalyse am Veröffentlichungstag 2026-09-04 belegt außerdem:

- DÖE `noticeIdentifier` ist eine quellspezifische UUID und **nicht** die
  TED-Veröffentlichungsnummer.
- Im DÖE-eForms-XML ist `cbc:ContractFolderID` die Verfahrenskennung.
- Diese Kennung entspricht exakt dem TED-Suchfeld `procedure-identifier`.
  Beispiel: DÖE-Notice `48a398d6-92fb-4f52-af60-d7782f1f87ef` enthält
  `cb6c0f60-837d-4085-99c0-18daf1c23808`; TED liefert für diese Kennung die
  Bekanntmachung `611984-2026`.

Die Veröffentlichungnummer darf damit nicht als quellenübergreifender
Deduplication-Key verwendet werden.

## Entscheidung

1. `notice` bleibt ein quellenbezogener, versionierter Normaldatensatz.
   `raw_notice` bleibt die unveränderte Quelle.
2. Eine neue Ebene `notice_cluster` repräsentiert ein Vergabeverfahren in UI
   und Report. Ein `notice_cluster_member` ordnet jeden Quellendatensatz genau
   einem Cluster zu.
3. Der erste automatische, quellenübergreifende Match ist:
   `DÖE ContractFolderID == TED procedure-identifier`.
4. Jede automatische Zuordnung speichert Methode, Konfidenz und Regelversion.
   Bei fehlender exakter Kennung wird **nicht** still zusammengeführt:
   Der spätere Fallback aus Auftraggeber, Titel, CPV, Ort und Datum erzeugt
   nur einen markierten Prüfhinweis, bis eine belastbare Regel abgenommen ist.
5. Rohdaten, quellspezifische Links und Versionen werden nie im Cluster
   überschrieben. Der Cluster führt nur eine nachvollziehbare,
   feldweise-provenienzierte Darstellung zusammen.

## Folgen

- Die nächste Datenmigration ergänzt `procedure_identifier` an `notice` sowie
  die beiden Clustertabellen und backfillt vorhandene DÖE-Notices.
- Der TED-Connector kann anschließend unabhängig laufen; ein TED-Ausfall
  blockiert den DÖE-Import nicht.
- Die UI wird erst nach dem Backfill auf Cluster umgestellt. Bis dahin bleibt
  die bestehende DÖE-Ansicht unverändert und ohne Datenverlust nutzbar.
- Vor dem produktiven Connector werden weitere Vergleichstage als reproduzier-
  bare Fixtures geprüft, insbesondere Versionen, Änderungsbekanntmachungen und
  Verfahren mit mehreren Losen.

## Quellen

- TED Search API: <https://docs.ted.europa.eu/api/latest/search.html>
- TED-Feldliste (`procedure-identifier`):
  <https://docs.ted.europa.eu/ODS/latest/reuse/field-list.html>
