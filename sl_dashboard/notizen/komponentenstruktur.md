# Komponentenstruktur

## Ziel

Die Struktur soll frueh trennen zwischen Datenmodell, Darstellung und
spaeterer Integration in die bestehende App.

## Ordner

### components/

- shell.py: oberes Layout des SL-Dashboards
- session_status.py: linker Statusbereich
- scene_focus.py: aktive Szene und Folgeszenen
- quick_access.py: Pins, Schnellzugriffe und relevante NSCs
- toolbox.py: Werkzeuge und kurze SL-Notizen

### data/

- reserviert fuer spaetere Sitzungsdaten, JSON- oder YAML-Dateien

## Python-Module im Wurzelordner

- models.py: gemeinsame Dataklassen fuer Dashboard-Inhalte
- demo_data.py: statische Beispieldaten fuer den schnellen UI-Aufbau
- __init__.py: zentraler Einstiegspunkt fuer spaetere Integration

## Vorteil dieser Aufteilung

- UI-Module bleiben klein
- Daten koennen spaeter aus Dateien statt aus Dummydaten kommen
- bestehende Komponenten wie Encounter-Rechner lassen sich gezielt in
  toolbox.py oder eigene Module ueberfuehren
