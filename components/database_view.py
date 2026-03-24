import re
from enum import Enum
from html import escape

import pandas as pd
import streamlit as st

from components.show_file import make_internal_links_clickable


def _normalize_lookup_text(value: str) -> str:
    normalized = value.casefold().strip()
    normalized = (
        normalized.replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("ß", "ss")
    )
    return re.sub(r"[^a-z0-9]", "", normalized)


class Rarity(Enum):
    HAEUFIG = ("Häufig", 0, "#e5e7eb", "#374151", ("haeufig", "häufig"))
    GEWOEHNLICH = ("Gewöhnlich", 1, "#e5e7eb", "#374151", ("gewoehnlich", "gewöhnlich"))
    UNGEWOEHNLICH = (
        "Ungewöhnlich",
        2,
        "#d1fae5",
        "#065f46",
        ("ungewoehnlich", "ungewöhnlich"),
    )
    SELTEN = ("Selten", 3, "#dbeafe", "#1d4ed8", ("selten",))
    SEHR_SELTEN = (
        "Sehr selten",
        4,
        "#ede9fe",
        "#6d28d9",
        ("sehrselten", "sehr selten"),
    )
    LEGENDAER = ("Legendär", 5, "#fde68a", "#92400e", ("legendaer", "legendär"))
    ARTEFAKT = ("Artefakt", 6, "#fecaca", "#991b1b", ("artefakt",))

    def __init__(
        self,
        display_label: str,
        order: int,
        background: str,
        foreground: str,
        aliases: tuple[str, ...],
    ):
        self.display_label = display_label
        self.order = order
        self.background = background
        self.foreground = foreground
        self.aliases = aliases

    @property
    def colors(self) -> tuple[str, str]:
        return (self.background, self.foreground)

    @classmethod
    def from_text(cls, value: str) -> "Rarity | None":
        normalized = _normalize_lookup_text(value)
        for rarity in cls:
            candidates = {_normalize_lookup_text(rarity.display_label)}
            candidates.update(_normalize_lookup_text(alias) for alias in rarity.aliases)
            if normalized in candidates:
                return rarity
            if any(candidate and candidate in normalized for candidate in candidates):
                return rarity
        return None


LEVEL_COLORS = {
    0: ("#e0f2fe", "#075985"),
    1: ("#dcfce7", "#166534"),
    2: ("#d1fae5", "#065f46"),
    3: ("#fde68a", "#92400e"),
    4: ("#fed7aa", "#9a3412"),
    5: ("#fecaca", "#991b1b"),
    6: ("#fbcfe8", "#9d174d"),
    7: ("#ddd6fe", "#6d28d9"),
    8: ("#c7d2fe", "#3730a3"),
    9: ("#dbeafe", "#1d4ed8"),
}

TAG_COLORS = [
    ("#fef3c7", "#92400e"),
    ("#dbeafe", "#1d4ed8"),
    ("#dcfce7", "#166534"),
    ("#fce7f3", "#9d174d"),
    ("#ede9fe", "#6d28d9"),
    ("#cffafe", "#155e75"),
]

SCHOOL_COLORS = {
    "beschwörung": ("#fde68a", "#92400e"),
    "bann": ("#dbeafe", "#1d4ed8"),
    "erkenntnis": ("#cffafe", "#155e75"),
    "hervorrufung": ("#fecaca", "#991b1b"),
    "illusion": ("#fbcfe8", "#9d174d"),
    "nekromantie": ("#ddd6fe", "#6d28d9"),
    "verzauberung": ("#dcfce7", "#166534"),
    "transmutation": ("#fed7aa", "#9a3412"),
}


def show_database(db: str):
    if "Bestiarium" in db:
        bestiarium_view()
    elif "Zauberarchiv" in db:
        zauberarchiev_view()
    elif "Tranksammlung" in db:
        trank_view()
    elif "Zutatenarchiv" in db:
        zutaten_view()


def set_to_databse_view(db: str):
    st.session_state["db_flag"] = True
    st.session_state["db"] = db


def _state_key(db: str, suffix: str) -> str:
    db_name = db.split("/")[-1]
    db_name = re.sub(r"\W+", "_", db_name.lower()).strip("_")
    return f"db_view_{db_name}_{suffix}"


