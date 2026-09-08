# ADR 0003: Filtertaxonomie und schlanker NUTS-Radius

**Datum:** 2026-09-08  
**Status:** akzeptiert

## Kontext

Die Übersicht braucht fachliche Mehrfachfilter für Objektart und Leistungsart,
eine sichtbare Quellenprüfung sowie einen Radius ab Olgastraße 69d in
Stuttgart-Mitte. DÖE und TED enthalten Stadt und NUTS, aber nicht zuverlässig
eine geocodierbare Leistungsadresse.

## Entscheidung

* Leistungsarten werden als versionierte, eigene Taxonomie geführt. Sie wird
  aus CPV-Präfixen und deutschen Textsignalen abgeleitet; sie kopiert weder
  Daten noch Kategorien automatisiert von competitionline.
* Objektarten sind `Bauen im Bestand`, `Neubau` und `Unklar / Mischprojekt`.
  Mischprojekt bleibt standardmäßig sichtbar.
* Der Start-Radius ist Luftlinie mit 25/50/75/100/150 km; 75 km ist Standard.
  Solange keine belastbare Ortskoordinate vorliegt, ist er ein konservativer
  NUTS-Vorfilter. Die GUI benennt das ausdrücklich und zeigt keine erfundene
  Entfernung an.
* Die verwendeten NUTS-Code-Listen werden aus den offiziellen GISCO
  NUTS-2024-Polygonen regeneriert. Ein erster konservativer Präfixsatz sorgt
  dafür, dass kein möglicher regionaler Treffer still verworfen wird.
* Exaktes Geocoding ist eine spätere zweite Stufe: lokaler Ortscache zuerst,
  selbst gehosteter Geocoder nur bei nachgewiesenem Bedarf. Öffentliche
  Nominatim-Instanzen werden nicht für Bulk-Importe verwendet.

## Folgen

Der NUTS-Startfilter kann Randtreffer enthalten; er ist keine exakte
Kilometerberechnung. Sobald ein lokaler Ort/PLZ-Cache Koordinaten liefert,
werden Luftlinie und räumlicher Index ergänzt, ohne die Filter-API zu ändern.
Jede Klassifikation speichert auslösende Regeln für spätere Trefferbegründung.

## Quellen

* GISCO NUTS 2024 GeoJSON: <https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/>
* PostGIS `ST_DWithin`: <https://postgis.net/docs/ST_DWithin.html>
* Nominatim-Nutzungsrichtlinie: <https://operations.osmfoundation.org/policies/nominatim/>
