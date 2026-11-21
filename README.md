# phonetic-obliterator

An Agent Skill that cuts phonemes but keeps SEO. Built for Claude Code; also runs on other agents that read `SKILL.md` skills.

1. It maps each word with the CMU Pronouncing Dictionary.
2. It finds top keywords via DataForSEO and locks them.
3. It cuts the rest by your level:

| Level | Cut (unlocked phonemes) |
|---|---|
| low | 20% |
| medium | 40% |
| high | 60% |

Cut too lossy? It reads it cold, drops a level and redoes it. Add `strict` to keep your level.

Pick from 57 styles (`phonetic-obliterator/styles.md`). Auto fits your voice, or logs a new one to `~/.agents/phonetic-obliterator/my-styles.md` (or to `~/.claude/phonetic-obliterator/my-styles.md`, if you already have that file). Updates keep it. No git needed.

## Install

Copy the `phonetic-obliterator/` folder to your agent's skills folder:

| Agent | Project folder | Personal folder |
|---|---|---|
| Claude Code | `.claude/skills/` | `~/.claude/skills/` |
| OpenAI Codex | `.agents/skills/` | `~/.agents/skills/` |
| Gemini CLI | `.gemini/skills/` or `.agents/skills/` | `~/.gemini/skills/` or `~/.agents/skills/` |
| GitHub Copilot | `.github/skills/`, `.claude/skills/` or `.agents/skills/` | `~/.copilot/skills/` or `~/.agents/skills/` |
| Cursor | `.agents/skills/` or `.cursor/skills/` | `~/.agents/skills/` or `~/.cursor/skills/` |

Paths are from each tool's docs. `.agents/skills/` covers all but Claude Code, whose docs list only `.claude/skills/`.

Then run:

```
pip install cmudict
```

The agent must run code. Chat-only LLMs can't run the counter, so they can't use this skill as designed.

Locks need DataForSEO, via one of:

- a DataForSEO MCP server in your agent, or
- env vars `DATAFORSEO_USERNAME` and `DATAFORSEO_PASSWORD` (your API login and password). The skill then runs `scripts/dataforseo.py`.

No DataForSEO? No locks; it cuts it all.

## Use

In Claude Code:

```
/phonetic-obliterator medium auto <text>
/phonetic-obliterator high witchy United Kingdom <text>
```

Elsewhere, ask: "phonetically obliterate this at medium, auto style: <text>".

## Counter script

Run the phoneme counter alone. On Windows, use `python` if `python3` isn't found.

```
python3 phonetic-obliterator/scripts/phonemes.py count text.txt --ipa
python3 phonetic-obliterator/scripts/phonemes.py check original.txt new.txt --level medium --lock "lesser houseflies"
```

DataForSEO script (`check` is free; the others cost cents):

```
python3 phonetic-obliterator/scripts/dataforseo.py check
python3 phonetic-obliterator/scripts/dataforseo.py volumes "house fly" "lesser house fly"
python3 phonetic-obliterator/scripts/dataforseo.py suggestions "house fly" --limit 20
```

## License

[MIT](LICENSE)

## Made by

[Alio! Brand Studio](https://aliobrandstudio.com): web design and local SEO, Sydney.