def _clean_text(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def _extract_tokens(value) -> list[str]:
    text = _clean_text(value)
    if not text:
        return []

    hash_tokens = [token.strip() for token in re.findall(r"#([^\s,#\]]+)", text)]
    wiki_tokens = [token.strip() for token in re.findall(r"\[\[([^\]]+)\]\]", text)]
    plain_tokens = []
    for segment in re.split(r"[,;\n]", text):
        if not segment or not segment.strip():
            continue
        if "#" in segment or "[[" in segment:
            continue
        plain_tokens.append(segment.strip())

    tokens = []
    seen = set()
    for token in hash_tokens + wiki_tokens + plain_tokens:
        normalized = token.strip()
        lowered = normalized.casefold()
        if normalized and lowered not in seen:
            tokens.append(normalized)
            seen.add(lowered)
    return tokens


def _format_plain_value(value) -> str:
    text = _clean_text(value)
    if not text:
        return ""
    if "#" in text or "[[" in text:
        return ", ".join(_extract_tokens(text))
    return text


def _format_rich_value(value) -> str:
    text = _clean_text(value)
    if not text:
        return ""
    if "[[" in text:
        return make_internal_links_clickable(text)
    if "#" in text:
        return ", ".join(_extract_tokens(text))
    return text


def _ensure_database_state(
    db: str, filter_fields: list[str], default_sort: str
) -> None:
    search_key = _state_key(db, "search")
    sort_key = _state_key(db, "sort")
    if search_key not in st.session_state:
        st.session_state[search_key] = ""
    if sort_key not in st.session_state:
        st.session_state[sort_key] = default_sort
    for field in filter_fields:
        filter_key = _state_key(db, f"filter_{field}")
        if filter_key not in st.session_state:
            st.session_state[filter_key] = []


def _reset_database_filters(
    db: str, filter_fields: list[str], default_sort: str
) -> None:
    st.session_state[_state_key(db, "search")] = ""
    st.session_state[_state_key(db, "sort")] = default_sort
    for field in filter_fields:
        st.session_state[_state_key(db, f"filter_{field}")] = []
    set_to_databse_view(db)


def _filter_options(df: pd.DataFrame, field: str) -> list[str]:
    options = []
    seen = set()
    for value in df[field].dropna().tolist():
        for token in _extract_tokens(value):
            lowered = token.casefold()
            if lowered not in seen:
                options.append(token)
                seen.add(lowered)
    return sorted(options, key=str.casefold)


def _apply_database_filters(
    df: pd.DataFrame,
    db: str,
    search_fields: list[str],
    filter_fields: list[str],
) -> pd.DataFrame:
    filtered = df.copy()
    search_query = st.session_state[_state_key(db, "search")].strip().casefold()

    if search_query:

        def matches_search(row: pd.Series) -> bool:
            haystack = " ".join(
                _clean_text(row.get(field, "")) for field in search_fields
            )
            return search_query in haystack.casefold()

        filtered = filtered[filtered.apply(matches_search, axis=1)]

    for field in filter_fields:
        selected = st.session_state[_state_key(db, f"filter_{field}")]
        if not selected:
            continue
        normalized_selected = {value.casefold() for value in selected}
        filtered = filtered[
            filtered[field].apply(
                lambda value: bool(
                    normalized_selected
                    & {token.casefold() for token in _extract_tokens(value)}
                )
            )
        ]

    return filtered


def _rarity_rank(value) -> tuple[int, str]:
    text = _format_plain_value(value).casefold()
    if not text:
        return (999, "")
    rarity = Rarity.from_text(text)
    if rarity is None:
        return (998, text)
    return (rarity.order, text)


def _first_number(value) -> int:
    text = _clean_text(value)
    match = re.search(r"\d+", text)
    if match:
        return int(match.group(0))
    return 999


def _infer_potion_rarity_from_value(value) -> str:
    amount = _first_number(value)
    if amount == 999:
        return ""
    if amount <= 25:
        return Rarity.HAEUFIG.display_label
    if amount <= 75:
        return Rarity.GEWOEHNLICH.display_label
    if amount <= 175:
        return Rarity.UNGEWOEHNLICH.display_label
    if amount <= 500:
        return Rarity.SELTEN.display_label
    if amount <= 1000:
        return Rarity.SEHR_SELTEN.display_label
    return Rarity.LEGENDAER.display_label


def _prepare_potion_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    prepared = df.copy()
    prepared["Seltenheit"] = prepared.apply(
        lambda row: _format_plain_value(row.get("Seltenheit", ""))
        or _infer_potion_rarity_from_value(row.get("Wert", "")),
        axis=1,
    )
    return prepared


def _sort_records(records: list[dict], sort_mode: str) -> list[dict]:
    if sort_mode == "Name (A-Z)":
        return sorted(
            records, key=lambda row: _format_plain_value(row.get("Name", "")).casefold()
        )
    if sort_mode == "Name (Z-A)":
        return sorted(
            records,
            key=lambda row: _format_plain_value(row.get("Name", "")).casefold(),
            reverse=True,
        )
    if sort_mode == "Grad -> Name":
        return sorted(
            records,
            key=lambda row: (
                _first_number(row.get("Grad", "")),
                _format_plain_value(row.get("Name", "")).casefold(),
            ),
        )
    if sort_mode == "Schule -> Name":
        return sorted(
            records,
            key=lambda row: (
                _format_plain_value(row.get("Schule", "")).casefold(),
                _format_plain_value(row.get("Name", "")).casefold(),
            ),
        )
    if sort_mode == "Seltenheit -> Name":
        return sorted(
            records,
            key=lambda row: (
                _rarity_rank(row.get("Seltenheit", "")),
                _format_plain_value(row.get("Name", "")).casefold(),
            ),
        )
    if sort_mode == "Fundort -> Name":
        return sorted(
            records,
            key=lambda row: (
                _format_plain_value(row.get("Fundort", "")).casefold(),
                _format_plain_value(row.get("Name", "")).casefold(),
            ),
        )
    if sort_mode == "Wert -> Name":
        return sorted(
            records,
            key=lambda row: (
                _first_number(row.get("Wert", "")),
                _format_plain_value(row.get("Name", "")).casefold(),
            ),
        )
    return records


def _badge_html(label: str, background: str, foreground: str) -> str:
    return (
        '<span style="display:inline-block;margin:0 0.35rem 0.35rem 0;padding:0.18rem 0.55rem;'
        f"border-radius:999px;background:{background};color:{foreground};font-size:0.82rem;"
        f'font-weight:600;">{escape(label)}</span>'
    )


def _region_html(label: str) -> str:
    return (
        '<span style="display:inline-block;margin:0 0.35rem 0.35rem 0;padding:0.24rem 0.6rem;'
        "border-radius:0.5rem;background:#f3f4f6;color:#374151;font-size:0.84rem;"
        f'font-weight:500;">{escape(label)}</span>'
    )


def _tag_color(tag: str) -> tuple[str, str]:
    color_index = sum(ord(char) for char in tag.casefold()) % len(TAG_COLORS)
    return TAG_COLORS[color_index]


def _rarity_colors(value: str) -> tuple[str, str]:
    rarity = Rarity.from_text(value)
    if rarity is not None:
        return rarity.colors
    return ("#e5e7eb", "#374151")


def _level_colors(value: str) -> tuple[str, str]:
    level = _first_number(value)
    return LEVEL_COLORS.get(level, ("#e5e7eb", "#374151"))


def _mapped_colors(value: str, mapping: dict[str, tuple[str, str]]) -> tuple[str, str]:
    normalized = value.casefold()
    for candidate, colors in mapping.items():
        if candidate in normalized:
            return colors
    return ("#e5e7eb", "#374151")


def _render_badges(badges: list[str]) -> None:
    if badges:
        st.markdown("".join(badges), unsafe_allow_html=True)


def _render_rarity_badge(value: str) -> None:
    if not value:
        return
    rarity = Rarity.from_text(value)
    background, foreground = _rarity_colors(value)
    label = rarity.display_label if rarity is not None else _format_plain_value(value)
    _render_badges([_badge_html(label, background, foreground)])


def _render_tag_badges(value) -> None:
    tokens = _extract_tokens(value)
    if not tokens:
        return
    badges = []
    for tag in tokens:
        background, foreground = _tag_color(tag)
        badges.append(_badge_html(tag, background, foreground))
    _render_badges(badges)


def _render_filter_bar(
    title: str,
    db: str,
    df: pd.DataFrame,
    filter_fields: list[str],
    sort_options: list[str],
    default_sort: str,
) -> None:
    expander = st.expander("Filter", expanded=False)
    with expander:
        control_cols = st.columns([3, 2, 1], vertical_alignment="bottom")
        control_cols[0].text_input(
            "Suche",
            key=_state_key(db, "search"),
            placeholder="Name oder Stichwort suchen",
            on_change=set_to_databse_view,
            args=(db,),
        )
        control_cols[1].selectbox(
            "Sortierung",
            sort_options,
            key=_state_key(db, "sort"),
            on_change=set_to_databse_view,
            args=(db,),
        )
        control_cols[2].button(
            "Reset",
            key=_state_key(db, "reset"),
            use_container_width=True,
            on_click=_reset_database_filters,
            args=(db, filter_fields, default_sort),
        )

        if filter_fields:
            filter_cols = st.columns(len(filter_fields), vertical_alignment="top")
            for index, field in enumerate(filter_fields):
                filter_cols[index].multiselect(
                    field,
                    _filter_options(df, field),
                    key=_state_key(db, f"filter_{field}"),
                    on_change=set_to_databse_view,
                    args=(db,),
                )

        active_filter_count = int(
            bool(st.session_state[_state_key(db, "search")].strip())
        )
        active_filter_count += sum(
            1
            for field in filter_fields
            if st.session_state[_state_key(db, f"filter_{field}")]
        )
    st.caption(f"{len(df)} Einträge insgesamt • {active_filter_count} aktive Filter")


def _render_name(name: str) -> None:
    st.markdown(make_internal_links_clickable(f"[[{name}]]"), unsafe_allow_html=True)


def _render_label_value_in_column(
    column, label: str, value, rich: bool = False
) -> None:
    text = _format_rich_value(value) if rich else _format_plain_value(value)
    if not text:
        return
    column.markdown(f"**{label}:** {text}", unsafe_allow_html=rich)


def _render_token_regions(value) -> None:
    tokens = _extract_tokens(value)
    if not tokens:
        return
    st.markdown(
        "".join(_region_html(token) for token in tokens), unsafe_allow_html=True
    )


def _render_spell_card(row: dict) -> None:
    grad = _format_plain_value(row.get("Grad", ""))
    schule = _format_plain_value(row.get("Schule", ""))
    konzentration = _format_plain_value(row.get("Konzentration", ""))
    with st.container(border=True):
        _render_name(row.get("Name", ""))
        left_col, middle_col, right_col = st.columns(
            [4, 3, 2], vertical_alignment="top"
        )
        grad_col, school_col = left_col.columns([1, 1], vertical_alignment="top")
        with grad_col:
            _render_badges(
                [
                    _badge_html(f"Grad {grad}", *_level_colors(grad)) if grad else "",
                ]
            )
        with school_col:
            _render_badges(
                [
                    (
                        _badge_html(schule, *_mapped_colors(schule, SCHOOL_COLORS))
                        if schule
                        else ""
                    ),
                ]
            )
        with middle_col:
            _render_token_regions(row.get("Komponenten", ""))
        with right_col:
            if konzentration:
                st.caption(f"Konzentration: {konzentration}")


def _render_potion_card(row: dict) -> None:
    seltenheit = _format_plain_value(row.get("Seltenheit", ""))
    wert = _format_plain_value(row.get("Wert", ""))
    with st.container(border=True):
        _render_name(row.get("Name", ""))
        first_col, second_col, third_col, fourth_col = st.columns(
            [2, 3, 4, 2], vertical_alignment="top"
        )
        with first_col:
            _render_rarity_badge(seltenheit)
        with second_col:
            _render_tag_badges(row.get("Tags", ""))
        with third_col:
            tokens = _extract_tokens(row.get("Komponenten", ""))
            if tokens:
                third_col.markdown(
                    "".join(_region_html(token) for token in tokens),
                    unsafe_allow_html=True,
                )
        with fourth_col:
            if wert:
                st.caption(f"Wert: {wert}")


def _render_ingredient_card(row: dict) -> None:
    seltenheit = _format_plain_value(row.get("Seltenheit", ""))
    wert = _format_plain_value(row.get("Wert", ""))
    fundort = row.get("Fundort", "")
    with st.container(border=True):
        _render_name(row.get("Name", ""))
        left_col, middle_col, right_col = st.columns(
            [3, 3, 2], vertical_alignment="top"
        )
        with left_col:
            _render_rarity_badge(seltenheit)
        with middle_col:
            tokens = _extract_tokens(fundort)
            if tokens:
                middle_col.markdown(
                    "".join(_region_html(token) for token in tokens),
                    unsafe_allow_html=True,
                )
        with right_col:
            if wert:
                st.caption(f"Wert: {wert}")


def _render_bestiary_card(row: dict) -> None:
    stufe = _format_plain_value(row.get("Stufe", ""))
    volk = _format_plain_value(row.get("Volk", ""))
    with st.container(border=True):
        _render_name(row.get("Name", ""))
        left_col, middle_col, right_col = st.columns(
            [3, 3, 2], vertical_alignment="top"
        )
        with left_col:
            if stufe:
                st.caption(f"Stufe: {stufe}")
        with middle_col:
            if volk:
                st.caption(volk)
        with right_col:
            if row.get("Rüstungsklasse"):
                st.caption(f"Rüstungsklasse: {row.get('Rüstungsklasse')}")

        body_left, body_middle, body_right = st.columns(
            [3, 3, 2], vertical_alignment="top"
        )
        _render_label_value_in_column(
            body_left, "Grundlage", row.get("Grundlage", ""), rich=True
        )
        _render_label_value_in_column(
            body_middle, "Gesinnung", row.get("Gesinnung", "")
        )
        with body_right:
            pass


def _render_results_header(result_count: int) -> None:
    title_col, meta_col = st.columns([5, 1], vertical_alignment="center")
    title_col.markdown("### Treffer")
    meta_col.caption(f"{result_count} Einträge")


def _render_card_list(records: list[dict], renderer) -> None:
    for row in records:
        renderer(row)


def _render_database_browser(
    title: str,
    db: str,
    df: pd.DataFrame,
    search_fields: list[str],
    filter_fields: list[str],
    sort_options: list[str],
    default_sort: str,
    renderer,
) -> None:
    _ensure_database_state(db, filter_fields, default_sort)
    _render_filter_bar(title, db, df, filter_fields, sort_options, default_sort)

    filtered = _apply_database_filters(df, db, search_fields, filter_fields)
    records = _sort_records(
        filtered.to_dict("records"), st.session_state[_state_key(db, "sort")]
    )
    with st.container(border=True):
        _render_results_header(len(records))
        if not records:
            st.info("Keine Einträge passen zu den aktuellen Filtern.")
            return
        _render_card_list(records, renderer)


def bestiarium_view():
    columns = [
        "Name",
        "Stufe",
        "Volk",
        "Gesinnung",
        "Rüstungsklasse",
        "Grundlage",
    ]
    _render_database_browser(
        "Bestiarium",
        "Bestiarium",
        st.session_state["Bestiarium"][columns],
        search_fields=columns,
        filter_fields=["Stufe", "Volk", "Grundlage"],
        sort_options=["Name (A-Z)", "Name (Z-A)"],
        default_sort="Name (A-Z)",
        renderer=_render_bestiary_card,
    )


def zauberarchiev_view():
    columns = ["Name", "Grad", "Schule", "Komponenten", "Konzentration"]
    _render_database_browser(
        "Zauberarchiv",
        "Zauberarchiv",
        st.session_state["Zauberarchiv"][columns],
        search_fields=columns,
        filter_fields=["Grad", "Schule", "Komponenten", "Konzentration"],
        sort_options=["Grad -> Name", "Schule -> Name", "Name (A-Z)", "Name (Z-A)"],
        default_sort="Grad -> Name",
        renderer=_render_spell_card,
    )


def trank_view():
    columns = ["Name", "Tags", "Wert", "Komponenten", "Seltenheit"]
    potions_df = _prepare_potion_dataframe(st.session_state["Tranksammlung"][columns])
    _render_database_browser(
        "Tranksammlung",
        "Tranksammlung",
        potions_df,
        search_fields=columns,
        filter_fields=["Tags", "Komponenten", "Seltenheit"],
        sort_options=["Seltenheit -> Name", "Wert -> Name", "Name (A-Z)", "Name (Z-A)"],
        default_sort="Seltenheit -> Name",
        renderer=_render_potion_card,
    )


def zutaten_view():
    columns = ["Name", "Wert", "Seltenheit", "Fundort"]
    _render_database_browser(
        "Zutatenarchiv",
        "Zutatenarchiv",
        st.session_state["Zutatenarchiv"][columns],
        search_fields=columns,
        filter_fields=["Seltenheit", "Fundort"],
        sort_options=[
            "Seltenheit -> Name",
            "Fundort -> Name",
            "Name (A-Z)",
            "Name (Z-A)",
        ],
        default_sort="Seltenheit -> Name",
        renderer=_render_ingredient_card,
    )
