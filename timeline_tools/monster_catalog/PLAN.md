# Plan: Monster-Katalog aus dem Bestiarium extrahieren

## Ziel

Der Monster-Katalog soll aus den Markdown-Dateien in World/Bestiarium erzeugt und als generierte Datei gespeichert werden.
Die Erzeugung soll extern triggerbar sein, analog zur Timeline-Pipeline.
Die Encounter-Berechnung soll danach nicht mehr ihren Profilkatalog im Code pflegen, sondern die generierte Katalogdatei laden.

## Zielbild

Es gibt am Ende drei Schichten:

1. Quellmaterial:
   World/Bestiarium/*.md

2. Extraktions-Pipeline:
   timeline_tools/monster_catalog/
   - scan_bestiary.py
   - validate_monsters.py
   - build_monster_catalog.py
   - extracted_monsters.json
   - validation_report.md
   - monster_catalog.json

3. Laufzeitnutzung:
   components/encounter_calculator.py lädt monster_catalog.json und baut daraus die Monsterprofile für die Encounter-Berechnung.

## Orientierung an der Timeline-Pipeline

Die Pipeline soll sich am bestehenden Muster aus timeline_tools/metadata_extractor orientieren:

1. scan_bestiary.py
   Liest alle Dateien unter World/Bestiarium/*.md
   Extrahiert Rohdaten und speichert sie in extracted_monsters.json

2. validate_monsters.py
   Prüft Pflichtfelder, CR, Rollen-Tags, Boss-Flags und Katalog-Key
   Schreibt validation_report.md

3. build_monster_catalog.py
   Baut aus den validen Rohdaten eine kompakte Laufzeitdatei monster_catalog.json

4. just-Task
   Ein neuer just-Task soll die Pipeline einmal komplett ausführen, ähnlich wie just svg

## Empfohlene Dateistruktur für generierte Artefakte

Empfohlenes Verzeichnis:

- timeline_tools/monster_catalog/

Empfohlene Dateien:

- timeline_tools/monster_catalog/extracted_monsters.json
  Rohdaten aus dem Scan, inklusive Metadaten und Parse-Ergebnis

- timeline_tools/monster_catalog/validation_report.md
  Menschlich lesbarer Prüfbericht mit fehlenden Feldern und Inkonsistenzen

- timeline_tools/monster_catalog/monster_catalog.json
  Finale Laufzeitdatei für den Encounter-Rechner

## Empfohlenes Format der Laufzeitdatei

monster_catalog.json sollte bewusst kompakt und UI-freundlich sein.
Wichtig ist dabei die Trennung zwischen redaktionellen Rohsignalen und berechneten Laufzeitfeldern.

Beispielstruktur:

```json
{
  "version": 1,
  "generated_at": "2026-03-23",
  "source_root": "World/Bestiarium",
  "profiles": [
    {
      "key": "zerra_die_fluesterin",
      "name": "Zerra die Flüsterin",
      "source_path": "World/Bestiarium/Zerra die Flüsterin.md",
      "cr": 6,
      "strategy": "controller",
      "tags": ["CONTROL", "HEIMLICH", "MOBIL", "DEBUFF"],
      "threat_modifier_bonus": 0.12,
      "action_weight_bonus": 0.08,
      "volatility_bonus": 0.18,
      "legendary_actions": false,
      "legendary_resistances": false,
      "phase_change": false,
      "summons": false,
      "confidence": 0.82,
      "hint": "Kontrolllastige Schatten-Warlockin mit Teleport und Unsichtbarkeit.",
      "derived_from": {
        "challenge_rating_raw": "6",
        "challenge_rating_parsed": 6,
        "has_spells": true,
        "spell_count": 4,
        "has_multiattack": false,
        "has_bonus_action": false,
        "has_reaction": false,
        "has_legend_actions_section": false,
        "has_legendary_resistances_text": false,
        "has_teleport": true,
        "has_invisibility": true,
        "has_control_effects": true,
        "has_aoe": false,
        "has_summon_markers": false,
        "has_phase_markers": false,
        "matched_keywords": ["Teleport", "Unsichtbarkeit", "Furcht"],
        "inferred_tags": ["CONTROL", "HEIMLICH", "MOBIL", "DEBUFF"],
        "inferred_strategy": "controller"
      }
    }
  ]
}
```

## Konkretes Schema: extracted_monsters.json

Die Scan-Datei ist die technische Zwischenstufe zwischen Markdown und dem finalen Laufzeitkatalog.
Sie darf ausführlicher sein als die Laufzeitdatei und soll alles enthalten, was Validator und Builder für nachvollziehbare Entscheidungen brauchen.

Empfohlene Struktur:

```json
{
   "version": 1,
   "generated_at": "2026-03-23T19:20:00Z",
   "source_root": "World/Bestiarium",
   "scanner": {
      "name": "scan_bestiary.py",
      "rules_version": 1
   },
   "entries": [
      {
         "source_path": "World/Bestiarium/Zerra die Flüsterin.md",
         "file_name": "Zerra die Flüsterin.md",
         "name": "Zerra die Flüsterin",
         "key": "zerra_die_fluesterin",
         "parse_status": "ok",
         "warnings": [],
         "errors": [],
         "raw_fields": {
            "challenge_rating_raw": "6",
            "alias_raw": "[[Lady Maerina von Elmrath]]",
            "catalog_metadata": {
               "strategy_override": null,
               "tags_override": null,
               "threat_override": null,
               "action_override": null,
               "volatility_override": null,
               "legendary_actions_override": null,
               "legendary_resistances_override": null,
               "phase_change_override": null,
               "summons_override": null,
               "hint": null
            }
         },
         "signals": {
            "parsed_cr": 6,
            "has_spells": true,
            "spell_count": 4,
            "has_multiattack": false,
            "multiattack_count_estimate": 0,
            "has_bonus_action": false,
            "has_reaction": false,
            "has_legend_actions_section": false,
            "has_legendary_resistances_text": false,
            "has_teleport": true,
            "has_invisibility": true,
            "has_flight": false,
            "has_aoe": false,
            "has_control_effects": true,
            "has_summon_markers": false,
            "has_phase_markers": false,
            "has_resistances": false,
            "has_immunities": false,
            "matched_keywords": ["Teleport", "Unsichtbarkeit", "Furcht"]
         },
         "sections": {
            "has_actions_section": true,
            "has_spellcasting_section": true,
            "has_legendary_actions_section": false,
            "has_reactions_section": false,
            "has_bonus_actions_section": false
         },
         "source_excerpt": {
            "cr_line": "- **Stufe/Herausfordungsgrad:** 6",
            "matched_lines": [
               "Teleport ...",
               "Unsichtbarkeit ...",
               "Furcht ..."
            ]
         }
      }
   ]
}
```

### Feldbedeutung für extracted_monsters.json

- version
   - Schema-Version der Zwischenstufe
- generated_at
   - UTC-Zeitpunkt der Scanner-Ausführung
- source_root
   - gescannter Markdown-Wurzelpfad
- scanner.name
   - Name des erzeugenden Skripts
- scanner.rules_version
   - Version der Heuristikregeln für spätere Vergleichbarkeit
- entries
   - Liste aller gescannten Monsterdateien, auch bei Warnungen oder Fehlern
- parse_status
   - ok, warning oder error
- warnings
   - nicht-blockierende Auffälligkeiten
- errors
   - blockierende Parse-Probleme
- raw_fields
   - direkt gelesene Werte ohne Interpretation
- signals
   - normalisierte Rohsignale für den Builder
- sections
   - erkannte Abschnittsstruktur zur Debugbarkeit
- source_excerpt
   - wenige textuelle Nachweise für Parser und Validator, keine vollständige Duplizierung der Quelldatei

## Konkretes Schema: monster_catalog.json

Der Laufzeitkatalog bleibt bewusst kompakt. Er enthält nur das, was der Encounter-Rechner direkt konsumieren soll, plus Explainability für Debugging und Nachvollziehbarkeit.

Empfohlene Struktur:

```json
{
   "version": 1,
   "generated_at": "2026-03-23T19:22:00Z",
   "source_root": "World/Bestiarium",
   "builder": {
      "name": "build_monster_catalog.py",
      "rules_version": 1
   },
   "profiles": [
      {
         "key": "zerra_die_fluesterin",
         "name": "Zerra die Flüsterin",
         "source_path": "World/Bestiarium/Zerra die Flüsterin.md",
         "cr": 6,
         "strategy": "controller",
         "tags": ["CONTROL", "HEIMLICH", "MOBIL", "DEBUFF"],
         "threat_modifier_bonus": 0.12,
         "action_weight_bonus": 0.08,
         "volatility_bonus": 0.18,
         "legendary_actions": false,
         "legendary_resistances": false,
         "phase_change": false,
         "summons": false,
         "confidence": 0.82,
         "hint": "Kontrolllastige Schatten-Warlockin mit Teleport und Unsichtbarkeit.",
         "notes": [],
         "overrides_applied": [],
         "derived_from": {
            "challenge_rating_raw": "6",
            "challenge_rating_parsed": 6,
            "has_spells": true,
            "spell_count": 4,
            "has_multiattack": false,
            "has_bonus_action": false,
            "has_reaction": false,
            "has_legend_actions_section": false,
            "has_legendary_resistances_text": false,
            "has_teleport": true,
            "has_invisibility": true,
            "has_control_effects": true,
            "has_aoe": false,
            "has_summon_markers": false,
            "has_phase_markers": false,
            "matched_keywords": ["Teleport", "Unsichtbarkeit", "Furcht"],
            "inferred_tags": ["CONTROL", "HEIMLICH", "MOBIL", "DEBUFF"],
            "inferred_strategy": "controller"
         }
      }
   ]
}
```

### Feldbedeutung für monster_catalog.json

- builder.name
   - Name des Builder-Skripts
- builder.rules_version
   - Version der Ableitungslogik
- profiles
   - nur valide und gebaute Laufzeitprofile
- overrides_applied
   - Liste der tatsächlich angewandten Override-Felder, damit man manuelle Eingriffe erkennen kann
- notes
   - optionale Builder- oder Validierungshinweise, die im Laufzeitkatalog sichtbar bleiben sollen

## Datenfluss zwischen den Dateien

Die drei Pipeline-Schritte bekommen damit einen klaren Vertrag:

1. scan_bestiary.py
    - erzeugt extracted_monsters.json mit raw_fields, signals, sections und parse_status

2. validate_monsters.py
    - prüft extracted_monsters.json
    - erzeugt validation_report.md
    - markiert Fehlerfälle, ohne die Rohdaten zu verlieren

3. build_monster_catalog.py
    - liest extracted_monsters.json
    - ignoriert Einträge mit parse_status error oder harten Validierungsfehlern
    - berechnet strategy, tags und numerische Boni
    - wendet danach optionale Overrides an
    - schreibt monster_catalog.json

## Minimale Builder-Regeln

Damit Scanner und Builder nicht inhaltlich auseinanderlaufen, sollten die Mindestregeln bereits im Plan fixiert werden.

### Reihenfolge der Ableitung

1. Rohwerte und Signale parsen
2. Basisflags ableiten
    - legendary_actions
    - legendary_resistances
    - summons
    - phase_change
3. Tags inferieren
4. strategy inferieren
5. numerische Boni berechnen
6. hint erzeugen, falls kein Override existiert
7. confidence berechnen
8. optionale Overrides anwenden
9. overrides_applied dokumentieren

### Mindest-Clamping für Modellwerte

Empfohlene harte Grenzen:

- threat_modifier_bonus: 0.00 bis 0.35
- action_weight_bonus: 0.00 bis 0.35
- volatility_bonus: 0.00 bis 0.30
- confidence: 0.00 bis 1.00

### Mindestregeln für confidence

confidence soll nicht subjektiv gesetzt werden, sondern aus Signalqualität entstehen.

Beispielhafte Startlogik:

- parsebarer CR vorhanden: +0.20
- Name und Key sauber ermittelt: +0.10
- klare Abschnittssignale vorhanden: +0.10
- mindestens 3 starke Keywords erkannt: +0.10
- strategy eindeutig inferiert: +0.10
- mindestens 2 Tags eindeutig inferiert: +0.10
- Override nötig: kein Bonus, aber auch kein Malus
- zentrale Felder nur aus schwachen Texttreffern: -0.10 bis -0.20
- Widerspruch zwischen Override und Heuristik: -0.10

Die genaue Formel kann später nachkalibriert werden. Wichtig ist nur, dass sie konsistent und reproduzierbar bleibt.

## Datenmodell: Rohsignale, Ableitungen, Overrides

Der Katalog sollte nicht so gedacht sein, dass Markdown-Dateien bereits alle finalen Laufzeitwerte direkt liefern.
Sauberer ist ein dreistufiges Modell:

1. Rohsignale aus dem Markdown
   - direkt auslesbare Struktur- und Textmerkmale

2. Abgeleitete Kampffelder
   - strategy
   - tags
   - threat_modifier_bonus
   - action_weight_bonus
   - volatility_bonus
   - legendary_actions
   - legendary_resistances
   - phase_change
   - summons

3. Optionale redaktionelle Overrides
   - nur für Sonderfälle, in denen die Heuristik bewusst überschrieben werden soll

Damit bleiben die Quelldateien lesbar, während die Builder-Logik die eigentliche Kampfbewertung konsistent erzeugt.

## Welche Daten extrahiert werden sollen

### Pflichtfelder

Diese Felder müssen pro Monster am Ende in der Laufzeitdatei vorhanden sein:

- key
- name
- source_path
- cr
- strategy
- tags
- hint

### Optionale, aber gewünschte Felder

- threat_modifier_bonus
- action_weight_bonus
- volatility_bonus
- legendary_actions
- legendary_resistances
- phase_change
- summons
- confidence
- notes
- derived_from

### Rohsignale aus dem Quelltext

Diese Daten sollten möglichst direkt aus dem Markdown extrahiert werden und nicht erst vom Autor als finale Modellwerte gepflegt werden:

- challenge_rating_raw
- parsed_cr
- has_spells
- spell_count
- has_multiattack
- multiattack_count_estimate
- has_bonus_action
- has_reaction
- has_legend_actions_section
- has_legendary_resistances_text
- has_teleport
- has_invisibility
- has_flight
- has_aoe
- has_control_effects
- has_summon_markers
- has_phase_markers
- has_resistances
- has_immunities
- matched_keywords

### Abgeleitete Laufzeitfelder

Diese Felder sollten bevorzugt im Builder berechnet werden:

- strategy
- tags
- threat_modifier_bonus
- action_weight_bonus
- volatility_bonus
- legendary_actions
- legendary_resistances
- phase_change
- summons
- confidence

### Redaktionelle Overrides

Falls ein Monster durch reinen Text nicht sauber beschrieben ist, kann die Katalog-Metadaten-Sektion optionale Overrides enthalten:

- Strategy-Override
- Tags-Override
- Threat-Override
- Action-Override
- Volatilität-Override
- Beschwörung-Override
- Phasenwechsel-Override
- Katalog-Hinweis

## Empfehlung für die Monsterlayouts

Die aktuellen Bestiarium-Dateien sind für Menschen gut lesbar, aber für zuverlässige Extraktion noch zu frei.
Für die Pipeline ist deshalb eine kleine, standardisierte Katalog-Metadaten-Sektion sinnvoll.

## Empfohlene Layout-Optimierung

Empfohlen wird ein zusätzlicher Metadatenblock am Dateianfang, direkt nach der bestehenden Grundlage-/CR-Sektion.

Beispiel:

```md
- **Grundlage:** #Homebrew
- **Stufe/Herausfordungsgrad:** 6
- **Alias:** [[Lady Maerina von Elmrath]]

## Katalog-Metadaten
- **Katalog-Key:** zerra_die_fluesterin
- **Strategie-Override:** Controller
- **Tags-Override:** Control, Heimlich, Mobil, Debuff
- **Threat-Override:** 0.12
- **Action-Override:** 0.08
- **Volatilität-Override:** 0.18
- **Legendäre Aktionen-Override:** Nein
- **Legendäre Resistenzen-Override:** Nein
- **Phasenwechsel-Override:** Nein
- **Beschwörung-Override:** Nein
- **Katalog-Hinweis:** Kontrolllastige Schatten-Warlockin mit Teleport und Unsichtbarkeit.
```

## Warum dieses Format

Dieses Format ist für Obsidian und für Menschen lesbar, ohne die bestehenden Seiten umzubauen.
Es ist leichter in Regex oder einfachen Zeilenparsern auszuwerten als frei interpretierte Fließtexte.

## Alternative

YAML-Frontmatter wäre technisch sauberer, aber im aktuellen Repo ist das bestehende Listenformat bereits etabliert.
Für minimale Reibung ist deshalb eine standardisierte Katalog-Metadaten-Sektion sinnvoller als ein harter Wechsel auf Frontmatter.

## Extraktionsstrategie

### Phase 1: explizite Metadaten als Override lesen

Der Extraktor liest zuerst die Katalog-Metadaten-Sektion.
Wenn sie vorhanden ist, werden die Werte nicht blind als Wahrheit übernommen, sondern als explizite Overrides auf ein ansonsten automatisch abgeleitetes Profil gelegt.

### Phase 2: Rohsignale aus dem Text extrahieren

Der Scanner extrahiert aus den bestehenden Markdown-Daten strukturierte Signale:

- Name aus Dateiname oder erstem H1
- CR aus Stufe/Herausfordungsgrad
- Vorhandensein von Zaubern
- Anzahl der Zauber oder Zauberblöcke
- Mehrfachangriff und geschätzte Angriffszahl
- Bonusaktionen
- Reaktionen
- Abschnitte zu Legendenaktionen
- Hinweise auf Legendäre Resistenzen
- Resistenzen und Immunitäten
- Teleport, Flug, Unsichtbarkeit, Heimlichkeit
- Flächeneffekte und Auren
- Kontrollbegriffe wie Furcht, Betäubung, Verlangsamung, Aktion verlieren
- Beschwörungsmarker
- Phasen- oder Transformationsmarker

### Phase 3: heuristische Ableitung der Profilwerte

Aus diesen Rohsignalen werden die finalen Profilwerte abgeleitet:

- CR aus Stufe/Herausfordungsgrad
- legendary_actions aus Abschnitt Legendenaktionen mit Inhalt
- legendary_resistances aus klaren Textmarkern wie Legendäre Resistenz oder Legendäre Resistenzen
- summons bei Begriffen wie Beschwörung, ruft, beschwört, Adds
- phase_change bei Begriffen wie Phase 2, Phase 3, Phasenwechsel
- CONTROL bei Begriffen wie Furcht, Verlangsamen, verliert Aktion, Betäubung, Unsichtbarkeit nur situativ nicht direkt
- MOBIL bei Teleport, Nebelschritt, Schattenschritt, große Bewegung, Flug
- HEIMLICH bei Heimlichkeit, Unsichtbarkeit, Verstecken, Assassine
- FERNKAMPF bei Fernkampfwaffen, Bögen, Strahlen, Projektilzaubern
- BURST bei hohem Alpha Strike, Hinterhältiger Angriff, Krit-Effekten, starkem Spike-Schaden
- FLAECHE bei allen Kreaturen im Umkreis, Flächenzaubern, Aura-Schaden
- DEBUFF bei Nachteil, Blind, Verstummen, Altern, Statussenkung
- TANK bei hoher RK, vielen HP, Resistenzen, Reaktionsschutz, Schadensreduktion

Zusätzlich sollte eine primäre strategy abgeleitet werden. Empfohlene Strategien:

- brute
- skirmisher
- controller
- artillery
- assassin
- summoner
- defender
- boss

Die strategy wird über ein Punktesystem aus Tags und Rohsignalen bestimmt.

### Phase 4: numerische Modellwerte berechnen

Die drei numerischen Boni sollten bevorzugt berechnet und nicht redaktionell gepflegt werden.

#### action_weight_bonus

Beschreibt zusätzliche effektive Wirkung pro Runde durch Aktionsökonomie.

Signale:

- Mehrfachangriff
- Bonusaktion
- Reaktion
- Legendenaktionen
- AoE
- Beschwörung
- Aktionen, die gegnerische Züge neutralisieren

#### threat_modifier_bonus

Beschreibt zusätzliche praktische Gefährlichkeit über reines CR/XP hinaus.

Signale:

- harte Kontrolle
- Fokusfeuerfähigkeit durch Mobilität oder Heimlichkeit
- Burst-Spitzen
- starke Resistenzen oder Immunitäten
- legendäre Resistenzen
- Beschwörung
- Anti-Player-Mechaniken wie Counterspell oder Aktion entziehen

#### volatility_bonus

Beschreibt die Schwankungs- und Eskalationsstärke des Kampfes.

Signale:

- Unsichtbarkeit und Ambush
- Teleport oder starke Repositionierung
- Recharge-ähnliche Spitzenfähigkeiten
- Save-or-suck-Effekte
- Phasenwechsel
- Beschwörung
- starke AoE- oder Burst-Eröffnungen

Alle drei Werte sollten im Builder aus Gewichten berechnet und auf sinnvolle Grenzen geklemmt werden.

### Phase 5: Explainability speichern

Die Ableitung soll nachvollziehbar bleiben.
Dafür enthält jedes Profil ein derived_from-Objekt mit den genutzten Rohsignalen, den gematchten Schlüsselwörtern und den inferierten Tags bzw. der inferierten strategy.

## Validierungsregeln

validate_monsters.py sollte mindestens prüfen:

- Jede Datei hat genau einen Namen und einen parsebaren CR
- Katalog-Key ist eindeutig
- Rollen-Tags sind nur aus einer erlaubten Menge
- strategy ist nur aus einer erlaubten Menge
- numerische Boni liegen in sinnvollen Grenzen
- Boss-Flags sind boolesch
- Katalog-Hinweis ist nicht leer
- Wenn Legendenaktionen aktiviert sind, sollte die Quelle dafür explizit sein oder ein entsprechender Abschnitt existieren
- Wenn Legendäre Resistenzen aktiviert sind, sollte ein Textmarker oder ein Override existieren
- confidence liegt zwischen 0.0 und 1.0
- derived_from enthält bei heuristisch erzeugten Werten mindestens die zentralen Rohsignale

## Empfohlene Tag-Menge

Die extrahierte Datei soll dieselben Tags nutzen wie der Encounter-Rechner:

- BURST
- CONTROL
- TANK
- MOBIL
- FERNKAMPF
- BESCHWOERUNG
- FLAECHE
- DEBUFF
- HEIMLICH

## Empfohlene Strategie-Menge

- brute
- skirmisher
- controller
- artillery
- assassin
- summoner
- defender
- boss

## Umsetzung im Encounter-Rechner

### Aktueller Zustand

Der Profilkatalog lebt aktuell direkt in components/encounter_calculator.py.

### Zielzustand

components/encounter_calculator.py soll monster_catalog.json laden.
Dafür wird eine kleine Ladeschicht ergänzt:

- load_monster_catalog()
- get_monster_profile(profile_key)
- profile_select_label(profile_key)

Wenn die generierte Datei fehlt, kann optional ein kleiner eingebauter Fallback-Katalog aktiv bleiben, damit die App nicht komplett ausfällt.

Wichtig: Die Laufzeitlogik soll die berechneten Werte aus dem JSON konsumieren, nicht die Rohsignale neu interpretieren. Die gesamte Ableitung liegt damit zentral im Builder und bleibt reproduzierbar.

## Vorschlag für den Trigger

Neuer just-Task:

```just
monster-catalog:
    uv run python timeline_tools/monster_catalog/scan_bestiary.py
    uv run python timeline_tools/monster_catalog/validate_monsters.py
    uv run python timeline_tools/monster_catalog/build_monster_catalog.py
```

Optional zusätzlich ein Sammel-Task:

```just
data:
    just svg
    just monster-catalog
```

## Migrationsplan

### Schritt 1

Neues Verzeichnis anlegen:
- timeline_tools/monster_catalog/

### Schritt 2

Scanner bauen:
- scan_bestiary.py

### Schritt 3

Validator bauen:
- validate_monsters.py

### Schritt 4

Katalogbuilder bauen:
- build_monster_catalog.py

### Schritt 5

Erste 10 bis 15 Monsterdateien mit Katalog-Metadaten ergänzen, primär für Overrides und Hinweise

### Schritt 6

Encounter-Rechner auf JSON-Katalog umstellen

### Schritt 7

Heuristik nur noch als Fallback behalten

### Schritt 8

Gewichtungen für strategy, threat, action und volatility an realen Kampfbeispielen nachkalibrieren

## Priorisierte erste Monster für die Migration

Empfohlen für die erste Welle:

- Blutjäger
- Söldner
- Schwarze Viper
- Zerra die Flüsterin
- Lord Vareth Nocthollow
- Ephazul
- Ser Vakor
- Der Namensnehmer
- Valkyre
- Raffon

## Warum diese Reihenfolge

Diese Monster decken die wichtigsten Rollenklassen ab:

- Standardkämpfer
- Elitekämpfer
- Assassine
- Controller
- Fernkampf
- Boss
- Endboss
- mehrphasiger Boss

## Technische Leitlinien

- Nur ASCII-Schlüssel im Katalog, menschliche Namen bleiben UTF-8
- JSON bleibt die Laufzeitquelle für Streamlit
- Markdown bleibt die redaktionelle Quelle
- Heuristiken nur dokumentiert und nachvollziehbar einsetzen
- Der Validator soll lieber warnen als stillschweigend falsche Daten zu erzeugen
- Finale numerische Modellwerte werden bevorzugt berechnet, nicht manuell gepflegt
- Overrides bleiben erlaubt, müssen aber im Katalog erkennbar sein

## Ergebnis nach Umsetzung

Am Ende gibt es einen einmal extern triggerbaren Build-Prozess, der:

1. Monsterdaten aus dem Bestiarium scannt
2. fehlende oder kaputte Einträge sichtbar meldet
3. einen stabilen JSON-Katalog erzeugt
4. diesen Katalog direkt in der Encounter-Berechnung verwendet

Damit wird der Monsterkatalog wartbar, reproduzierbar und von der Laufzeitlogik entkoppelt.
