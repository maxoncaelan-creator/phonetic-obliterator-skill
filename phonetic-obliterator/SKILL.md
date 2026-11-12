---
name: phonetic-obliterator
description: SEO-safe phoneme reduction. Finds the best search keywords already in a text with DataForSEO, locks those phrases, then rewrites everything else to cut its phoneme count by a set level (low 20%, medium 40%, high 60%), checked with CMU Pronouncing Dictionary counts, in a chosen style from a registry of 57 (e.g. none, clean, corporate, moody, emo-metal, lusty, whimsy, witchy, noir, pirate, nature-documentary; see styles.md), or auto, which detects the text's style and records a new one if none fits. Use when the user asks to "phonetically obliterate" a text, cut its phonemes while keeping keywords, or invokes /phonetic-obliterator. Arguments are the level (default high), the style (default auto), an optional location (default United States), and the text.
argument-hint: "[low|medium|high] [auto|<style from styles.md>|<new style name>] [location] <text>"
---

# Phonetic Obliterator

Shortens a text by **phonemes**, not words, while keeping the words searchers use.

| Level | Reduction of unlocked phonemes |
|---|---|
| low | 20% |
| medium | 40% |
| high (default) | 60% |

The reduction applies only to phonemes **outside** the locked keyword phrases. Locked phrases are never changed, so the reduction across the whole text comes out a bit lower. Report both numbers.

The counter is `scripts/phonemes.py` in this skill's folder (`.claude/skills/phonetic-obliterator/scripts/phonemes.py`). Use it for every count. Never estimate phonemes by hand.

## Step 0: Setup

