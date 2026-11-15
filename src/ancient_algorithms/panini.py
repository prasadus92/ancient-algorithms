"""Vowel sandhi from Panini's Ashtadhyayi as an ordered rewrite system.

Panini's Ashtadhyayi (date debated; usually placed c. 5th to 4th century BCE) states
Sanskrit grammar as about 4,000 short rules (sutras). This module models a handful
of them: the vowel-junction rules of 6.1, the shorthand (pratyahara) built from the
14 Shiva Sutras, and the 2 principles that decide which rule applies.

Sutra text and numbers follow the GRETIL e-texts of the Ashtadhyayi (the mula text
taken from the Kasikavrtti, and the version input under W. P. Lehmann). The Shiva
Sutras, the 41 pratyaharas they serve and the reading of the ambiguous ``an`` follow
the Kasikavrtti (c. 7th century). Places of articulation follow the gloss in
Varadaraja's Laghusiddhantakaumudi, which also supplies the test examples.

1. Expand a pratyahara (1.1.71): a sound plus a marker letter names every sound
   from that sound up to the marker, leaving out the markers (1.3.3, 1.3.9).
2. Widen it to homogeneous sounds (1.1.69): ``ik`` also covers long i, u and r.
3. At a junction of 2 sounds, collect every rule whose condition holds.
4. If more than 1 rule applies, the later one wins (1.4.2 vipratishedhe param karyam).
5. Pick the substitute closest in place of articulation (1.1.50); a vowel of the
   a, i, u class that replaces r is followed by r (1.1.51).
6. Repeat while a rule applies. Then run the last 3 quarter-chapters (from 8.2.1)
   strictly in order; their output is invisible to every earlier rule (8.2.1).

The model covers 6.1.77, 6.1.78, 6.1.87, 6.1.88, 6.1.101, 6.1.109 and 8.3.19. It
leaves out the exceptions that protect some vowels from sandhi (pragrhya, 1.1.11
onward), accent, and optional consonant doubling (8.4.47).

An unordered rewrite system over the same rules, which applies whatever matches
until nothing does, is at the end of the module for comparison.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Callable
from dataclasses import dataclass

__all__ = [
    "SHIVA_SUTRAS",
    "PLACES",
    "GUNA",
    "VRDDHI",
    "Rule",
    "SandhiStep",
    "RULES",
    "TRIPADI",
    "pratyahara",
    "savarnas",
    "antaratama",
    "derive",
    "join",
    "join_words",
    "rewrite_to_fixpoint",
]

SHIVA_SUTRAS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("a", "i", "u"), "ṇ"),
    (("ṛ", "ḷ"), "k"),
    (("e", "o"), "ṅ"),
    (("ai", "au"), "c"),
    (("h", "y", "v", "r"), "ṭ"),
    (("l",), "ṇ"),
    (("ñ", "m", "ṅ", "ṇ", "n"), "m"),
    (("jh", "bh"), "ñ"),
    (("gh", "ḍh", "dh"), "ṣ"),
    (("j", "b", "g", "ḍ", "d"), "ś"),
    (("kh", "ph", "ch", "ṭh", "th", "c", "ṭ", "t"), "v"),
    (("k", "p"), "y"),
    (("ś", "ṣ", "s"), "r"),
    (("h",), "l"),
)
"""The 14 Shiva Sutras: each sutra's sounds, then its marker. The a of ha, ya is for saying only."""

PLACES: dict[str, frozenset[str]] = {
    sound: frozenset(places.split())
    for sound, places in {
        "a": "throat", "ā": "throat",
        "i": "palate", "ī": "palate", "y": "palate",
        "u": "lips", "ū": "lips",
        "ṛ": "roof", "ṝ": "roof", "r": "roof",
        "ḷ": "teeth", "l": "teeth",
        "e": "throat palate", "ai": "throat palate",
        "o": "throat lips", "au": "throat lips",
        "v": "teeth lips",
    }.items()
}  # fmt: skip
"""Place of articulation (sthana) of each sound the vowel rules use (Laghusiddhantakaumudi)."""

LONG: dict[str, str] = {"a": "ā", "i": "ī", "u": "ū", "ṛ": "ṝ"}
"""The long vowel homogeneous with each short one. The l-vowel has none (1.1.9 in the LSK)."""

SIMPLE: tuple[str, ...] = ("a", "i", "u", "ṛ", "ḷ")
"""The simple short vowels, the members of ``ak``."""

