# Erste Ideen fuer das SL-Dashboard

## Produktziel

Das SL-Dashboard soll Obsidian beim Leiten ersetzen.
Die Anwendung soll nicht nur Dateien anzeigen, sondern als aktive
Arbeitsflaeche fuer eine laufende Sitzung dienen.

## Kernprinzip

Trennung von zwei Modi:

- Wiki-Modus zum Nachschlagen
- SL-Modus zum Fuehren einer Sitzung

Das Dashboard sollte daher nicht aus einer Liste von Links bestehen,
sondern aus kontextbezogenen Modulen.

## Empfohlene Hauptbereiche

### 1. Sitzungsstatus

- aktuelle Sitzung
- Ingame-Datum und Ort
- aktive Szene
- naechste 2 bis 3 Szenen
- offene Plotfaeden

### 2. Aktive Szene

- Kurzbeschreibung fuer die SL
- beteiligte NSCs
- wichtige Hinweise
- moegliche Eskalationen
- direkte Links zu Orten, NSCs und Abenteuerseiten

### 3. Schnellzugriffe

- gepinnte Seiten
- kuerzlich geoeffnete Seiten
- heute vorbereitete Inhalte
- wichtige Regeln und Referenzen

### 4. Werkzeuge

- Encounter-Rechner
- NSC-Schnellansicht
- Monster-Quick-Stats
- kurze Sitzungsnotizen
- spaeter eventuell Initiativ- oder Clock-Modul

## Vorschlag fuer ein MVP

Ein erster brauchbarer Stand koennte aus diesen Teilen bestehen:

- neues SL-Cockpit als eigener Dashboard-Modus
- Bereich fuer gepinnte Seiten
- Karte fuer aktuelle Szene
- Liste mit relevanten NSCs
- eingebetteter Encounter-Rechner
- einfache private Sitzungsnotizen

## Moegliches Datenmodell

Sinnvoll waere ein separates Sitzungsformat, das nicht direkt in den
Lore-Dateien lebt.
Beispielhafte Inhalte:

- sitzungstitel
- datum
- ort
- aktive_szene
- naechste_szenen
- pins
- aktive_nscs
- offene_faeden
- notizen

## Offene Designfragen

- Wie werden Pins gesetzt: global, pro Sitzung oder beides?
- Sollen Sitzungsnotizen als Markdown, JSON oder YAML-Metadaten gespeichert werden?
- Soll das SL-Dashboard einen eigenen Navigationseintrag bekommen oder
  vom Home aus starten?
- Welche Daten koennen direkt aus vorhandenen World-Dateien gelesen
  werden und was braucht neue Strukturen?

## Erste Entwicklungsreihenfolge

1. Zielbild und Module festzurren
2. Datenstruktur fuer Sitzungen definieren
3. Dummy-Dashboard mit statischen Karten bauen
4. Pins und Szenendaten anbinden
5. vorhandene Tools integrieren