1. Run `python3 -c "import cmudict"`. If that fails, run `pip install cmudict`.
2. Parse the arguments:
   - **Level:** low, medium or high. The default is high.
   - **Style:** any style name in `styles.md` (in this skill's folder), or `auto`. The default is `auto`. Match loosely: "emo metal" means `emo-metal`, and "no style" or "plain" means `none`. If the user names a style that isn't in the registry, treat it as an auto-recorded style using the name they gave (see "Auto style").
   - **Location:** default United States (`location_code` 2840, `language_code` "en").
   - **Text:** the rest of the arguments, or what the user pasted. If no text is given, ask for it.
3. Split off the parts that should not be counted or changed: headers (e.g. "🪰 DID YOU KNOW?"), sign-offs/bylines (e.g. a brand name at the end), emojis and hashtags. Keep them as they are and put them back at the end.
4. Write the countable body to `original.txt` in the scratchpad directory.

## Step 1: Phonetic transcription

Run `python3 phonemes.py count original.txt --ipa`. This prints every word with its IPA and ARPAbet spelling plus the phoneme total.
- The script splits words it can't find into two dictionary words (lampshade becomes lamp + shade).
- If it still stops with "No pronunciation for", add each missing word with `--pron WORD=ARPABET` and give stress digits on the vowels, e.g. `--pron housefly="HH AW1 S F L AY2"`. Reuse the same `--pron` flags on every later call.

## Step 2: Keyword research (DataForSEO)

### 2a. DataForSEO check (always run this first)

Find out whether the user has a working DataForSEO connection before any keyword work:

1. **Look for the tool.** Run ToolSearch with `select:mcp__DataForSEO__api_request`. If nothing is found, search for `dataforseo` too, since the tool may be under a plugin prefix or still connecting.
2. **Test the account.** If the tool loads, call it with `method: "GET"`, `path: "/v3/appendix/user_data"`. This is a free account lookup. It passes only if the response has `status_code` 20000.
3. **Decide:**
   - **PASS:** continue with Step 2b.
   - **FAIL:** skip Step 2b and **continue without keyword locks**. Failing means the tool wasn't found, the server needs sign-in or failed to connect, the call errored, or the `status_code` wasn't 20000.
     - Don't stop to ask, and don't make up search volumes.
     - Use no `--lock` flags in Steps 3 and 4, so the level's reduction applies to the whole text.
     - In the output, say "DataForSEO check: not available (<reason>). No keywords were locked." Mention that connecting DataForSEO adds keyword locks on the next run.
     - If the user names phrases to keep anyway, lock those as user locks. Don't present them as SEO keywords.

### 2b. Keyword research (only if the check passed)

1. **Make candidates.** Pick 15–25 search phrases that someone looking for this text's content might type. Include:
   - Phrases taken from the text, normalized to how people search. "lesser houseflies" becomes "lesser house fly"; "attracted to the light" becomes "flies attracted to light".
   - Question forms ("why do flies fly in circles").
   - Short head terms.
2. **Get volumes.** POST `/v3/dataforseo_labs/google/keyword_overview/live` with `[{"keywords":[...], "location_code":..., "language_code":...}]`.
3. **Optional expansion.** For the two strongest seed terms, POST `/v3/dataforseo_labs/google/keyword_suggestions/live` with `{"keyword": seed, ..., "limit": 20, "order_by": ["keyword_info.search_volume,desc"]}`. Score any new phrases.
4. **Choose phrases to lock.** A keyword can only be locked if its wording **already appears in the original text**, as a phrase of consecutive words. Small changes in plural, articles or spacing are fine: the keyword "lesser house fly" matches the text "lesser houseflies". Lock the **text's wording**, not the keyword's.
   - Rank matches by search volume. Low keyword difficulty breaks ties.
   - Skip matches under about 30 searches a month unless nothing better matches.
   - Usually lock 1–4 phrases.
   - Don't lock a phrase so long that it leaves too little to cut.
5. Show a table: keyword | volume | difficulty | found in text? (quote the wording) | locked?

## Step 3: Set the budget

Run:

```
python3 phonemes.py target original.txt --level <level> --lock "<phrase 1>" --lock "<phrase 2>"
```

It prints the locked phonemes, the unlocked phonemes and the **unlocked budget**: the most phonemes the rewritten unlocked text may use.

## Step 4: Rewrite

Rewrite the body to fit the budget:
- **Locked phrases:** keep each one word-for-word, in the same order, and the same number of times. They may move to a new sentence, but their words don't change.
- **Facts:** keep the core facts and the main point. Drop filler, hedges and repeated ideas first.
- **Cheap words:** prefer words with fewer phonemes ("seen" over "noticed", "spin" over "reversing"). Contractions help.
- **Rhythm:** keep it readable and natural, never a word list.
- **Style:** read the style's entry in `styles.md` and follow its Voice, Do and Avoid. Get the style from word choice, not added length; it has to fit the same budget. A style never overrides locks or facts.
- **Specific words the user asks to keep:** treat them as extra locks and add a `--lock` for each.

Write the draft to `candidate.txt`, then run:

```
python3 phonemes.py check original.txt candidate.txt --level <level> --lock ... [--pron ...]
```

If the result is FAIL, edit the draft and run the check again. Cut more when the reduction is under target; add words back when it is over. Repeat until it prints PASS (within ±3 points of target). Stop after 6 tries and report the closest version.

## Auto style

Use this when the style is `auto`, or when the user names a style that isn't in the registry.

1. **Read the original's voice.** Look at its tone, audience, register, emoji use, sentence rhythm and signature phrases.
2. **Match it.** Compare against every entry in `styles.md`, including auto-recorded ones.
   - If one fits cleanly (its Voice describes the text, and nothing in the text breaks its Avoid list), use it. Say "Auto style: <name>" and give a one-line reason.
   - If none fits cleanly, **determine the style** yourself:
     - Give it a short kebab-case name, e.g. `cosy-naturalist`, with a Voice, Do and Avoid that describe this text.
     - Add a Sample line from the rewritten text.
     - Add a `Recorded:` line with today's date and a few words on the source.
   - If the user named an unknown style, build the entry from their name and intent instead of from the text.
3. **Record it.** Append the new entry under the `AUTO-RECORDED STYLES` marker at the bottom of `styles.md`.
   - Never edit or delete existing entries while recording.
   - Tell the user it was recorded and show the entry.
   - If the skill is in a git repo, offer to commit it. Recorded styles are lost when a cloud session ends unless committed.
4. Rewrite in the chosen or recorded style as in Step 4.

A recorded style can be used by name in later runs, e.g. `/phonetic-obliterator medium cosy-naturalist <text>`.

## Step 5: Output

1. The final text, with header, emojis and sign-off put back. Mark locked phrases with 🔒 and bold **only** in the preview. Also give a clean, copy-ready version with no markers.
2. The style used, saying whether you chose it automatically and whether it was newly recorded.
3. Stats:
   - original phonemes = locked + unlocked
   - new phonemes = locked + unlocked
   - reduction of unlocked phonemes (the level target)
   - overall reduction
4. The result of the DataForSEO check (passed, or not available with the reason), then the keyword table from Step 2b. If there was no check pass, say no keywords were locked.
5. Things to flag:
   - **Unused high-volume keywords:** ones that weren't in the text and so couldn't be locked. Offer to work them in.
   - **Exact-match tradeoffs:** places where the locked wording differs from the searched keyword, and switching would mean changing a lock.
   - **Location:** say which one was used.
   - **Pronunciation:** CMUdict uses one General American pronunciation per word, so other accents change counts slightly.
6. Point to the IPA transcriptions of both versions (`count --ipa`) in the scratchpad. Give full absolute paths.
