"""Vowel sandhi from Panini's Ashtadhyayi as an ordered rewrite system.

Panini's Ashtadhyayi states Sanskrit grammar as about 4,000 short rules (sutras).
Its date is debated: older proposals range from 700 BCE to 100 CE, and Agrawala
(1969) argued for 480 to 410 BCE (P. Singh, Historia Mathematica 12, 1985). This
module models a few of its rules: the vowel-junction rules of 6.1, the shorthand
(pratyahara) built from the 14 Shiva Sutras, and the principles that decide which
rule applies when several could.

Sutra text and numbers follow the GRETIL e-texts of the Ashtadhyayi (the mula text
taken from the Kasikavrtti, and the version input under W. P. Lehmann). The Shiva
Sutras, the 41 pratyaharas they serve, the prefix list, the reading of the
ambiguous ``an`` and the exceptions named for 6.1.91, 6.1.94 and 6.1.109 follow the
Kasikavrtti of Jayaditya and Vamana. Places of articulation and most test examples
follow Varadaraja's Laghusiddhantakaumudi.

1. Expand a pratyahara (1.1.71): a sound plus a marker letter names every sound
   from that sound up to the marker, leaving out the markers (1.3.3, 1.3.9).
2. Widen it to homogeneous sounds (1.1.69): ``ik`` also covers long i, u and r.
3. At a junction of 2 vowels, collect every rule whose condition holds.
4. Drop each rule that another applicable rule is an exception to (apavada: the
   special rule blocks the general one). If more than 1 rule is left, the later
   sutra wins (1.4.2 vipratishedhe param karyam). Every conflict in this model is
   settled at the first step.
5. Pick the substitute closest in place of articulation (1.1.50); a vowel of the
   a, i, u class that replaces r is followed by r (1.1.51).
6. Repeat while a rule applies. Then run the last 3 quarter-chapters (from 8.2.1)
   strictly in order; their output is invisible to every earlier rule (8.2.1).

The model covers 6.1.77, 6.1.78, 6.1.87, 6.1.88, 6.1.89, 6.1.91, 6.1.94, 6.1.101,
6.1.109 and 8.3.19, at junctions where 2 vowels meet. It leaves out the exceptions
that protect some vowels from sandhi (pragrhya, 1.1.11 onward), accent, consonant
junctions and optional consonant doubling (8.4.47).

For comparison, ``rewrite_to_fixpoint`` at the end runs the same rules with 8.2.1
removed.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Callable, Collection
from dataclasses import dataclass


def _nfc(text: str) -> str:
    """Unicode NFC form, so precomposed and combining diacritics compare equal."""
    return unicodedata.normalize("NFC", text)


__all__ = [
    "SHIVA_SUTRAS",
    "PLACES",
    "LONG",
    "GUNA",
    "VRDDHI",
    "Rule",
    "SandhiStep",
    "pratyahara",
    "savarnas",
    "antaratama",
    "resolve",
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
        "ṛ": "retroflex", "ṝ": "retroflex", "r": "retroflex",
        "ḷ": "teeth", "l": "teeth",
        "e": "throat palate", "ai": "throat palate",
        "o": "throat lips", "au": "throat lips",
        "v": "teeth lips",
    }.items()
}  # fmt: skip
"""Place of articulation (sthana) of each sound the vowel rules use (Laghusiddhantakaumudi)."""

LONG: dict[str, str] = {"a": "ā", "i": "ī", "u": "ū", "ṛ": "ṝ"}
"""The long vowel of each homogeneous class (1.1.9). The l-vowel has none (LSK on 1.1.8)."""

GUNA: tuple[str, ...] = ("a", "e", "o")
"""The guna vowels (1.1.2 ad eng gunah: short a, and the pratyahara en)."""

VRDDHI: tuple[str, ...] = ("ā", "ai", "au")
"""The vrddhi vowels (1.1.1 vrddhir ad aic: long a, and the pratyahara aic)."""

_SAVARNA_CLASS: dict[str, str] = {
    "a": "a", "ā": "a",
    "i": "i", "ī": "i",
    "u": "u", "ū": "u",
    "ṛ": "ṛ", "ṝ": "ṛ", "ḷ": "ṛ",
}  # fmt: skip
"""Each simple vowel's homogeneous class (1.1.9).