VOWELS: tuple[str, ...] = ("ai", "au", "a", "ā", "i", "ī", "u", "ū", "ṛ", "ṝ", "ḷ", "e", "o")
"""Every vowel in IAST, diphthongs first so that the longest match is found."""

AVAGRAHA = "'"
"""The sign printed for an a absorbed by the vowel before it, as in hare'va."""

Junction = tuple[str, str]
"""The 2 sides of a junction: the end of the left word and the start of the right one."""


def pratyahara(name: str, *, marker_sutra: int | None = None) -> tuple[str, ...]:
    """The sounds a pratyahara names: its first sound up to its marker, markers left out (1.1.71).

    ``marker_sutra`` picks which Shiva Sutra's marker to stop at, for the marker n that
    ends both sutra 1 and sutra 6. By default ``an`` stops at sutra 1 and every other
    name at sutra 6, the reading the Kasikavrtti gives (``an`` in 1.1.69 is the exception).
    """
    name = unicodedata.normalize("NFC", name)
    first, marker = name[:-1], name[-1:]
    if first.endswith("a") and first[:-1] and first[:-1] not in VOWELS:
        first = first[:-1]  # the a in hal, yan, jhal is said for pronunciation only
    stops = [i for i, (_, m) in enumerate(SHIVA_SUTRAS, start=1) if m == marker]
    if not first or not stops:
        raise ValueError(f"{name!r} is not a sound followed by a marker letter")
    stop = marker_sutra or (stops[0] if first == "a" else stops[-1])
    if stop not in stops:
        raise ValueError(f"Shiva Sutra {stop} does not end in {marker!r}")
    sounds = [sound for sounds, _ in SHIVA_SUTRAS[:stop] for sound in sounds]
    if first not in sounds:
        raise ValueError(f"{first!r} does not occur before the marker of Shiva Sutra {stop}")
    return tuple(dict.fromkeys(sounds[sounds.index(first) :]))


def savarnas(sounds: tuple[str, ...]) -> frozenset[str]:
    """The sounds plus their homogeneous long vowels (1.1.69 anudit savarnasya capratyayah)."""
    return frozenset(sounds) | {LONG[s] for s in sounds if s in LONG}


def antaratama(target: frozenset[str], substitutes: tuple[str, ...]) -> str:
    """The substitute closest in place to ``target`` (1.1.50 sthane 'ntaratamah).

    Closest means the most places shared, then the fewest extra places. Nagesa's
    Paribhashendushekhara ranks likeness of place above other likeness.
    """
    return max(substitutes, key=lambda s: (len(PLACES[s] & target), -len(PLACES[s] - target)))


GUNA: tuple[str, ...] = ("a", *pratyahara("eṅ"))
"""The guna vowels a, e, o (1.1.2 ad eng gunah)."""

VRDDHI: tuple[str, ...] = ("ā", *pratyahara("aic"))
"""The vrddhi vowels ā, ai, au (1.1.1 vrddhir ad aic)."""

AC = savarnas(pratyahara("ac"))
"""Every vowel, short and long."""

IK = savarnas(pratyahara("ik"))
"""i, u, r-vowel, l-vowel and their long forms."""

AK = savarnas(pratyahara("ak"))
"""a, i, u, r-vowel, l-vowel and their long forms."""

EC = pratyahara("ec")
"""The diphthongs e, o, ai, au."""

EN = pratyahara("eṅ")
"""e and o."""

AS = savarnas(pratyahara("aś"))
"""Vowels, semivowels, nasals and voiced consonants: the context of 8.3.19."""

A_CLASS = savarnas(("a",))
"""Short and long a."""

RAPARA = savarnas(pratyahara("aṇ", marker_sutra=1))
"""a, i, u and their long forms: they take r after them when they replace r-vowel (1.1.51)."""


@dataclass(frozen=True)
class Rule:
    """One sutra: its number, its text, when it applies, and what it does to a junction."""

    number: tuple[int, int, int]
    text: str
    applies: Callable[[Junction, bool], bool]
    apply: Callable[[Junction], Junction]

    @property
    def label(self) -> str:
        """The sutra number as written, for example ``6.1.77``."""
        return ".".join(map(str, self.number))


@dataclass
class SandhiStep:
    """One rewrite: which rules applied, which one won, and the form after it."""

    applicable: list[str]
    chosen: str
    form: str


