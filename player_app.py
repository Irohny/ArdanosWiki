import streamlit as st
import math

st.set_page_config(page_title="DnD Charakterbogen", layout="wide")
st.title("Dungeons & Dragons Charakterbogen")

# === Hilfsfunktionen ===
def calculate_modifier(score):
    return math.floor((score - 10) / 2)

def get_proficiency_bonus(level):
    return 2 + ((level - 1) // 4)

# === Klasseninformationen ===
class_saves = {
    "Kämpfer": ["STR", "CON"],
    "Magier": ["INT", "WIS"],
    "Schurke": ["DEX", "INT"],
    "Kleriker": ["WIS", "CHA"],
    "Paladin": ["WIS", "CHA"],
    "Waldläufer": ["STR", "DEX"],
    "Barde": ["DEX", "CHA"],
    "Hexenmeister": ["CON", "CHA"],
    "Druide": ["INT", "WIS"],
    "Barbar": ["STR", "CON"],
    "Mönch": ["STR", "DEX"],
    "Zauberer": ["INT", "WIS"]
}

spellcaster_classes = {
    "Magier", "Kleriker", "Barde", "Hexenmeister", "Druide", "Paladin",
    "Waldläufer", "Zauberer"
}

# Zauberslots nach Klasse und Stufe (vereinfachte Darstellung)
def get_spell_slots(level):
    slots = {
        1: [2],
        2: [3],
        3: [4, 2],
        4: [4, 3],
        5: [4, 3, 2],
        6: [4, 3, 3],
        7: [4, 3, 3, 1],
        8: [4, 3, 3, 2],
        9: [4, 3, 3, 3, 1],
        10: [4, 3, 3, 3, 2],
        11: [4, 3, 3, 3, 2, 1],
        12: [4, 3, 3, 3, 2, 1],
        13: [4, 3, 3, 3, 2, 1, 1],
        14: [4, 3, 3, 3, 2, 1, 1],
        15: [4, 3, 3, 3, 2, 1, 1, 1],
        16: [4, 3, 3, 3, 2, 1, 1, 1],
        17: [4, 3, 3, 3, 2, 1, 1, 1, 1],
        18: [4, 3, 3, 3, 3, 1, 1, 1, 1],
        19: [4, 3, 3, 3, 3, 2, 1, 1, 1],
        20: [4, 3, 3, 3, 3, 2, 2, 1, 1],
    }
    return slots.get(level, [])

skills = {
    "Athletics": "STR", "Acrobatics": "DEX", "Sleight of Hand": "DEX", "Stealth": "DEX",
    "Arcana": "INT", "History": "INT", "Investigation": "INT", "Nature": "INT", "Religion": "INT",
    "Animal Handling": "WIS", "Insight": "WIS", "Medicine": "WIS", "Perception": "WIS", "Survival": "WIS",
    "Deception": "CHA", "Intimidation": "CHA", "Performance": "CHA", "Persuasion": "CHA"
}

# === Eingabe: Charakterdaten ===
header_con = st.container(border=True)
col1, col2, col3, col4 = header_con.columns(4)
name = col1.text_input("Name")
char_class = col2.selectbox("Klasse", list(class_saves.keys()))
race = col3.selectbox("Rasse", ["Mensch", "Elf", "Zwerg", "Halbling", "Halbelf", "Halbork", "Gnom", "Tiefling", "Dragonborn"])
level = col4.number_input("Stufe", min_value=1, max_value=20, value=1)
proficiency = get_proficiency_bonus(level)

cols = st.columns(5, border=True)
# === Attribute ===
cols[0].header("Attribute", divider=True)
short = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]
attributes, modifiers = {}, {}

for i, stat in enumerate(short):
    score = cols[0].number_input(f"{stat}", min_value=1, max_value=30, value=10)
    mod = calculate_modifier(score)
    cols[0].markdown(f"**Mod: {mod:+}**")
    attributes[stat] = score
    modifiers[stat] = mod

