import streamlit as st
from dataclasses import dataclass
from enum import Enum

# =========================
# XP-Schwellen (DMG 2014)
# =========================
XP_THRESHOLDS = {
    1: (25, 50, 75, 100),
    2: (50, 100, 150, 200),
    3: (75, 150, 225, 400),
    4: (125, 250, 375, 500),
    5: (250, 500, 750, 1100),
    6: (300, 600, 900, 1400),
    7: (350, 750, 1100, 1700),
    8: (450, 900, 1400, 2100),
    9: (550, 1100, 1600, 2400),
    10: (600, 1200, 1900, 2800),
    11: (800, 1600, 2400, 3600),
    12: (1000, 2000, 3000, 4500),
    13: (1100, 2200, 3400, 5100),
    14: (1250, 2500, 3800, 5700),
    15: (1400, 2800, 4300, 6400),
    16: (1600, 3200, 4800, 7200),
    17: (2000, 3900, 5900, 8800),
    18: (2100, 4200, 6300, 9500),
    19: (2400, 4900, 7300, 10900),
    20: (2800, 5700, 8500, 12700),
}

# =========================
# CR → XP (DMG 2014)
# =========================
CR_XP = {
    0: 10,
    0.125: 25,
    0.25: 50,
    0.5: 100,
    1: 200,
    2: 450,
    3: 700,
    4: 1100,
    5: 1800,
    6: 2300,
    7: 2900,
    8: 3900,
    9: 5000,
    10: 5900,
    11: 7200,
    12: 8400,
    13: 10000,
    14: 11500,
    15: 13000,
}


# =========================
# Schwierigkeit
# =========================
class Schwierigkeit(Enum):
    LEICHT = "Leicht"
    MITTEL = "Mittel"
    SCHWER = "Schwer"
    TOEDLICH = "Tödlich"


SCHWIERIGKEITS_FAKTOR = {
    "LEICHT": 0.7,
    "MITTEL": 1.0,
    "SCHWER": 1.3,
    "TÖDLICH": 1.6,
}


# =========================
# Party
# =========================
@dataclass
class Party:
    spieler: int
    stufe: int


# =========================
# XP-Grenzen
# =========================
def xp_grenzen(party: Party):
    e, m, s, t = XP_THRESHOLDS[party.stufe]
    return {
        "LEICHT": e * party.spieler,
        "MITTEL": m * party.spieler,
        "SCHWER": s * party.spieler,
        "TÖDLICH": t * party.spieler,
    }


# =========================
# Hilfsfunktionen
# =========================
def skaliere_anzahl(basis, schwierigkeit):
    return max(
        1, int(round(basis * SCHWIERIGKEITS_FAKTOR[schwierigkeit.value.upper()]))
    )


def xp_fuer(cr, anzahl):
    return CR_XP.get(cr, 0) * anzahl


def bewertung(xp, grenzen):
    if xp < grenzen[Schwierigkeit.MITTEL.value.upper()]:
        return "🟢 untere Kante"
    elif xp < grenzen[Schwierigkeit.SCHWER.value.upper()]:
        return "🟡 mittlerer Bereich"
    else:
        return "🔴 obere Kante"


# =========================
# Encounter-Vorschläge
# =========================
def wellen_beispiel(party, schwierigkeit, wellen=3):
    basis = party.spieler
    minion_cr = max(0.5, party.stufe / 4)

    anzahl = skaliere_anzahl(basis + 1, schwierigkeit)
    xp_pro_welle = xp_fuer(minion_cr, anzahl)
    xp_gesamt = xp_pro_welle * wellen

    gegner_text = [
        f"{anzahl}× CR {minion_cr:.1f} pro Welle",
        f"{wellen} Wellen insgesamt",
    ]

    return ("🌊 Wellenkampf (dynamisch)", gegner_text, xp_pro_welle, xp_gesamt)


def beispiele(party, schwierigkeit):
    grenzen = xp_grenzen(party)
    ziel = ziel_xp(party, schwierigkeit, grenzen)

    daten = []

    # -------------------------
    # 1. Boss + starke Minions
    # -------------------------
    boss_cr = party.stufe + (1 if schwierigkeit != Schwierigkeit.LEICHT else 0)
    boss_xp = CR_XP.get(boss_cr, 0)

    minion_cr = max(0.5, party.stufe / 3)
    minions = max(2, int((ziel - boss_xp) / CR_XP.get(minion_cr, 1e-7)))

    xp_total = boss_xp + xp_fuer(minion_cr, minions)

    daten.append(
        (
            "Boss + Minions",
            [f"1× CR {boss_cr}", f"{minions}× CR {minion_cr:.1f}"],
            xp_total,
        )
    )

    # -------------------------
    # 2. Elite-Trupp
    # -------------------------
    elite_cr = party.stufe
    elite_xp = CR_XP[elite_cr]

    elites = max(2, int(ziel / elite_xp))
    xp_total = xp_fuer(elite_cr, elites)

    daten.append(("Elite-Trupp", [f"{elites}× CR {elite_cr}"], xp_total))

    # -------------------------
    # 3. Überzahl / Horde
    # -------------------------
    swarm_cr = max(0.5, party.stufe / 2)
    swarm_xp = CR_XP.get(swarm_cr, 1e-7)

    swarm = max(party.spieler * 2, int(ziel / swarm_xp))
    xp_total = xp_fuer(swarm_cr, swarm)

    daten.append(("Überzahl", [f"{swarm}× CR {swarm_cr:.1f}"], xp_total))

    # Wellen
    name, gegner, xp_welle, xp_gesamt = wellen_beispiel(party, schwierigkeit, wellen=3)

    daten.append((name, gegner, xp_gesamt))

    return daten


