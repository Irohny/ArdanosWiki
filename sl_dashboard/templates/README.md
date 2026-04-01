# Templates fuer das SL-Dashboard

Diese Vorlagen sind auf das aktuelle Dashboard-Layout abgestimmt:

- Session: oberer Header, aktive Szene, linke Navigationsspalte
- Szene: Fokusbereich in der Mitte und Szenenauswahl links
- Ort: Detailansicht rechts und Orts-Tab links
- NPC: Detailansicht rechts und NSC-Tab links
- Monster: Monster-Tab links und Bestiarium-Detail rechts

Empfohlene Nutzung:

- erst eine Session anlegen
- danach Szenen mit `scene_ids` verknuepfen
- Orte und NSCs ueber ihre `id` in Szenen und Sessions referenzieren

Hinweis:

Alle Vorlagen liegen bewusst als Markdown mit YAML-Frontmatter vor. So lassen
sie sich direkt in Obsidian schreiben und bleiben trotzdem maschinenlesbar fuer
den Loader.

Empfohlenes Format:

- technisches Feldset im Frontmatter, zum Beispiel `id`, Referenzdatei und optionale Overrides
- Session-Dateien halten nur Sitzungsmetadaten und die Reihenfolge der Szenen
- Szenen tragen ihren Inhalt direkt in Markdown-Abschnitten und definieren ueber `[[...]]` die relevanten Orte, NSCs und Monster
- Orte, NSCs und Monster koennen als kompakte Referenzdateien nur auf World-Markdown zeigen
- Listen, Zitate und Unterueberschriften koennen innerhalb der Abschnitte frei
	genutzt werden
