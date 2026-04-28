from sl_dashboard.models import (
    DashboardData,
    DashboardLink,
    DashboardNpc,
    DashboardScene,
    DashboardTool,
    SessionStatus,
)


def build_demo_dashboard_data() -> DashboardData:
    return DashboardData(
        status=SessionStatus(
            session_title="Sitzung 12 - Schatten ueber Morgenfels",
            in_game_date="27. Tag des Aschmonds, 842 n.R.",
            region="Drakmora / Morgenfels",
            current_scene="Ankunft im Westtor",
            current_goal="Die Gruppe in die Stadtkonflikte ziehen, ohne sofort Kampf zu erzwingen.",
            pacing="angespannt",
            open_threads=(
                "Wer bezahlt die Sumpfbanden im Umland?",
                "Der Bote aus Schwarzklamm ist noch nicht eingetroffen.",
                "Nyssara kennt den Namen des Informanten, verschweigt ihn aber.",
            ),
        ),
        current_scene=DashboardScene(
            title="Ankunft im Westtor",
            status="aktiv",
            summary=(
                "Die Gruppe erreicht Morgenfels kurz vor Sonnenuntergang und trifft"
                " auf ueberforderte Wachen, Geruechte ueber verschwundene Lieferungen"
                " und eine angespannte Stadtstimmung."
            ),
            location="Morgenfels / Westtor",
            id="ankunft-im-westtor",
            goal="Die Gruppe soll zwischen Ordnung, Misstrauen und der ersten Spur waehlen muessen.",
            atmosphere="Misstrauen, Hektik und das Gefuehl, dass die Stadt etwas verheimlicht.",
            pressure="Wenn die Gruppe zoegert, verschwindet eine wichtige Spur noch vor Einbruch der Nacht.",
            stakes=(
                "Vertrauen der Stadtwache gewinnen oder verlieren.",
                "Den ersten Hinweis auf den Schmugglerring sichern.",
            ),
            discoveries=(
                "Am Tor liegt frischer Schlamm mit Spuren eines schweren Wagens.",
                "Eine Wachliste wurde hastig geaendert und ein Name fehlt.",
                "Ein Haendlerjunge hat mehr gesehen, als er offen sagen will.",
            ),
            likely_player_actions=(
                "Die Wachen getrennt befragen.",
                "Dem verschwundenen Wagen folgen.",
                "Direkt den Kontakt im Gasthaus aufsuchen.",
            ),
            hidden_truths=(
                "Eine der Wachen arbeitet fuer die Schmuggler.",
                "Der verschwundene Wagen wurde absichtlich umgeleitet.",
            ),
        ),
        next_scenes=(
            DashboardScene(
                title="Gasthaus Zum Grauen Kranich",
                status="vorbereitet",
                summary="Kontaktaufnahme mit der Informantin und erster sozialer Druck.",
                location="Morgenfels / Marktviertel",
                id="gasthaus-zum-grauen-kranich",
                goal="Nyssara als nuetzliche, aber riskante Verbuendete etablieren.",
                pressure="Nyssara zieht sich zurueck, wenn die Gruppe zu offen auftritt.",
            ),
            DashboardScene(
                title="Lagerhaus am Fluss",
                status="optional",
                summary="Moeglicher Uebergang in Infiltration oder Kampf.",
                location="Morgenfels / Unterhafen",
                id="lagerhaus-am-fluss",
                goal="Den Schmugglerring sichtbar machen und die Lage eskalieren lassen.",
                pressure="Die Schmuggler beginnen mit dem Umladen, sobald es ganz dunkel ist.",
            ),
        ),
        npcs=(
            DashboardNpc(
                name="Nyssara Vale",
                role="Informantin",
                motivation="Will den Schmugglerring schwaechen, ohne selbst aufzufliegen.",
                tension="misstrauisch",
                species="Mensch",
                location="Morgenfels / Marktviertel",
                voice="ruhig, praezise, mit absichtlichen Luecken",
            ),
            DashboardNpc(
                name="Hauptmann Ser Daran",
                role="Wachoffizier",
                motivation="Muss Ordnung demonstrieren, obwohl ihm die Kontrolle entgleitet.",
                tension="unter Druck",
                species="Mensch",
                location="Morgenfels / Westtor",
                voice="knapp, autoritaer, schnell gereizt",
            ),
        ),
        quick_links=(
            DashboardLink(
                title="Morgenfels",
                context="Ort",
                reason="fuer Stimmung, Fraktionen und Ortswechsel",
            ),
            DashboardLink(
                title="Nyssara Vale",
                context="NSC",
                reason="sofort griffbereit fuer den ersten sozialen Knotenpunkt",
            ),
            DashboardLink(
                title="Sumpfbanden",
                context="Fraktion",
                reason="wahrscheinlicher roter Faden der Sitzung",
            ),
        ),
        tools=(
            DashboardTool(
                title="Encounter-Rechner",
                description="Kampfschwierigkeit, Volatilitaet und Ressourcenlast schnell pruefen.",
                status="bestehend",
                emphasis="hoch",
            ),
            DashboardTool(
                title="NSC-Schnellansicht",
                description="Kurzprofil mit Motivation, Haltung und Stimme.",
                status="geplant",
            ),
            DashboardTool(
                title="Sitzungsnotizen",
                description="Private Notizen fuer Verlauf, Improvisation und Folgen.",
                status="geplant",
            ),
        ),
        notes=(
            "Wenn die Gruppe beim Westtor eskaliert, zieht Ser Daran zwei Veteranen hinzu.",
            "Nyssara gibt Informationen nur gegen eine sofortige Gegenleistung preis.",
        ),
        alerts=(
            "Offener Konflikt mit der Wache verschiebt die Sitzung sofort in eine Verfolgung.",
            "Die erste echte Entscheidung sollte spaetestens nach 10 Minuten fallen.",
        ),
    )
