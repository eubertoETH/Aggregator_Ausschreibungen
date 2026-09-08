# 0002 — Quellen unabhängig importieren, Verfahren einmal darstellen

- **Datum:** 2026-09-08
- **Status:** angenommen

## Kontext

Nach der Cluster-Grundlage liefert TED eigene Suchmetadaten und originale
eForms-XML-Dokumente. DÖE und TED können temporär unterschiedlich verfügbar
sein oder verschiedene Felder derselben Vergabe liefern.

## Entscheidung

1. DÖE und TED laufen im Scheduler als getrennte Jobs. Ein Fehler einer Quelle
   wird geloggt, blockiert die andere Quelle und den Tagesreport aber nicht.
2. TED speichert Search-Result und Original-XML unverändert in `raw_notice`
   sowie im Quellenarchiv. Der Startumfang ist Deutschland über
   `place-of-performance-country-lot = DEU`.
3. Die UI und der Report lesen aus `notice_cluster`, nicht mehr direkt aus
   quellenbezogenen Notices. Ein Cluster erscheint genau einmal.
4. Für die Darstellung werden nicht leere Felder deterministisch gewählt:
   DÖE vor TED, anschließend der jeweils vorhandene Wert. Alle Quellenlinks
   bleiben sichtbar. Abweichende Kerndaten werden markiert, nicht verborgen.
5. Der Fallback für nicht identische Verfahren bleibt deaktiviert. Seine
   Kandidatenlogik muss später getrennt versioniert, testbar und überprüfbar
   eingeführt werden.

## Folgen

- Quellen-Badges und mehrere Quelllinks machen Zusammenführungen nachvollziehbar.
- Die Reihenfolge ist keine Aussage über rechtliche Verbindlichkeit; sie dient
  nur einer stabilen deutschsprachigen Darstellung.
- Ein manueller `POST /imports/ted/YYYY-MM-DD` ermöglicht die kontrollierte
  Nachladung eines Vergleichstags ohne den Scheduler abzuwarten.