The varttika rlvarnayor mithah savarnyam vacyam, quoted in the LSK under 1.1.9, puts
the r- and l-vowels in 1 class, so the long form of the l-vowel is the long r-vowel.
"""

_VOWELS: tuple[str, ...] = ("ai", "au", "a", "ā", "i", "ī", "u", "ū", "ṛ", "ṝ", "ḷ", "e", "o")
"""Every vowel in IAST, diphthongs first so that the longest match is found."""

_R_AFTER: dict[str, str] = {"ṛ": "r", "ṝ": "r", "ḷ": "l"}
"""The consonant that follows an a, i or u put in place of an r- or l-vowel (1.1.51)."""

_AVAGRAHA = "'"
"""The sign printed for an a absorbed by the vowel before it, as in hare'va."""

_UPASARGAS: tuple[str, ...] = (
    "pra", "parā", "apa", "sam", "anu", "ava", "nis", "nir", "dus", "dur", "vi",
    "ā", "ni", "adhi", "api", "ati", "su", "ut", "abhi", "prati", "pari", "upa",
)  # fmt: skip
"""The 22 verbal prefixes (upasarga) from pra onward, as the Kasikavrtti lists them under 1.4.58."""

_ETI_EDHATI = frozenset({"i", "edh"})
"""The roots i (go) and edh (grow), whose forms take vrddhi after a by 6.1.89."""

_Junction = tuple[str, str]


@dataclass(frozen=True)
class Rule:
    """One sutra: its number, its text, when it applies, what it does, and what it overrides.

    ``applies`` takes the junction, whether it is a word boundary, and the verb root
    when the left word is a prefix. ``exception_to`` lists the general rules this one
    blocks where both apply (apavada).
    """

    number: tuple[int, int, int]
    text: str
    applies: Callable[[_Junction, bool, str | None], bool]
    apply: Callable[[_Junction], _Junction]
    exception_to: tuple[tuple[int, int, int], ...] = ()

    @property
    def label(self) -> str:
        """The sutra number as written, for example ``6.1.77``."""
        return ".".join(map(str, self.number))


@dataclass
class SandhiStep:
    """One rewrite: the rules that applied, the one chosen, why, and the form after it.

    ``reason`` is ``"only rule"``, ``"exception"`` or ``"later rule (1.4.2)"``.
    """

    applicable: list[str]
    chosen: str
    reason: str
    form: str


def pratyahara(name: str, *, marker_sutra: int | None = None) -> tuple[str, ...]:
    """The sounds a pratyahara names: its first sound up to its marker, markers left out (1.1.71).

    ``marker_sutra`` picks which Shiva Sutra's marker to stop at, for the marker n that
    ends both sutra 1 and sutra 6. By default ``an`` stops at sutra 1 and every other
    name at sutra 6, the reading the Kasikavrtti gives (``an`` in 1.1.69 is the exception).
    """
    name = _nfc(name)
    first, marker = name[:-1], name[-1:]
    if first.endswith("a") and first[:-1] and first[:-1] not in _VOWELS:
        first = first[:-1]  # the a in hal, yan, jhal is said for pronunciation only
    stops = [i for i, (_, m) in enumerate(SHIVA_SUTRAS, start=1) if m == marker]
    if not first or not stops:
        raise ValueError(f"{name!r} is not a sound followed by a marker letter")
    if marker_sutra is None:
        marker_sutra = stops[0] if first == "a" else stops[-1]
    if marker_sutra not in stops:
        raise ValueError(f"Shiva Sutra {marker_sutra} does not end in {marker!r}")
    sounds = [sound for sounds, _ in SHIVA_SUTRAS[:marker_sutra] for sound in sounds]
    if first not in sounds:
        raise ValueError(
            f"{first!r} does not occur before the marker of Shiva Sutra {marker_sutra}"
        )
    return tuple(dict.fromkeys(sounds[sounds.index(first) :]))


def savarnas(sounds: tuple[str, ...]) -> frozenset[str]:
    """The sounds plus every vowel homogeneous with them (1.1.69 anudit savarnasya capratyayah)."""
    classes = {_SAVARNA_CLASS[s] for s in sounds if s in _SAVARNA_CLASS}
    return frozenset(sounds) | {v for v, c in _SAVARNA_CLASS.items() if c in classes}


def antaratama(target: frozenset[str], substitutes: tuple[str, ...]) -> str:
    """The substitute closest in place to ``target`` (1.1.50 sthane 'ntaratamah).

    Closest means the most places shared, then the fewest extra places. Nagesa's
    Paribhashendushekhara ranks likeness of place above other likeness.
    """
    return max(substitutes, key=lambda s: (len(PLACES[s] & target), -len(PLACES[s] - target)))


