# Vertikale Timeline

Dieses Verzeichnis ist bewusst vom Rest des Projekts getrennt und enthaelt
den Generator fuer die Reichs- und Fuerstentums-Timelines als vertikale SVGs.

## Dateien

- `timeline_data.json`: Datenquelle fuer die Reichs-Timeline
- `timeline_data_<profil>.json`: Datenquellen fuer Fuerstentums-Timelines
- `generate_svg.py`: erzeugt aus einer oder mehreren JSON-Dateien SVG-Dateien

## Ausgabe

Die erzeugten Grafiken landen in:

- `World/Images/Timelines/ardanos_vertical_timeline.svg`
- `World/Images/Timelines/elmrath_vertical_timeline.svg`
- `World/Images/Timelines/drakmora_vertical_timeline.svg`
- `World/Images/Timelines/mariven_vertical_timeline.svg`
- `World/Images/Timelines/schwarzklamm_vertical_timeline.svg`
- `World/Images/Timelines/vaylen_vertical_timeline.svg`

## Build-Ablauf

1. Metadaten scannen und Timeline-JSON-Dateien bauen:

```bash
uv run python wiki_dasboard/extraktion_tools/metadata_extractor/build_timeline_json.py
```

1. Alle vorhandenen Timeline-JSON-Dateien zu SVG rendern:

```bash
uv run python wiki_dasboard/extraktion_tools/vertical_svg/generate_svg.py
```

1. Optional nur einzelne Profile bauen:

```bash
uv run python wiki_dasboard/extraktion_tools/metadata_extractor/build_timeline_json.py drakmora mariven
```

1. Optional nur einzelne JSON-Dateien rendern:

```bash
uv run python wiki_dasboard/extraktion_tools/vertical_svg/generate_svg.py \
  wiki_dasboard/extraktion_tools/vertical_svg/timeline_data_drakmora.json
```

## Aufruf

```bash
uv run python wiki_dasboard/extraktion_tools/vertical_svg/generate_svg.py
```

## Aufbau

- Vertikale Zeitachse von oben nach unten
- Fuerstentums-Timelines haben Spalten fuer Zeit, Herrscher, Zeitspannen und Zeitpunkte
- Blockhoehe entspricht der Dauer des Ereignisses oder der Regentschaft
- Punktuelle Ereignisse werden als Marker gezeichnet

## Hinweis

Die Darstellung ist fuer Obsidian gedacht, aber nicht an Mermaid gebunden.
Dadurch laesst sich die Grafik freier und sauberer layouten als mit
Gantt- oder Flowchart-Syntax.