def ziel_xp(party, schwierigkeit, grenzen):
    """
    Liefert eine Ziel-XP, die bewusst im oberen Bereich
    der gewünschten Schwierigkeit liegt.
    """
    if schwierigkeit.value.upper() == Schwierigkeit.LEICHT.value.upper():
        return grenzen["LEICHT"] * 0.9
    if schwierigkeit.value.upper() == Schwierigkeit.MITTEL.value.upper():
        return grenzen["MITTEL"] * 1.1
    if schwierigkeit.value.upper() == Schwierigkeit.SCHWER.value.upper():
        return grenzen["SCHWER"] * 1.15
    if schwierigkeit.value.upper() == Schwierigkeit.TOEDLICH.value.upper():
        return grenzen["TÖDLICH"] * 1.25


def xp_fuer_monsterliste(monster_liste):
    """
    monster_liste = [
        {"cr": 2, "anzahl": 3},
        {"cr": 0.5, "anzahl": 6}
    ]
    """
    gesamt_xp = 0
    details = []

    for monster in monster_liste:
        cr = monster["cr"]
        anzahl = monster["anzahl"]
        xp = xp_fuer(cr, anzahl)
        gesamt_xp += xp
        details.append(f"{anzahl}× CR {cr} → {xp} XP")

    return gesamt_xp, details


def set_to_encounter_calculator_view():
    st.session_state["db_flag"] = True
    st.session_state["db"] = "Encounter Rechner"


def encounter_calculator_view():
    set_to_encounter_calculator_view()
    cols = st.columns(2, vertical_alignment="bottom")
    cols[0].number_input("Anzahl Spieler", 1, 8, 4, key="player_input")
    cols[0].number_input("Durchschnittliches Level", 1, 20, 5, key="level_input")

    cols[0].selectbox(
        "Gewünschte Schwierigkeit",
        list(Schwierigkeit),
        format_func=lambda s: s.value,
        key="cr_input",
    )

    party = Party(
        spieler=st.session_state["player_input"], stufe=st.session_state["level_input"]
    )
    grenzen = xp_grenzen(party)

    # =========================
    # XP-Leiste
    # =========================
    cols[1].subheader("XP-Schwierigkeitsleiste")
    # max_xp = grenzen[Schwierigkeit.TOEDLICH.value.upper()]

    for s in Schwierigkeit:
        # rel = grenzen[s.value.upper()] / max_xp
        label = f"{s.value}: {grenzen[s.value.upper()]} XP"
        if s == st.session_state["cr_input"]:
            cols[1].markdown(f"**👉 {label}**")
        else:
            cols[1].markdown(label)
        # cols[1].progress(rel)

    st.divider()

    # =========================
    # Beispiele mit XP
    # =========================
    st.subheader("Beispiel-Encounter mit XP-Einordnung")
    examples = beispiele(party, st.session_state["cr_input"])
    cols = st.columns(len(examples))
    i = 0
    for name, gegner, xp in examples:
        cols[i].markdown(f"### {name}")
        for g in gegner:
            cols[i].markdown(f"- {g}")
        cols[i].markdown(f"**Gesamt-XP:** `{xp}`")
        cols[i].markdown(f"**Einordnung:** {bewertung(xp, grenzen)}")
        i += 1
    st.divider()

    st.caption(
        "Definiere hier deine eigene Monstergruppe "
        "und prüfe, welchem Schwierigkeitsgrad sie entspricht."
    )

    monster_anzahl = st.number_input(
        "Wie viele unterschiedliche Monster-Typen?",
        min_value=1,
        max_value=6,
        value=2,
        step=1,
    )

    monster_liste = []

    cols = st.columns(2)
    for i in range(monster_anzahl):
        with cols[i % 2]:
            st.markdown(f"**Monster {i + 1}**")
            cr = st.selectbox(
                f"CR (Monster {i + 1})", sorted(CR_XP.keys()), key=f"cr_custom_{i}"
            )
            anzahl = st.number_input(
                f"Anzahl (Monster {i + 1})",
                min_value=1,
                max_value=20,
                value=1,
                step=1,
                key=f"anzahl_custom_{i}",
            )

            monster_liste.append({"cr": cr, "anzahl": anzahl})

    # =========================
    # Auswertung
    # =========================
    grenze = xp_grenzen(party)
    if monster_liste:
        xp_custom, details = xp_fuer_monsterliste(monster_liste)

        st.markdown("### 📊 Auswertung")

        for d in details:
            st.markdown(f"- {d}")

        st.markdown(f"**Gesamt-XP:** `{xp_custom}`")
        st.markdown(f"**Schwierigkeit:** {bewertung(xp_custom, grenzen)}")

        # Klare Einordnung
        for s in Schwierigkeit:
            print(grenze)
            if xp_custom <= grenze[s.value.upper()]:
                st.info(
                    f"➡ Der Encounter liegt **im Bereich {s.value}** "
                    f"(≤ {grenze} XP)"
                )
                break
