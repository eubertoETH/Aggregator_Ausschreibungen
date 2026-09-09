# ADR 0004: Gemeinsame Merkliste und belastbarer Arbeitsstatus

## Kontext

Die Trefferliste wird von einem gemeinsamen Büro ohne Benutzerkonten genutzt.
Sie braucht eine einfache Arbeitsliste und einen verständlichen Friststatus,
ohne fehlende Vergabedaten als Tatsachen auszugeben.

## Entscheidung

- Ein Lesezeichen ist global: Alle Nutzerinnen und Nutzer derselben Instanz
  sehen dieselbe Merkliste.
- Jede gemerkte Ausschreibung kann eine optionale Kurznotiz erhalten.
- Der Schnellfilter **Gemerkte Projekte** zeigt nur diese Arbeitsliste.
- Der Status wird aus Teilnahme- bzw. Angebotsfrist abgeleitet:
  - mehr als 7 Tage,
  - noch 1–7 Tage,
  - Frist abgelaufen.
- **Entschieden** wird ausschließlich für ausdrücklich als Ergebnis-/Award-
  Bekanntmachung gekennzeichnete Quellendatensätze gesetzt; eine vergangene
  Frist allein ist kein Zuschlag.
- **Unterschwelle** wird nur für ein explizites nationales bzw.
  Unterschwellen-Signal aus der Quelle gefiltert. Geschätzte Werte und
  fehlende Werte werden nicht zur Vermutung verwendet.
- Standardmäßig zeigt die Liste nur die beiden noch offenen Friststatus.
  Abgelaufene und entschiedene Verfahren werden gezielt zugeschaltet.

## Folgen

Die Merkliste ist bewusst nicht personenbezogen. Eine spätere Anmeldung kann
sie auf Nutzerprofile erweitern, ohne die fachlichen Ausschreibungsdaten zu
ändern. Unbekannte oder nicht eindeutig klassifizierbare Verfahren bleiben
sichtbar, wenn kein entsprechender restriktiver Filter aktiv ist.
