import streamlit as st


def apply_sl_parchment_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
            --sl-parchment-base: #d8c19a;
            --sl-parchment-base-deep: #bea070;
            --sl-parchment-surface: rgba(236, 224, 196, 0.88);
            --sl-parchment-surface-strong: rgba(229, 214, 185, 0.94);
            --sl-parchment-border: #9e7b4d;
            --sl-parchment-border-strong: #6f5332;
            --sl-parchment-ink: #312215;
            --sl-parchment-muted: #5f4a35;
            --sl-parchment-accent: #674224;
            --sl-parchment-accent-soft: #c7a874;
            --sl-seal-accent: #6f3a2f;
            --sl-seal-accent-soft: rgba(111, 58, 47, 0.1);
        }

        html, body, [class*="css"] {
            font-family: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", Georgia, serif;
        }

        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(circle at 12% 8%, rgba(247, 239, 216, 0.7), transparent 20%),
                radial-gradient(circle at 86% 14%, rgba(116, 79, 42, 0.08), transparent 16%),
                radial-gradient(circle at 78% 84%, rgba(142, 101, 56, 0.12), transparent 22%),
                linear-gradient(180deg, rgba(84, 58, 34, 0.05) 0%, rgba(84, 58, 34, 0) 12%),
                repeating-linear-gradient(
                    0deg,
                    rgba(255, 250, 239, 0.03) 0px,
                    rgba(255, 250, 239, 0.03) 1px,
                    rgba(115, 86, 54, 0.018) 1px,
                    rgba(115, 86, 54, 0.018) 3px
                ),
                linear-gradient(180deg, #eadbb7 0%, var(--sl-parchment-base) 48%, var(--sl-parchment-base-deep) 100%);
            color: var(--sl-parchment-ink);
        }

        [data-testid="stHeader"] {
            background: rgba(229, 216, 186, 0.72);
            border-bottom: 1px solid rgba(111, 83, 50, 0.14);
            backdrop-filter: blur(6px);
        }

        [data-testid="stSidebar"] {
            background:
                radial-gradient(circle at 18% 10%, rgba(255, 245, 222, 0.24), transparent 20%),
                linear-gradient(180deg, rgba(89, 62, 36, 0.1) 0%, rgba(89, 62, 36, 0.03) 100%),
                linear-gradient(180deg, #e5d1aa 0%, #c9ac7d 100%);
            border-right: 1px solid rgba(111, 83, 50, 0.2);
        }

        [data-testid="stSidebar"] * {
            color: var(--sl-parchment-ink);
        }

        h1, h2, h3, h4, h5, h6,
        p, label, span, div,
        [data-testid="stMarkdownContainer"] {
            color: var(--sl-parchment-ink);
        }

        [data-testid="stCaptionContainer"] {
            color: var(--sl-parchment-muted);
        }

        a {
            color: var(--sl-seal-accent);
            text-decoration-color: rgba(124, 63, 52, 0.35);
        }

        a:hover {
            color: #542117;
        }

        [data-testid="stTabs"] [data-baseweb="tab-list"] {
            gap: 0.35rem;
            background: rgba(100, 72, 43, 0.07);
            border: 1px solid rgba(111, 83, 50, 0.14);
            border-radius: 999px;
            padding: 0.25rem;
            box-shadow: inset 0 1px 1px rgba(68, 48, 28, 0.05);
        }

        [data-testid="stTabs"] [data-baseweb="tab"] {
            border-radius: 999px;
            color: var(--sl-parchment-muted);
            background: transparent;
        }

        [data-testid="stTabs"] [aria-selected="true"] {
            background: linear-gradient(180deg, rgba(194, 164, 114, 0.38) 0%, rgba(157, 118, 77, 0.2) 100%);
            color: var(--sl-seal-accent);
            font-weight: 700;
        }

        [data-testid="stVerticalBlockBorderWrapper"] {
            background:
                radial-gradient(circle at top, rgba(255, 247, 229, 0.18), transparent 38%),
                linear-gradient(180deg, rgba(255, 247, 229, 0.12) 0%, rgba(255, 247, 229, 0) 28%),
                var(--sl-parchment-surface);
            border: 1px solid rgba(111, 83, 50, 0.2);
            box-shadow: 0 8px 18px rgba(78, 55, 30, 0.06);
            border-radius: 1rem;
        }

        [data-testid="stButton"] > button,
        [data-testid="stLinkButton"] > a {
            border-radius: 0.75rem;
            border: 1px solid var(--sl-parchment-border) !important;
            background: linear-gradient(180deg, #ead9b4 0%, #d1af7a 100%) !important;
            color: var(--sl-parchment-accent) !important;
            box-shadow: 0 1px 4px rgba(78, 55, 30, 0.06) !important;
            text-decoration: none !important;
        }

        [data-testid="stButton"] > button[kind="primary"],
        [data-testid="stLinkButton"] > a[kind="primary"] {
            border-color: var(--sl-parchment-border-strong) !important;
            background: linear-gradient(180deg, #cda565 0%, #a87646 60%, #8d5738 100%) !important;
            color: #24150b !important;
        }

        [data-testid="stButton"] > button:hover,
        [data-testid="stLinkButton"] > a:hover {
            border-color: var(--sl-parchment-border-strong) !important;
            color: #4f3118 !important;
        }

        [data-testid="stButton"] > button[kind="secondary"]:hover,
        [data-testid="stLinkButton"] > a[kind="secondary"]:hover {
            background: linear-gradient(180deg, #efdfbc 0%, #dcc08f 100%) !important;
        }

        [data-testid="stButton"] > button[kind="secondary"] {
            background: linear-gradient(180deg, #ead9b4 0%, #d1af7a 100%) !important;
            color: var(--sl-parchment-accent) !important;
        }

        [data-testid="stButton"] > button:active,
        [data-testid="stLinkButton"] > a:active {
            transform: translateY(1px);
        }

        [data-testid="stSelectbox"] [data-baseweb="select"] > div,
        [data-testid="stTextInputRootElement"] > div,
        [data-testid="stTextAreaRootElement"] textarea {
            background: rgba(240, 228, 199, 0.94);
            border-color: rgba(111, 83, 50, 0.24);
            box-shadow: inset 0 1px 1px rgba(74, 52, 28, 0.04);
            color: var(--sl-parchment-ink);
        }

        [data-testid="stCodeBlock"] {
            border: 1px solid rgba(111, 83, 50, 0.16);
        }

        [data-testid="stElementToolbar"] {
            opacity: 0.58;
        }

        .app-breadcrumbs__prefix {
            color: var(--sl-parchment-muted) !important;
        }

        .app-breadcrumbs__button {
            color: var(--sl-parchment-accent) !important;
        }

        .app-breadcrumbs__current {
            color: var(--sl-seal-accent) !important;
        }

        .app-breadcrumbs__sep {
            color: var(--sl-parchment-border) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
