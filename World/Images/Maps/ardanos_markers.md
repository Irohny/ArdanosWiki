# Ardanos-Karte erweitern

Die Kartendaten liegen in `ardanos_markers.json`. Prozentkoordinaten beziehen sich auf das Kartenbild: `x` ist der Abstand vom linken Rand, `y` der Abstand vom oberen Rand. Beide Werte liegen zwischen `0` und `100`.

## Markertyp und Icon festlegen

Jeder Typ wird einmal unter `marker_types` beschrieben:

```json
"Hafen": {
  "shape": "icon",
  "icon": "⚓",
  "color": "#356b8c"
}
```

`shape` ist `icon` für ein Symbol oder `dot` für einen farbigen Punkt. `icon` kann ein Emoji oder ein anderes Unicode-Zeichen sein. `color` ist ein HEX-Farbwert. Fehlt eine Typdefinition, wird ein neutrales Symbol mit Standardfarbe verwendet.

## Punkt eintragen

Ergänze das Array `markers` um einen Eintrag:

```json
{
  "name": "Leuchtturm",
  "type": "Hafen",
  "x": 12,
  "y": 30,
  "page": "Kaiserreich/Mariven/Leuchtturm.md"
}
```

`type` muss mit einem Eintrag in `marker_types` übereinstimmen, damit das gewünschte Icon und die Farbe verwendet werden. Neue Typen mit Markern erscheinen automatisch in der Filterauswahl.

`page` ist der Pfad zur Wiki-Seite relativ zum Ordner `World/`; schreibe also nicht `World/` davor. Die Datei muss vorhanden und für den aktuellen Nutzer sichtbar sein, damit der Punkt angezeigt und geöffnet werden kann.

## Regionen

Regionen stehen im Array `regions`. `page` verweist ebenfalls relativ zu `World/` auf die Zielseite. Eine einzelne Fläche verwendet `points`, mehrere getrennte Flächen verwenden `polygons`. Die Polygonkoordinaten nutzen dasselbe Prozentformat wie Marker.
