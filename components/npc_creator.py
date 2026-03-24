from pathlib import Path
import re

import streamlit as st


NPC_CREATOR_FEATURE_NAME = "NSC Ersteller"
NPC_RACES = [
    "Mensch",
    "Elf",
    "Zwerg",
    "Halbling",
    "Halbelf",
    "Halbork",
    "Gnom",
    "Tiefling",
    "Dragonborn",
    "Aasimar",
]
NPC_ROLE_PRESETS = {
    "Frei eingeben": "",
    "Haendler": "Erfahrener Haendler mit Gespuer fuer Preise, Kontakte und seltene Waren.",
    "Krieger": "Veteran vieler Kaempfe, diszipliniert, direkt und an klare Befehlsketten gewoehnt.",
    "Braumeister": "Kennt sich mit Braukunst, Gaerung, Zutatenqualitaet und den Gewohnheiten der einfachen Leute aus.",
    "Seefahrer": "Hat Jahre auf Flussschiffen oder Seewegen verbracht und kennt Haefen, Wetter und zwielichtige Crews.",
    "Adliger": "Stammt aus gutem Hause, ist mit Etikette vertraut und denkt in Einfluss, Verpflichtungen und Ansehen.",
    "Jaeger": "Lebt nahe an der Wildnis und versteht Spuren, Tiere, Wetter und abgelegene Pfade.",
    "Gelehrter": "Sammelt Wissen systematisch und argumentiert ueberlegt, neugierig und oft etwas distanziert.",
}
NPC_ORIGIN_OPTIONS = [
    "Frei eingeben",
    "Ardanos",
    "Drakmora",
    "Elmrath",
    "Mariven",
    "Schwarzklamm",
    "Vaylen",
    "Kaiserreich",
    "Grenzlande",
]
NPC_ROLE_OPTIONS = [
    "Frei eingeben",
    "Krieger",
    "Wache",
    "Söldner",
    "Jäger",
    "Händler",
    "Adliger",
    "Gelehrter",
    "Priester",
    "Magier",
    "Heiler",
    "Seefahrer",
    "Handwerker",
    "Spion",
    "Bandit",
]
NPC_ALIGNMENT_OPTIONS = [
    "Frei eingeben",
    "Rechtschaffen gut",
    "Neutral gut",
    "Chaotisch gut",
    "Rechtschaffen neutral",
    "Neutral",
    "Chaotisch neutral",
    "Rechtschaffen boese",
    "Neutral boese",
    "Chaotisch boese",
]
NPC_UNKNOWN_VALUE = "unbekannt"
NPC_FOUNDATION_OPTIONS = [
    "#Homebrew",
    "#Book",
    "#Online",
    "#Homebrew #Book",
    "#Homebrew #Online",
    "#Book #Online",
    "#Homebrew #Book #Online",
]


def set_to_npc_creator_view() -> None:
    st.session_state["db_flag"] = True
    st.session_state["db"] = NPC_CREATOR_FEATURE_NAME


def npc_creator_is_admin() -> bool:
    user = st.session_state.get("user")
    return bool(user and getattr(user.role, "value", None) == "GameMaster")


def _resolved_select_value(select_key: str, custom_key: str) -> str:
    selected_value = st.session_state.get(select_key, "Frei eingeben")
    if selected_value == "Frei eingeben":
        return st.session_state.get(custom_key, "").strip()
    return selected_value


def _npc_export_directory() -> Path:
    return Path(__file__).resolve().parents[1] / "World" / "Spielleiter"