def derive(
    left: str, right: str, *, word_boundary: bool = True, sakalya: bool = False
) -> list[SandhiStep]:
    """Every rewrite at the junction of ``left`` and ``right``, in order.

    ``word_boundary`` is False for a stem and an ending inside 1 word. ``sakalya``
    takes the optional deletion of 8.3.19, which the sutra credits to Sakalya.
    """
    state = (_nfc(left), _nfc(right))
    steps: list[SandhiStep] = []
    state = _rewrite(state, RULES, word_boundary, steps)
    tripadi = TRIPADI if sakalya else ()
    for rule in tripadi:  # 8.2.1: in order, once each, never fed back to the rules above
        if rule.applies(state, word_boundary):
            state = rule.apply(state)
            steps.append(SandhiStep([rule.label], rule.label, _render(state)))
    return steps


def join(left: str, right: str, *, word_boundary: bool = True, sakalya: bool = False) -> str:
    """The form of ``left`` and ``right`` joined by the rules in ``RULES`` and ``TRIPADI``."""
    steps = derive(left, right, word_boundary=word_boundary, sakalya=sakalya)
    return steps[-1].form if steps else _render((_nfc(left), _nfc(right)))


def join_words(words: list[str], *, sakalya: bool = False) -> str:
    """A sentence in continuous speech (samhita): each word joined to the next, left to right."""
    if not words:
        raise ValueError("need at least 1 word")
    sentence = _nfc(words[0])
    for word in words[1:]:
        sentence = join(sentence, word, sakalya=sakalya)
    return sentence


def _rewrite(
    state: Junction, rules: tuple[Rule, ...], word_boundary: bool, steps: list[SandhiStep]
) -> Junction:
    """Apply rules until none applies, choosing the later sutra when several do (1.4.2)."""
    while candidates := [rule for rule in rules if rule.applies(state, word_boundary)]:
        winner = max(candidates, key=lambda rule: rule.number)
        state = winner.apply(state)
        steps.append(SandhiStep([r.label for r in candidates], winner.label, _render(state)))
    return state


def _nfc(text: str) -> str:
    """``text`` in Unicode NFC, so that each IAST letter is 1 code point."""
    return unicodedata.normalize("NFC", text)


def _last_vowel(word: str) -> str:
    """The vowel ``word`` ends in, or an empty string."""
    return next((v for v in VOWELS if word.endswith(v)), "")


def _first_vowel(word: str) -> str:
    """The vowel ``word`` starts with, or an empty string."""
    return next((v for v in VOWELS if word.startswith(v)), "")


def _vowels_meet(state: Junction) -> tuple[str, str]:
    """The 2 vowels at the junction, or empty strings when the junction is closed."""
    left, right = state
    return (_last_vowel(left), _first_vowel(right)) if right else ("", "")


def _render(state: Junction) -> str:
    """The junction as written: a space only where 2 vowels stay apart."""
    left, right = state
    gap = " " if _last_vowel(left) and _first_vowel(right) else ""
    return left + gap + right


def _replace_left(state: Junction, old: str, new: str) -> Junction:
    """Replace the last ``old`` sound of the left word with ``new``."""
    left, right = state
    return left[: len(left) - len(old)] + new, right


def _single_replacement(state: Junction, new: str) -> Junction:
    """Replace the 2 vowels at the junction with 1 sound (6.1.84 ekah purvaparayoh)."""
    first, second = _vowels_meet(state)
    left, right = state
    return left[: len(left) - len(first)] + new + right[len(second) :], ""


def _with_r(substitute: str, replaced: str) -> str:
    """Add r (or l) after an a, i or u that replaces r-vowel (or l-vowel): 1.1.51 ur an raparah."""
    if substitute in RAPARA and replaced in {"ṛ", "ṝ"}:
        return substitute + "r"
    if substitute in RAPARA and replaced == "ḷ":
        return substitute + "l"
    return substitute


def _places(*sounds: str) -> frozenset[str]:
    """Every place of articulation the sounds use, together."""
    return frozenset().union(*(PLACES[s] for s in sounds))


def _iko_yan_aci(state: Junction) -> Junction:
    """6.1.77: i, u, r, l vowels become y, v, r, l before a vowel."""
    first, _ = _vowels_meet(state)
    return _replace_left(state, first, antaratama(PLACES[first], pratyahara("yaṇ")))


def _eco_yavayavah(state: Junction) -> Junction:
    """6.1.78: e, o, ai, au become ay, av, āy, āv before a vowel, respectively (1.3.10)."""
    first, _ = _vowels_meet(state)
    return _replace_left(state, first, dict(zip(EC, ("ay", "av", "āy", "āv"), strict=True))[first])


