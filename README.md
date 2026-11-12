# phonetic-obliterator

A Claude Code skill for SEO-safe phoneme reduction.

1. Transcribes a text phonetically with the CMU Pronouncing Dictionary.
2. Finds the best search keywords already in the text, using DataForSEO.
3. Locks those keyword phrases so they are never changed.
4. Rewrites everything else to cut its phoneme count by a set level:

| Level | Phoneme cut outside the locked keywords |
|---|---|
| low | 20% |
| medium | 40% |
| high | 60% |

The rewrite can be in any of 57 styles (see `phonetic-obliterator/styles.md`). The default, `auto`, matches the text's own voice, and records a new style if none fits.

## Install

Copy the `phonetic-obliterator/` folder into `~/.claude/skills/` (every project) or `<project>/.claude/skills/` (one project). Then run:

```
pip install cmudict
```

Keyword locking needs the DataForSEO MCP connector. The skill checks for it on every run. If DataForSEO is missing or not signed in, the skill continues without keyword locks, and the level applies to the whole text.

## Use

```
/phonetic-obliterator medium auto <text>
/phonetic-obliterator high witchy United Kingdom <text>
```

## Counter script

You can also run the phoneme counter on its own:

```
python3 phonetic-obliterator/scripts/phonemes.py count text.txt --ipa
python3 phonetic-obliterator/scripts/phonemes.py check original.txt new.txt --level medium --lock "lesser houseflies"
```