def _sanitize_filename(name: str) -> str:
    normalized = name.strip() or "Unbenannter NSC"
    normalized = re.sub(r"[^A-Za-z0-9 _.-]", "", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized or "Unbenannter NSC"


def _comma_separated_entries(raw_value: str) -> list[str]:
    return [entry.strip() for entry in raw_value.split(",") if entry.strip()]


def _format_link_entries(raw_value: str) -> str:
    entries = []
    for entry in _comma_separated_entries(raw_value):
        if entry.startswith("[[") and entry.endswith("]]"):
            entries.append(entry)
        else:
            entries.append(f"[[{entry}]]")
    return ", ".join(entries)


def _section_text(value: str, default: str = "-") -> str:
    cleaned = value.strip()
    return cleaned if cleaned else default


def _template_values() -> dict[str, str]:
    foundation = st.session_state.get(
        "npc_creator_foundation", NPC_FOUNDATION_OPTIONS[0]
    )
    manual_tags = st.session_state.get("npc_creator_tags", "").strip()
    combined_tags = " ".join(part for part in [foundation, manual_tags] if part).strip()
    return {
        "alias": st.session_state.get("npc_creator_alias", "").strip(),
        "title_office": st.session_state.get("npc_creator_title_office", "").strip(),
        "dynasty": st.session_state.get("npc_creator_dynasty", "").strip(),
        "regency": st.session_state.get("npc_creator_regency", "").strip(),
        "birth_year": st.session_state.get("npc_creator_birth_year", "").strip(),
        "death_year": st.session_state.get("npc_creator_death_year", "").strip(),
        "linked_places": st.session_state.get("npc_creator_linked_places", "").strip(),
        "linked_npcs": st.session_state.get("npc_creator_linked_npcs", "").strip(),
        "known_for": st.session_state.get("npc_creator_known_for", "").strip(),
        "first_mention": st.session_state.get("npc_creator_first_mention", "").strip(),
        "tags": combined_tags,
        "role_relations": st.session_state.get(
            "npc_creator_role_relations", ""
        ).strip(),
        "plot_hooks": st.session_state.get("npc_creator_plot_hooks", "").strip(),
        "secret_info": st.session_state.get("npc_creator_secret_info", "").strip(),
        "monster_profile": st.session_state.get(
            "npc_creator_monster_profile", ""
        ).strip(),
    }


def _description_section(background: str, profile_values: dict[str, str]) -> str:
    lines = []
    if background and background != "-":
        lines.append(background)
    if profile_values["alignment"]:
        lines.append(f"- Gesinnung: {profile_values['alignment']}")
    if profile_values["languages"]:
        lines.append(f"- Sprachen: {profile_values['languages']}")
    if profile_values["traits"]:
        lines.append(f"- Merkmale: {profile_values['traits']}")
    if profile_values["quotes"]:
        lines.append(f"- Typischer Sprachstil oder Zitat: {profile_values['quotes']}")
    return "\n".join(lines) if lines else "-"


def _role_section(
    profile_values: dict[str, str], template_values: dict[str, str]
) -> str:
    lines = []
    if template_values["role_relations"]:
        lines.append(template_values["role_relations"])
    if profile_values["role"] and profile_values["role"] != "Frei eingeben":
        lines.append(f"- Funktion: {profile_values['role']}")
    if profile_values["affiliation"]:
        lines.append(f"- Zugehoerigkeit: {profile_values['affiliation']}")
    return "\n".join(lines) if lines else "-"


def _render_export_markdown() -> str:
    race = st.session_state.get("npc_creator_race", NPC_RACES[0])
    background = st.session_state.get("npc_creator_background", "").strip() or "-"
    profile_values = _profile_values()
    template_values = _template_values()

    title_office = template_values["title_office"] or (
        profile_values["role"] if profile_values["role"] != "Frei eingeben" else ""
    )
    known_for = template_values["known_for"] or profile_values["traits"] or title_office
    linked_places = _format_link_entries(template_values["linked_places"])
    linked_npcs = _format_link_entries(template_values["linked_npcs"])
    first_mention = template_values["first_mention"] or NPC_UNKNOWN_VALUE
    description_section = _description_section(background, profile_values)
    role_section = _role_section(profile_values, template_values)
    monster_profile = _format_link_entries(template_values["monster_profile"])

    lines = [
        "<!--",
        "Ein-Datei-Profil fuer NPCs.",
        "Oeffentliche und nicht oeffentliche Informationen duerfen in derselben Datei stehen.",
        "Die Timeline-Crawler lesen spaeter gezielt die markierten Metadatenfelder aus dieser Struktur.",
        "-->",
        "",
        f"- **Rufname / Beiname:** {template_values['alias']}",
        f"- **Titel / Amt:** {title_office}",
        f"- **Haus / Dynastie:** {template_values['dynasty'] or profile_values['affiliation']}",
        f"- **Regentschaft:** {template_values['regency']}",
        f"- **Spezies / Volk:** {race}",
        f"- **Herkunft:** {profile_values['origin']}",
        f"- **Geburtsjahr:** {template_values['birth_year']}",
        f"- **Sterbejahr:** {template_values['death_year']}",
        f"- **Alter:** {profile_values['age']}",
        "",
        f"- **Verknuepfte Orte:** {linked_places}",
        f"- **Verknuepfte NPCs:** {linked_npcs}",
        f"- **Bekannt fuer:** {known_for}",
        f"- **Erste Erwaehnung:** {first_mention}",
        f"- **Tags:** {template_values['tags']}",
        "",
        "## Beschreibung und Auftreten",
        "",
        description_section,
        "",
        "## Rolle und Beziehungen",
        "",
        role_section,
        "",
        "<!--",
        "Nicht oeffentliche Angaben zum NPC.",
        "Diese Abschnitte koennen vom Crawler ignoriert werden, solange er nur die expliziten Felder und oeffentlichen Bereiche ausliest.",
        "-->",
        "",
        "## Ziele",
        "",
        _section_text(profile_values["motivation"]),
        "",
        "## Plot-Hooks",
        "",
        _section_text(template_values["plot_hooks"]),
        "",
        "## Geheime Informationen",
        "",
        _section_text(template_values["secret_info"]),
        "",
        "## Kampfwerte",
        "",
        f"- **Bestiarium-Profil:** {monster_profile or '-'}",
        "- **Hinweis:** Das verlinkte Profil sollte auf dem Monster-Template im Bestiarium basieren.",
    ]
    return "\n".join(lines) + "\n"


def _export_npc_markdown() -> tuple[bool, str]:
    export_dir = _npc_export_directory()
    export_dir.mkdir(parents=True, exist_ok=True)
    file_name = f"{_sanitize_filename(st.session_state.get('npc_creator_name', ''))}.md"
    export_path = export_dir / file_name
    if export_path.exists():
        return False, f"Datei existiert bereits: {export_path.name}"
    export_path.write_text(_render_export_markdown(), encoding="utf-8")
    return True, str(export_path)


def _profile_values() -> dict[str, str]:
    return {
        "foundation": st.session_state.get(
            "npc_creator_foundation", NPC_FOUNDATION_OPTIONS[0]
        ),
        "origin": _resolved_select_value(
            "npc_creator_origin", "npc_creator_origin_custom"
        ),
        "role": st.session_state.get("npc_creator_role_preset", "Frei eingeben"),
        "alias": st.session_state.get("npc_creator_alias", "").strip(),
        "age": st.session_state.get("npc_creator_age", "").strip(),
        "alignment": _resolved_select_value(
            "npc_creator_alignment", "npc_creator_alignment_custom"
        ),
        "languages": st.session_state.get("npc_creator_languages", "").strip(),
        "traits": st.session_state.get("npc_creator_traits", "").strip(),
        "affiliation": st.session_state.get("npc_creator_affiliation", "").strip(),
        "motivation": st.session_state.get("npc_creator_motivation", "").strip(),
        "quotes": st.session_state.get("npc_creator_quotes", "").strip(),
    }


def _ensure_npc_creator_state() -> None:
    if "npc_creator_name" not in st.session_state:
        st.session_state["npc_creator_name"] = ""
    if "npc_creator_race" not in st.session_state:
        st.session_state["npc_creator_race"] = NPC_RACES[0]
    if "npc_creator_role_preset" not in st.session_state:
        st.session_state["npc_creator_role_preset"] = "Frei eingeben"
    if "npc_creator_background" not in st.session_state:
        st.session_state["npc_creator_background"] = ""
    if "npc_creator_enable_profile_module" not in st.session_state:
        st.session_state["npc_creator_enable_profile_module"] = False
    if "npc_creator_foundation" not in st.session_state:
        st.session_state["npc_creator_foundation"] = NPC_FOUNDATION_OPTIONS[0]
    if "npc_creator_origin" not in st.session_state:
        st.session_state["npc_creator_origin"] = NPC_ORIGIN_OPTIONS[0]
    if "npc_creator_origin_custom" not in st.session_state:
        st.session_state["npc_creator_origin_custom"] = ""
    if "npc_creator_alias" not in st.session_state:
        st.session_state["npc_creator_alias"] = ""
    if "npc_creator_title_office" not in st.session_state:
        st.session_state["npc_creator_title_office"] = ""
    if "npc_creator_dynasty" not in st.session_state:
        st.session_state["npc_creator_dynasty"] = ""
    if "npc_creator_regency" not in st.session_state:
        st.session_state["npc_creator_regency"] = ""
    if "npc_creator_birth_year" not in st.session_state:
        st.session_state["npc_creator_birth_year"] = ""
    if "npc_creator_death_year" not in st.session_state:
        st.session_state["npc_creator_death_year"] = ""
    if "npc_creator_age" not in st.session_state:
        st.session_state["npc_creator_age"] = ""
    if "npc_creator_linked_places" not in st.session_state:
        st.session_state["npc_creator_linked_places"] = ""
    if "npc_creator_linked_npcs" not in st.session_state:
        st.session_state["npc_creator_linked_npcs"] = ""
    if "npc_creator_known_for" not in st.session_state:
        st.session_state["npc_creator_known_for"] = ""
    if "npc_creator_first_mention" not in st.session_state:
        st.session_state["npc_creator_first_mention"] = NPC_UNKNOWN_VALUE
    if "npc_creator_tags" not in st.session_state:
        st.session_state["npc_creator_tags"] = ""
    if "npc_creator_alignment" not in st.session_state:
        st.session_state["npc_creator_alignment"] = NPC_ALIGNMENT_OPTIONS[0]
    if "npc_creator_alignment_custom" not in st.session_state:
        st.session_state["npc_creator_alignment_custom"] = ""
    if "npc_creator_languages" not in st.session_state:
        st.session_state["npc_creator_languages"] = ""
    if "npc_creator_traits" not in st.session_state:
        st.session_state["npc_creator_traits"] = ""
    if "npc_creator_affiliation" not in st.session_state:
        st.session_state["npc_creator_affiliation"] = ""
    if "npc_creator_role_relations" not in st.session_state:
        st.session_state["npc_creator_role_relations"] = ""
    if "npc_creator_motivation" not in st.session_state:
        st.session_state["npc_creator_motivation"] = ""
    if "npc_creator_plot_hooks" not in st.session_state:
        st.session_state["npc_creator_plot_hooks"] = ""
    if "npc_creator_secret_info" not in st.session_state:
        st.session_state["npc_creator_secret_info"] = ""
    if "npc_creator_monster_profile" not in st.session_state:
        st.session_state["npc_creator_monster_profile"] = ""
    if "npc_creator_quotes" not in st.session_state:
        st.session_state["npc_creator_quotes"] = ""


def _apply_background_preset() -> None:
    preset_name = st.session_state.get("npc_creator_role_preset", "Frei eingeben")
    st.session_state["npc_creator_background"] = NPC_ROLE_PRESETS.get(preset_name, "")
    set_to_npc_creator_view()


def npc_creator_view() -> None:
    set_to_npc_creator_view()
    if not npc_creator_is_admin():
        st.warning("Der NPC-Ersteller ist nur fuer Spielleiter verfuegbar.")
        return

    _ensure_npc_creator_state()

    st.subheader("NSC Ersteller")
    st.caption(
        "Profilwerkzeug fuer NSCs mit oeffentlichen und nicht oeffentlichen Bereichen."
    )

    form_col, preview_col = st.columns([3, 4], vertical_alignment="top")

    with form_col:
        with st.container(border=True):
            st.text_input(
                "Name",
                key="npc_creator_name",
                placeholder="Zum Beispiel: Arved der Graue",
            )
            st.selectbox("Rasse", NPC_RACES, key="npc_creator_race")
            st.selectbox(
                "Funktion oder Rolle",
                list(NPC_ROLE_PRESETS.keys()),
                key="npc_creator_role_preset",
                on_change=_apply_background_preset,
            )
            st.text_area(
                "Beschreibung und Auftreten",
                key="npc_creator_background",
                height=140,
                placeholder="Ein bis drei Saetze zu Auftreten, Wirkung und oeffentlich sichtbarer Relevanz",
            )
            with st.expander("Optionale Profildaten"):
                st.checkbox(
                    "Profildaten verwenden",
                    key="npc_creator_enable_profile_module",
                    help="Blendet Herkunft, Gesinnung, Sprachen und weitere Profilfelder in der Vorschau ein.",
                )
                if st.session_state.get("npc_creator_enable_profile_module", False):
                    st.markdown("**Template-Felder**")
                    st.selectbox(
                        "Grundlage",
                        NPC_FOUNDATION_OPTIONS,
                        key="npc_creator_foundation",
                    )
                    st.selectbox(
                        "Herkunft",
                        NPC_ORIGIN_OPTIONS,
                        key="npc_creator_origin",
                    )
                    if st.session_state.get("npc_creator_origin") == "Frei eingeben":
                        st.text_input("Herkunft frei", key="npc_creator_origin_custom")
                    text_cols = st.columns(2, gap="medium")
                    text_cols[0].text_input(
                        "Rufname / Beiname", key="npc_creator_alias"
                    )
                    text_cols[1].text_input(
                        "Titel / Amt", key="npc_creator_title_office"
                    )
                    text_cols = st.columns(2, gap="medium")
                    text_cols[0].text_input(
                        "Haus / Dynastie", key="npc_creator_dynasty"
                    )
                    text_cols[1].text_input("Regentschaft", key="npc_creator_regency")
                    text_cols = st.columns(3, gap="medium")
                    text_cols[0].text_input("Geburtsjahr", key="npc_creator_birth_year")
                    text_cols[1].text_input("Sterbejahr", key="npc_creator_death_year")
                    text_cols[2].text_input("Alter", key="npc_creator_age")
                    st.selectbox(
                        "Gesinnung",
                        NPC_ALIGNMENT_OPTIONS,
                        key="npc_creator_alignment",
                    )
                    if st.session_state.get("npc_creator_alignment") == "Frei eingeben":
                        st.text_input(
                            "Gesinnung frei", key="npc_creator_alignment_custom"
                        )
                    st.text_input(
                        "Sprachen",
                        key="npc_creator_languages",
                        placeholder="Zum Beispiel: Gemeinsprache, Elfisch, Zwergisch",
                    )
                    st.text_input(
                        "Merkmale",
                        key="npc_creator_traits",
                        placeholder="Zum Beispiel: Narben, ruhiger Blick, goldene Kette",
                    )
                    st.text_input(
                        "Haus / Zugehoerigkeit / Fraktion",
                        key="npc_creator_affiliation",
                        placeholder="Zum Beispiel: Morgenwacht, Haus Valmor, freie Gilde",
                    )
                    st.text_input(
                        "Verknuepfte Orte",
                        key="npc_creator_linked_places",
                        placeholder="Zum Beispiel: Ardanos, Elmrath, Luminara",
                    )
                    st.text_input(
                        "Verknuepfte NPCs",
                        key="npc_creator_linked_npcs",
                        placeholder="Zum Beispiel: Aldric von Elmrath, Selene Drachenruf",
                    )
                    st.text_input(
                        "Bekannt fuer",
                        key="npc_creator_known_for",
                        placeholder="Zum Beispiel: Diplomatie, Kriegskunst, Handel",
                    )
                    text_cols = st.columns(2, gap="medium")
                    text_cols[0].text_input(
                        "Erste Erwaehnung", key="npc_creator_first_mention"
                    )
                    text_cols[1].text_input(
                        "Weitere Tags",
                        key="npc_creator_tags",
                        placeholder="#region #rolle #schlagwort",
                    )
                    st.text_area(
                        "Rolle und Beziehungen",
                        key="npc_creator_role_relations",
                        height=120,
                        placeholder="Welche Funktion erfuellt die Figur und zu wem oder was steht sie in Beziehung?",
                    )
                    st.text_area(
                        "Ziele",
                        key="npc_creator_motivation",
                        height=100,
                        placeholder="Was treibt den NPC aktuell an?",
                    )
                    st.text_area(
                        "Plot-Hooks",
                        key="npc_creator_plot_hooks",
                        height=100,
                        placeholder="Einstiege, Komplikationen oder Abenteueraufhaenger rund um diese Figur",
                    )
                    st.text_area(
                        "Geheime Informationen",
                        key="npc_creator_secret_info",
                        height=100,
                        placeholder="Nur fuer Spielleiter bestimmte Informationen",
                    )
                    st.text_input(
                        "Bestiarium-Profil fuer Kampfwerte",
                        key="npc_creator_monster_profile",
                        placeholder="Zum Beispiel: Söldner oder Lady Seress",
                        help="Verweist auf ein separates Monsterprofil im Bestiarium, das auf dem Monster-Template basiert.",
                    )
                    st.text_area(
                        "Typischer Sprachstil oder Zitat",
                        key="npc_creator_quotes",
                        height=80,
                        placeholder="Typische Formulierungen, Redeweise oder ein markantes Zitat",
                    )
            if st.button(
                "NSC nach World/Spielleiter exportieren", use_container_width=True
            ):
                export_success, export_message = _export_npc_markdown()
                if export_success:
                    st.success(f"NSC exportiert nach {export_message}")
                else:
                    st.warning(export_message)

    with preview_col:
        with st.container(border=True):
            name = st.session_state.get("npc_creator_name", "") or "Unbenannter NSC"
            race = st.session_state.get("npc_creator_race", NPC_RACES[0])
            background = st.session_state.get("npc_creator_background", "").strip()
            profile_values = _profile_values()
            template_values = _template_values()
            st.markdown(f"## {name}")
            st.caption(f"Spezies / Volk: {race}")
            if template_values["title_office"]:
                st.caption(f"Titel / Amt: {template_values['title_office']}")
            elif profile_values["role"] and profile_values["role"] != "Frei eingeben":
                st.caption(f"Titel / Amt: {profile_values['role']}")
            if st.session_state.get("npc_creator_enable_profile_module", False):
                with st.container(border=True):
                    st.markdown("**Oeffentliches Profil**")
                    st.markdown(
                        f"Rufname / Beiname: **{template_values['alias'] or '-'}**"
                    )
                    st.markdown(
                        f"Titel / Amt: **{template_values['title_office'] or (profile_values['role'] if profile_values['role'] != 'Frei eingeben' else '-')}**"
                    )
                    st.markdown(
                        f"Haus / Dynastie: **{template_values['dynasty'] or profile_values['affiliation'] or '-'}**"
                    )
                    st.markdown(
                        f"Grundlage/Tags: **{template_values['tags'] or profile_values['foundation']}**"
                    )
                    if template_values["regency"]:
                        st.markdown(f"Regentschaft: **{template_values['regency']}**")
                    if profile_values["origin"]:
                        st.markdown(f"Herkunft: **{profile_values['origin']}**")
                    if template_values["birth_year"]:
                        st.markdown(f"Geburtsjahr: **{template_values['birth_year']}**")
                    if template_values["death_year"]:
                        st.markdown(f"Sterbejahr: **{template_values['death_year']}**")
                    if profile_values["age"]:
                        st.markdown(f"Alter: **{profile_values['age']}**")
                    if template_values["linked_places"]:
                        st.markdown(
                            f"Verknuepfte Orte: {template_values['linked_places']}"
                        )
                    if template_values["linked_npcs"]:
                        st.markdown(
                            f"Verknuepfte NPCs: {template_values['linked_npcs']}"
                        )
                    if template_values["known_for"]:
                        st.markdown(f"Bekannt fuer: {template_values['known_for']}")
                    if template_values["first_mention"]:
                        st.markdown(
                            f"Erste Erwaehnung: **{template_values['first_mention']}**"
                        )
                with st.container(border=True):
                    st.markdown("**Beschreibung und Auftreten**")
                    st.markdown(_description_section(background, profile_values))
                with st.container(border=True):
                    st.markdown("**Rolle und Beziehungen**")
                    st.markdown(_role_section(profile_values, template_values))
                with st.container(border=True):
                    st.markdown("**Nicht oeffentlich**")
                    st.markdown(f"Ziele: {_section_text(profile_values['motivation'])}")
                    st.markdown(
                        f"Plot-Hooks: {_section_text(template_values['plot_hooks'])}"
                    )
                    st.markdown(
                        f"Geheime Informationen: {_section_text(template_values['secret_info'])}"
                    )
                    st.markdown(
                        f"Kampfwerte/Bestiarium: {template_values['monster_profile'] or '-'}"
                    )
                    if profile_values["quotes"]:
                        st.markdown(f"Sprachstil/Zitat: {profile_values['quotes']}")