def resolve(candidates: list[Rule]) -> tuple[Rule, str]:
    """The rule that applies among ``candidates``, and why.

    Exceptions block their general rules; among what is left, the later sutra wins (1.4.2).
    """
    if not candidates:
        raise ValueError("need at least 1 applicable rule")
    if len(candidates) == 1:
        return candidates[0], "only rule"
    blocked = {number for rule in candidates for number in rule.exception_to}
    remaining = [rule for rule in candidates if rule.number not in blocked]
    if len(remaining) == 1:
        return remaining[0], "exception"
    return max(remaining, key=lambda rule: rule.number), "later rule (1.4.2)"


def derive(
    left: str,
    right: str,
    *,
    word_boundary: bool = True,
    sakalya: bool = False,
    verb_root: str | None = None,
) -> list[SandhiStep]:
    """Every rewrite at the junction of ``left`` and ``right``, in order.

    ``word_boundary`` is False for a stem and an ending inside 1 word. ``sakalya``
    takes the optional deletion of 8.3.19, which the sutra credits to Sakalya.
    ``verb_root`` names the root when ``right`` is a verb form; 6.1.91 and 6.1.94
    also need ``left`` to be a prefix ending in a or ā.
    Raises ``ValueError`` unless 2 vowels meet at the junction, and for an empty
    ``verb_root``.
    """
    state = _vowel_junction(left, right)
    if verb_root == "":
        raise ValueError("verb_root must name a root, got an empty string")
    steps: list[SandhiStep] = []
    state = _rewrite(state, _RULES, word_boundary, verb_root, steps)
    if sakalya:  # 8.3.19 is optional, and the only tripadi rule in this model
        for rule in _TRIPADI:  # 8.2.1: in order, once each, never fed back to the rules above
            if rule.applies(state, word_boundary, verb_root):
                state = rule.apply(state)
                steps.append(SandhiStep([rule.label], rule.label, "only rule", _render(state)))
    return steps


def join(
    left: str,
    right: str,
    *,
    word_boundary: bool = True,
    sakalya: bool = False,
    verb_root: str | None = None,
) -> str:
    """The form of ``left`` and ``right`` joined at a vowel junction, as ``derive`` builds it."""
    steps = derive(left, right, word_boundary=word_boundary, sakalya=sakalya, verb_root=verb_root)
    return steps[-1].form


def join_words(words: list[str], *, sakalya: bool = False) -> str:
    """A sentence in continuous speech (samhita): each word joined to the next, left to right.

    Every junction must be 2 vowels; ``derive`` raises ``ValueError`` at any other.
    """
    if not words:
        raise ValueError("need at least 1 word")
    sentence = _nfc(words[0])
    for word in words[1:]:
        sentence = join(sentence, word, sakalya=sakalya)
    return sentence


_AC = savarnas(pratyahara("ac"))
"""Every vowel, short and long."""

_IK = savarnas(pratyahara("ik"))
"""i, u, r-vowel, l-vowel and their long forms."""

_AK = savarnas(pratyahara("ak"))
"""a, i, u, r-vowel, l-vowel and their long forms."""

_EC = pratyahara("ec")
"""The diphthongs e, o, ai, au."""

_EN = pratyahara("eṅ")
"""e and o."""

_A_CLASS = savarnas(("a",))
"""Short and long a."""

_RAPARA = savarnas(pratyahara("aṇ", marker_sutra=1))
"""a, i, u and their long forms: they take r after them when they replace r-vowel (1.1.51)."""

_SHORT_R = frozenset({"ṛ"})
"""Short r-vowel only: 6.1.91 writes ṛti, and by 1.1.70 a t-marked vowel names its own length."""

