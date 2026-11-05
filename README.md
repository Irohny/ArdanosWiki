# Wiki of my DnD Campain

Tools: Obsidian, Streamlit
Visible at: <https://ardanoswiki.streamlit.app/>

## LLM context export

Build a compact GM-only lore context file for session and campaign planning:

```text
just context
```

The command writes the prompt-ready export to `context/llm_gm_context.md`.

## Campaign and character visibility

Store login credentials in Streamlit secrets using `user_name` as the account key:

```toml
[[users]]
user_name = "vishuda-login"
password = "..."
```

Player access is loaded from `World/Zugriffsrechte/Spielerrechte.md`; do not duplicate these entries in Python. Each level-one heading starts a player record. `username` matches the secret account's `user_name`, `role` sets that player's own role, `charaktere` links character profiles whose `charakter_id` grants the player's access, and `kampangen` lists campaign names or aliases.

```markdown
# Vishuda-Spieler
**username:** [[vishuda-login]]
**role**: player
**charaktere**:
- [[Vishuda]]
**kampangen:**
- [[Schatten der Zeit]]
```

`World/Zugriffsrechte/Kampangen Mappings.md` maps each canonical `Kampangen Name` to its `Alias`. Both names resolve to the same campaign; the canonical name is displayed in the UI, never the working alias. Campaign IDs are stable slugs derived from the canonical name. Character-profile `kampagne` metadata determines the available mapped campaigns; filtering does not itself grant document access.

Documents use a character-ID list for whole-file access and a separate heading-to-ID mapping for restricted sections:

```yaml
sichtbarkeit: [gnodomir, vishuda]
abschnitt_sichtbarkeit:
  "Geheime Details": [vishuda]
```

Use `sichtbarkeit: []` for a public document. A non-empty list grants access only to assigned characters. Section rules hide the matching heading and its contents from other characters; an empty ID list makes that section GameMaster-only. Headings used by a rule must be unique. Missing or invalid visibility metadata is denied to players. `status: DM`, `zugriff: spielleitung`, and files under `World/Spielleiter` are GameMaster-only.

For players, the `Ziele`, `Plot-Hooks`, `Spielleiter`, and `Kampfwerte` sections are always hidden. The `Geheime Informationen` heading is hidden as well; its content is visible only to characters granted by a non-empty `abschnitt_sichtbarkeit` entry for that heading, or by the document's non-empty `sichtbarkeit` list when no section entry is defined.