# === Saving Throws ===
cols[1].header("Saving Throws", divider=True)
save_proficiencies = class_saves.get(char_class, [])
saving_throws = {}
save_cols = cols[1].columns(2)
for i, stat in enumerate(short):
    prof = save_cols[0].checkbox(f"{stat}", value=stat in save_proficiencies)
    saving_throws[stat] = modifiers[stat] + (proficiency if prof else 0)
    save_cols[1].markdown(f"**→ {saving_throws[stat]:+}**")

# === Skills ===
cols[2].header("Skills", divider=True)
skill_profs = {}
skill_cols = cols[2].columns([2,1])
for skill, attr in skills.items():
    prof = skill_cols[0].checkbox(f"{skill} ({attr})")
    skill_profs[skill] = modifiers[attr] + (proficiency if prof else 0)
    skill_cols[1].write(f"→ {skill_profs[skill]:+}")

# === Passive Perception & Initiative ===
cols[3].header("Initiative & Wahrnehmung", divider=True)
initiative = modifiers["DEX"]
passive_perception = 10 + skill_profs.get("Perception", modifiers["WIS"])
cols[3].markdown(f"**Initiative:** {initiative:+}")
cols[3].markdown(f"**Passive Wahrnehmung:** {passive_perception}")

# === HP ===
cols[3].header("Trefferpunkte", divider=True)
hit_die = 10 if char_class in ["Kämpfer", "Paladin", "Waldläufer"] else \
          12 if char_class == "Barbar" else \
          6 if char_class in ["Magier", "Zauberer"] else 8
base_hp = hit_die + modifiers["CON"]
total_hp = base_hp + (hit_die + modifiers["CON"]) * (level - 1)
cols[3].markdown(f"**Trefferwürfel:** 1W{hit_die}")
cols[3].markdown(f"**Maximale HP:** {max(total_hp, level)}")

# === Zauber ===
if char_class in spellcaster_classes:
    st.header("✨ Zauberslots & Zauber")
    slots = get_spell_slots(level)
    st.markdown(f"**Zauberslots:**")
    for i, s in enumerate(slots):
        st.markdown(f"- Stufe {i+1}: {s} Slots")

    spells = st.data_editor(
        [{"Zaubername": "Magisches Geschoss", "Stufe": 1}],
        num_rows="dynamic",
        key="spell_editor"
    )

# === Backgrounds & Traits ===
st.header("📘 Background & Traits")
background = st.text_input("Hintergrund", value="Soldat")
traits = st.text_area("Traits & Features", value="Tapferkeit, Dunkelsicht, Zweihandwaffen")

# === Inventar ===
st.header("🎒 Inventar")
inventory = st.data_editor(
    [{"Gegenstand": "Ration", "Anzahl": 5}, {"Gegenstand": "Seil", "Anzahl": 1}],
    num_rows="dynamic",
    key="inventar_editor"
)

# === Übersicht ===
with st.expander("📜 Charakterübersicht"):
    st.subheader(f"{name} (Lvl {level} {race} {char_class})")
    st.markdown(f"**Proficiency Bonus:** {proficiency:+}  \n**HP:** {max(total_hp, level)}  \n**Initiative:** {initiative:+}  \n**Passive Wahrnehmung:** {passive_perception}")
    st.markdown(f"**Hintergrund:** {background}")
    st.markdown(f"**Traits:** {traits}")

    st.subheader("Attribute")
    for stat in short:
        st.write(f"{stat}: {attributes[stat]} → Mod: {modifiers[stat]:+}")

    st.subheader("Saving Throws")
    for stat in short:
        st.write(f"{stat}: {saving_throws[stat]:+}")

    st.subheader("Skills")
    for skill, val in skill_profs.items():
        st.write(f"{skill}: {val:+}")

    if char_class in spellcaster_classes:
        st.subheader("Zauber")
        for s in spells:
            st.write(f"{s['Zaubername']} (Stufe {s['Stufe']})")

    st.subheader("Inventar")
    for item in inventory:
        st.write(f"{item['Gegenstand']} (x{item['Anzahl']})")