_RULES: tuple[Rule, ...] = (
    Rule(
        (6, 1, 77),
        "iko yaṇ aci",
        lambda s, _, __: _meet(s, _IK, _AC),
        lambda s: _iko_yan_aci(s),
    ),
    Rule(
        (6, 1, 78),
        "eco 'yavāyāvaḥ",
        lambda s, _, __: _meet(s, _EC, _AC),
        lambda s: _eco_yavayavah(s),
    ),
    Rule(
        (6, 1, 87),
        "ād guṇaḥ",
        lambda s, _, __: _meet(s, _A_CLASS, _AC),
        lambda s: _ad_gunah(s),
    ),
    Rule(
        (6, 1, 88),
        "vṛddhir eci",
        lambda s, _, __: _meet(s, _A_CLASS, _EC),
        lambda s: _vrddhi(s),
        exception_to=((6, 1, 87),),  # Laghusiddhantakaumudi: gunapavadah
    ),
    Rule(
        (6, 1, 89),
        "ety-edhaty-ūṭhsu",
        lambda s, _, root: root in _ETI_EDHATI and _meet(s, _A_CLASS, _EC),
        lambda s: _vrddhi(s),
        exception_to=((6, 1, 87), (6, 1, 88), (6, 1, 94)),  # Kiparsky, examples (29) and (30)
    ),
    Rule(
        (6, 1, 91),
        "upasargād ṛti dhātau",
        lambda s, _, root: _after_prefix(s, root) and _meet(s, _A_CLASS, _SHORT_R),
        lambda s: _vrddhi(s),
        exception_to=((6, 1, 87),),  # Kasikavrtti: adgunapavadah
    ),
    Rule(
        (6, 1, 94),
        "eṅi pararūpam",
        lambda s, _, root: _after_prefix(s, root) and _meet(s, _A_CLASS, _EN),
        lambda s: _eni_pararupam(s),
        exception_to=((6, 1, 87), (6, 1, 88)),  # Kasikavrtti: vrddhir eci ity asya apavadah
    ),
    Rule(
        (6, 1, 101),
        "akaḥ savarṇe dīrghaḥ",
        lambda s, _, __: _homogeneous(*_vowels_meet(s)),
        lambda s: _akah_savarne_dirghah(s),
        exception_to=((6, 1, 77), (6, 1, 87)),  # Kiparsky, collective blocking of (25) and (26)
    ),
    Rule(
        (6, 1, 109),
        "eṅaḥ padāntād ati",
        lambda s, word_boundary, _: word_boundary and _meet(s, _EN, frozenset({"a"})),
        lambda s: _enah_padantad_ati(s),
        exception_to=((6, 1, 78),),  # Kasikavrtti: ayavadesayor ayam apavadah
    ),
)
"""The vowel-junction rules of 6.1 in this model, in the order of the Ashtadhyayi."""

_TRIPADI: tuple[Rule, ...] = (
    Rule(
        (8, 3, 19),
        "lopaḥ śākalyasya",
        # The right side starts with a vowel here, so the sutra's "before as" always holds.
        lambda s, word_boundary, _: (
            word_boundary and s[1] != "" and s[0][-1:] in {"y", "v"} and s[0][-2:-1] in _A_CLASS
        ),
        lambda s: _lopah_sakalyasya(s),
    ),
)
"""Rules from the last 3 quarter-chapters (8.2 to 8.4), applied after everything else."""


def _vowel_junction(left: str, right: str) -> _Junction:
    """The junction in NFC; ``ValueError`` unless ``left`` ends and ``right`` starts in a vowel."""
    state = (_nfc(left), _nfc(right))
    if not all(_vowels_meet(state)):
        raise ValueError(f"the model covers vowel junctions only, got {left!r} + {right!r}")
    return state


def _rewrite(
    state: _Junction,
    rules: tuple[Rule, ...],
    word_boundary: bool,
    verb_root: str | None,
    steps: list[SandhiStep],
) -> _Junction:
    """Apply rules until none applies, choosing among several by ``resolve``."""
    while candidates := [r for r in rules if r.applies(state, word_boundary, verb_root)]:
        winner, reason = resolve(candidates)
        state = winner.apply(state)
        steps.append(
            SandhiStep([r.label for r in candidates], winner.label, reason, _render(state))
        )
    return state


def _last_vowel(word: str) -> str:
    """The vowel ``word`` ends in, or an empty string."""
    return next((v for v in _VOWELS if word.endswith(v)), "")


def _first_vowel(word: str) -> str:
    """The vowel ``word`` starts with, or an empty string."""
    return next((v for v in _VOWELS if word.startswith(v)), "")


def _vowels_meet(state: _Junction) -> tuple[str, str]:
    """The 2 vowels at the junction, or empty strings where there is none."""
    left, right = state
    return (_last_vowel(left), _first_vowel(right)) if right else ("", "")


def _render(state: _Junction) -> str:
    """The junction as written: a space only where 2 vowels stay apart."""
    left, right = state
    gap = " " if _last_vowel(left) and _first_vowel(right) else ""
    return left + gap + right


