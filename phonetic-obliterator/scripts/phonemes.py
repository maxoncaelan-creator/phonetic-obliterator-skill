#!/usr/bin/env python3
"""Phoneme counter for the phonetic-obliterator skill.

Uses the CMU Pronouncing Dictionary (pip package `cmudict`, ARPAbet phonemes,
General American). Words missing from the dictionary are split into two
dictionary words where possible (lampshade -> lamp + shade); otherwise they
must be supplied with --pron.

Subcommands
  count FILE [--ipa] [--pron WORD=ARPABET ...]
      Transcribe every word and print the phoneme total.

  check ORIGINAL CANDIDATE --level low|medium|high
        [--lock "phrase" ...] [--pron WORD=ARPABET ...] [--tolerance N]
      Verify that every locked phrase survives verbatim, then compare the
      phonemes OUTSIDE the locked phrases against the level's target
      reduction (low 20%, medium 40%, high 60%). Exits 0 on pass, 1 on fail.

  target ORIGINAL --level low|medium|high [--lock "phrase" ...]
      Print the phoneme budget the rewritten remainder must hit.

Only alphabetic words (and apostrophes) are counted; emojis, numbers and
punctuation are ignored. Pass header/sign-off lines separately or strip them
first if they should not count.
"""
import argparse
import re
import sys

try:
    import cmudict
except ImportError:
    sys.exit("cmudict is not installed. Run: pip install cmudict")

LEVELS = {"low": 20, "medium": 40, "high": 60}

IPA = {'AA': 'ɑ', 'AE': 'æ', 'AH': 'ʌ', 'AO': 'ɔ', 'AW': 'aʊ', 'AY': 'aɪ', 'B': 'b',
       'CH': 'tʃ', 'D': 'd', 'DH': 'ð', 'EH': 'ɛ', 'ER': 'ɝ', 'EY': 'eɪ', 'F': 'f',
       'G': 'ɡ', 'HH': 'h', 'IH': 'ɪ', 'IY': 'i', 'JH': 'dʒ', 'K': 'k', 'L': 'l',
       'M': 'm', 'N': 'n', 'NG': 'ŋ', 'OW': 'oʊ', 'OY': 'ɔɪ', 'P': 'p', 'R': 'ɹ',
       'S': 's', 'SH': 'ʃ', 'T': 't', 'TH': 'θ', 'UH': 'ʊ', 'UW': 'u', 'V': 'v',
       'W': 'w', 'Y': 'j', 'Z': 'z', 'ZH': 'ʒ'}

WORD_RE = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)*")

_D = None


def dictionary(prons):
    global _D
    if _D is None:
        _D = cmudict.dict()
    for p in prons or []:
        word, _, arpa = p.partition("=")
        if not arpa.strip():
            sys.exit(f"Bad --pron '{p}'. Use WORD=ARPABET, e.g. housefly=HH AW1 S F L AY2")
        _D[word.strip().lower()] = [arpa.split()]
    return _D


def lookup(word, d):
    """Return (phonemes, source) or (None, None)."""
    k = word.lower()
    if k in d:
        return d[k][0], "cmudict"
    for i in range(2, len(k) - 1):  # try a two-word compound split
        a, b = k[:i], k[i:]
        if a in d and b in d and len(a) > 1 and len(b) > 1:
            return d[a][0] + d[b][0], f"split {a}+{b}"
    return None, None


def to_ipa(phones):
    out = []
    for x in phones:
        base = re.sub(r"\d", "", x)
        sym = 'ə' if x == 'AH0' else ('ɚ' if x == 'ER0' else IPA[base])
        out.append(('ˈ' if x.endswith('1') else '') + sym)
    return ''.join(out)


def transcribe(text, d):
    rows, missing = [], []
    for w in WORD_RE.findall(text):
        ph, src = lookup(w, d)
        if ph is None:
            missing.append(w)
        else:
            rows.append((w, ph, src))
    return rows, missing


def total(text, d):
    rows, missing = transcribe(text, d)
    return sum(len(r[1]) for r in rows), missing


def norm(s):
    return " ".join(w.lower() for w in WORD_RE.findall(s))


