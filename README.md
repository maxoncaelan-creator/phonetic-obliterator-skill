# phonetic-obliterator

A Claude Code skill that cuts phonemes but keeps SEO.

1. It maps each word with the CMU Pronouncing Dictionary.
2. It finds top keywords via DataForSEO and locks them.
3. It cuts the rest by your level:

| Level | Cut (unlocked phonemes) |
|---|---|
| low | 20% |
| medium | 40% |
| high | 60% |

Pick from 57 styles (`phonetic-obliterator/styles.md`). Auto fits your voice, or logs a new one.

## Install

Copy the `phonetic-obliterator/` folder to your skills folder (`~/.claude/skills/` or `<project>/.claude/skills/`). Then run:

```
pip install cmudict
```

Locks need DataForSEO. No DataForSEO? No locks; it cuts it all.

## Use

```
/phonetic-obliterator medium auto <text>
/phonetic-obliterator high witchy United Kingdom <text>
```

## Counter script

Run the phoneme counter alone:

```
python3 phonetic-obliterator/scripts/phonemes.py count text.txt --ipa
python3 phonetic-obliterator/scripts/phonemes.py check original.txt new.txt --level medium --lock "lesser houseflies"
```

## License

[MIT](LICENSE)