def _replace_left(state: _Junction, old: str, new: str) -> _Junction:
    """Replace the last ``old`` sound of the left word with ``new``."""
    left, right = state
    return left[: len(left) - len(old)] + new, right


def _single_replacement(state: _Junction, new: str) -> _Junction:
    """Replace the 2 vowels at the junction with 1 sound (6.1.84 ekah purvaparayoh)."""
    first, second = _vowels_meet(state)
    left, right = state
    return left[: len(left) - len(first)] + new + right[len(second) :], ""


def _with_r(substitute: str, replaced: str) -> str:
    """Add r (or l) after an a, i or u that replaces r-vowel (or l-vowel): 1.1.51 ur an raparah."""
    return substitute + _R_AFTER.get(replaced, "") if substitute in _RAPARA else substitute


def _places(*sounds: str) -> frozenset[str]:
    """Every place of articulation the sounds use, together."""
    return frozenset().union(*(PLACES[s] for s in sounds))


def _homogeneous(first: str, second: str) -> bool:
    """Whether 2 simple vowels are homogeneous (1.1.9)."""
    return first in _SAVARNA_CLASS and _SAVARNA_CLASS[first] == _SAVARNA_CLASS.get(second)


def _iko_yan_aci(state: _Junction) -> _Junction:
    """6.1.77: i, u, r, l vowels become y, v, r, l before a vowel."""
    first, _ = _vowels_meet(state)
    return _replace_left(state, first, antaratama(PLACES[first], pratyahara("yaṇ")))


def _eco_yavayavah(state: _Junction) -> _Junction:
    """6.1.78: e, o, ai, au become ay, av, āy, āv before a vowel, respectively (1.3.10)."""
    first, _ = _vowels_meet(state)
    return _replace_left(state, first, dict(zip(_EC, ("ay", "av", "āy", "āv"), strict=True))[first])


def _ad_gunah(state: _Junction) -> _Junction:
    """6.1.87: a or ā and a following vowel become 1 guna vowel."""
    first, second = _vowels_meet(state)
    return _single_replacement(state, _with_r(antaratama(_places(first, second), GUNA), second))


def _vrddhi(state: _Junction) -> _Junction:
    """6.1.88, 6.1.89 and 6.1.91: a or ā and the next vowel become 1 vrddhi vowel."""
    first, second = _vowels_meet(state)
    return _single_replacement(state, _with_r(antaratama(_places(first, second), VRDDHI), second))


def _eni_pararupam(state: _Junction) -> _Junction:
    """6.1.94: a prefix-final a or ā and a following e or o become the second vowel."""
    _, second = _vowels_meet(state)
    return _single_replacement(state, second)


def _akah_savarne_dirghah(state: _Junction) -> _Junction:
    """6.1.101: 2 homogeneous simple vowels become 1 long vowel."""
    first, _ = _vowels_meet(state)
    return _single_replacement(state, LONG[_SAVARNA_CLASS[first]])


def _enah_padantad_ati(state: _Junction) -> _Junction:
    """6.1.109: word-final e or o absorbs a following short a."""
    left, right = state
    return left, _AVAGRAHA + right[1:]


def _lopah_sakalyasya(state: _Junction) -> _Junction:
    """8.3.19: word-final y or v after a or ā drops before a voiced sound, in Sakalya's view."""
    left, right = state
    return left[:-1], right


def _meet(state: _Junction, before: Collection[str], after: Collection[str]) -> bool:
    """Whether the left vowel is in ``before`` and the right vowel in ``after``."""
    first, second = _vowels_meet(state)
    return first in before and second in after


def _after_prefix(state: _Junction, root: str | None) -> bool:
    """Whether the left word is a verbal prefix ending in a or ā and a verb form follows."""
    return root is not None and state[0] in _UPASARGAS and _last_vowel(state[0]) in _A_CLASS


def rewrite_to_fixpoint(left: str, right: str, *, word_boundary: bool = True) -> str:
    """The same rules with 8.2.1 removed: 8.3.19 sits in the loop with the rest, always taken.

    Without 8.2.1 the output of 8.3.19 feeds 6.1.87 again. Raises ``ValueError``, as
    ``derive`` does, unless 2 vowels meet at the junction.
    """
    steps: list[SandhiStep] = []
    state = _rewrite(_vowel_junction(left, right), _RULES + _TRIPADI, word_boundary, None, steps)
    return _render(state)
