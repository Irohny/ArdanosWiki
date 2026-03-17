# Vertikale Timeline

Dieses Verzeichnis ist bewusst vom Rest des Projekts getrennt und enthaelt nur den Generator fuer eine vertikale SVG-Timeline.

## Dateien

- `timeline_data.json`: Datenquelle fuer Zeitalter, Weltgeschichte und Herrscher
- `generate_svg.py`: erzeugt aus den Daten eine SVG-Datei

## Ausgabe

Die erzeugte Grafik landet in:

- `World/Images/ardanos_vertical_timeline.svg`

## Aufruf

```bash
/Users/cstruth/spielerei/ArdanosWiki/.venv/bin/python timeline_tools/vertical_svg/generate_svg.py
```

## Aufbau

- Vertikale Zeitachse von oben nach unten
- Separate Spalten fuer Weltgeschichte, Kaiser und Fuerstentuemer
- Blockhoehe entspricht der Dauer des Ereignisses oder der Regentschaft
- Punktuelle Ereignisse werden als Marker gezeichnet

## Hinweis

Die Darstellung ist fuer Obsidian gedacht, aber nicht an Mermaid gebunden. Dadurch laesst sich die Grafik freier und sauberer layouten als mit Gantt- oder Flowchart-Syntax.