def locked_phonemes(text, locks, d):
    """Count phonemes used by each locked phrase occurrence; report absent ones."""
    body = " " + norm(text) + " "
    used, absent, detail = 0, [], []
    for phrase in locks:
        n = norm(phrase)
        occ = body.count(" " + n + " ")
        if occ == 0:
            absent.append(phrase)
            continue
        per, miss = total(phrase, d)
        if miss:
            sys.exit(f"Locked phrase '{phrase}' has words with no pronunciation: {miss}. Add --pron.")
        used += per * occ
        detail.append((phrase, per, occ))
    return used, absent, detail


def fail_missing(missing):
    sys.exit("No pronunciation for: " + ", ".join(sorted(set(missing))) +
             "\nAdd each with --pron WORD=ARPABET (stress digits 0/1/2 on vowels).")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("count", "check", "target"):
        p = sub.add_parser(name)
        p.add_argument("original")
        if name == "check":
            p.add_argument("candidate")
        if name != "count":
            p.add_argument("--level", choices=LEVELS, required=True)
            p.add_argument("--lock", action="append", default=[])
        if name == "check":
            p.add_argument("--tolerance", type=float, default=3.0,
                           help="allowed percentage-point miss either side of target (default 3)")
        if name == "count":
            p.add_argument("--ipa", action="store_true")
        p.add_argument("--pron", action="append", default=[])
    a = ap.parse_args()
    d = dictionary(a.pron)
    orig = open(a.original, encoding="utf-8").read()

    if a.cmd == "count":
        rows, missing = transcribe(orig, d)
        if missing:
            fail_missing(missing)
        if a.ipa:
            for w, ph, src in rows:
                note = "" if src == "cmudict" else f"  ({src})"
                print(f"{w:16} /{to_ipa(ph)}/  {' '.join(ph)}  {len(ph)}{note}")
        print("TOTAL PHONEMES:", sum(len(r[1]) for r in rows))
        return

    o_total, missing = total(orig, d)
    if missing:
        fail_missing(missing)
    o_lock, absent, detail = locked_phonemes(orig, a.lock, d)
    if absent:
        sys.exit(f"Locked phrases not found in the original: {absent}")
    o_rem = o_total - o_lock
    pct = LEVELS[a.level]
    budget = round(o_rem * (100 - pct) / 100)

    print(f"Level: {a.level} ({pct}% reduction of unlocked phonemes)")
    for phrase, per, occ in detail:
        print(f"  LOCK '{phrase}': {per} phonemes x {occ}")
    print(f"Original: {o_total} total = {o_lock} locked + {o_rem} unlocked")
    print(f"Unlocked budget: {budget} phonemes (total target {budget + o_lock})")
    if a.cmd == "target":
        return

    cand = open(a.candidate, encoding="utf-8").read()
    c_total, missing = total(cand, d)
    if missing:
        fail_missing(missing)
    c_lock, c_absent, c_detail = locked_phonemes(cand, a.lock, d)
    ok = True
    if c_absent:
        print(f"FAIL: locked phrases missing or altered in candidate: {c_absent}")
        ok = False
    for (phrase, _, o_occ), (_, _, c_occ) in zip(detail, c_detail):
        if c_occ < o_occ:
            print(f"NOTE: '{phrase}' appears {c_occ}x in candidate vs {o_occ}x in original")
    c_rem = c_total - c_lock
    achieved = 100 * (o_rem - c_rem) / o_rem if o_rem else 0.0
    overall = 100 * (o_total - c_total) / o_total if o_total else 0.0
    print(f"Candidate: {c_total} total = {c_lock} locked + {c_rem} unlocked")
    print(f"Unlocked reduction: {achieved:.1f}% (target {pct}% +/- {a.tolerance})")
    print(f"Overall reduction:  {overall:.1f}%")
    if abs(achieved - pct) > a.tolerance:
        direction = "cut more" if achieved < pct else "cut less (restore words)"
        print(f"FAIL: off target by {achieved - pct:+.1f} points; {direction}. "
              f"Aim for {budget} unlocked phonemes, now {c_rem}.")
        ok = False
    print("PASS" if ok else "RESULT: FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