def _ad_gunah(state: Junction) -> Junction:
    """6.1.87: a or ā and a following vowel become 1 guna vowel."""
    first, second = _vowels_meet(state)
    return _single_replacement(state, _with_r(antaratama(_places(first, second), GUNA), second))


def _vrddhir_eci(state: Junction) -> Junction:
    """6.1.88: a or ā and a following diphthong become 1 vrddhi vowel."""
    first, second = _vowels_meet(state)
    return _single_replacement(state, antaratama(_places(first, second), VRDDHI))


def _akah_savarne_dirghah(state: Junction) -> Junction:
    """6.1.101: 2 homogeneous simple vowels become 1 long vowel."""
    first, _ = _vowels_meet(state)
    short = _short_of(first)
    if short not in LONG:
        raise ValueError(f"no long vowel is homogeneous with {first!r}")
    return _single_replacement(state, LONG[short])


def _enah_padantad_ati(state: Junction) -> Junction:
    """6.1.109: word-final e or o absorbs a following short a."""
    left, right = state
    return left, AVAGRAHA + right[1:]


def _lopah_sakalyasya(state: Junction) -> Junction:
    """8.3.19: word-final y or v after a or ā drops before a voiced sound, in Sakalya's view."""
    left, right = state
    return left[:-1], right


def _short_of(vowel: str) -> str | None:
    """The short simple vowel that ``vowel`` is, or is the long form of; None for diphthongs."""
    if vowel in SIMPLE:
        return vowel
    return next((short for short, long in LONG.items() if long == vowel), None)


def _homogeneous(first: str, second: str) -> bool:
    """Whether 2 simple vowels are homogeneous (1.1.9): the same vowel, short or long."""
    short = _short_of(first)
    return short is not None and _short_of(second) == short


RULES: tuple[Rule, ...] = (
    Rule(
        (6, 1, 77),
        "iko yaṇ aci",
        lambda s, _: _vowels_meet(s)[0] in IK and _vowels_meet(s)[1] in AC,
        _iko_yan_aci,
    ),
    Rule(
        (6, 1, 78),
        "eco 'yavāyāvaḥ",
        lambda s, _: _vowels_meet(s)[0] in EC and _vowels_meet(s)[1] in AC,
        _eco_yavayavah,
    ),
    Rule(
        (6, 1, 87),
        "ād guṇaḥ",
        lambda s, _: _vowels_meet(s)[0] in A_CLASS and _vowels_meet(s)[1] in AC,
        _ad_gunah,
    ),
    Rule(
        (6, 1, 88),
        "vṛddhir eci",
        lambda s, _: _vowels_meet(s)[0] in A_CLASS and _vowels_meet(s)[1] in EC,
        _vrddhir_eci,
    ),
    Rule(
        (6, 1, 101),
        "akaḥ savarṇe dīrghaḥ",
        lambda s, _: _homogeneous(*_vowels_meet(s)),
        _akah_savarne_dirghah,
    ),
    Rule(
        (6, 1, 109),
        "eṅaḥ padāntād ati",
        lambda s, word_boundary: (
            word_boundary and _vowels_meet(s)[0] in EN and _vowels_meet(s)[1] == "a"
        ),
        _enah_padantad_ati,
    ),
)
"""The vowel-junction rules of 6.1 in this model, in the order of the Ashtadhyayi."""

TRIPADI: tuple[Rule, ...] = (
    Rule(
        (8, 3, 19),
        "lopaḥ śākalyasya",
        lambda s, word_boundary: (
            word_boundary
            and s[1] != ""
            and s[0][-1:] in {"y", "v"}
            and s[0][-2:-1] in A_CLASS
            and (_first_vowel(s[1]) or s[1][:1]) in AS
        ),
        _lopah_sakalyasya,
    ),
)
"""Rules from the last 3 quarter-chapters (8.2 to 8.4), applied after everything else.

Its 1 rule here, 8.3.19, is optional, so ``derive`` runs it only when ``sakalya`` is set.
"""


def rewrite_to_fixpoint(left: str, right: str, *, word_boundary: bool = True) -> str:
    """An unordered rewrite system: apply any matching rule, 8.3.19 included, until none matches.

    This drops 8.2.1. Without it, the output of 8.3.19 feeds 6.1.87 again.
    """
    steps: list[SandhiStep] = []
    state = _rewrite((_nfc(left), _nfc(right)), RULES + TRIPADI, word_boundary, steps)
    return _render(state)
