"""The katapayadi notation: whole numbers written as Sanskrit syllables.

Source: Sankaravarman, Sadratnamala (1819), chapter 3, verse 3, edited by K. V.
Sarma, Indian Journal of History of Science 36 (2001). The verse is the fullest
statement of the rule that S. R. Sarma (Revue d'histoire des mathematiques 18,
2012, pp. 37 to 66) found in the texts:

    nañāv acaś ca śūnyāni saṃkhyāḥ kaṭapayādayaḥ |
    miśre tūpāntyahal saṃkhyā na ca cintyo hal asvaraḥ ||

"Ña, na and the vowels are zeros. The numbers [1 to 9] are the consonants
starting with ka, ta, pa and ya. In a cluster, the last consonant is the
number. A consonant without a vowel is not counted."

The steps:

1. Split the text into syllables. A syllable is a vowel with the consonants
   before it. In IAST a space does not end a cluster, since a word-final
   consonant joins the next word's vowel when recited; in Devanagari the virama
   marks a consonant with no vowel.
2. Give each syllable the value of its last consonant from the table below, or
   0 when it is a vowel alone. Anusvara, visarga and a consonant with no vowel
   after it count for nothing.
3. Read the digits from right to left: the first syllable is the units place.
   The verse leaves this out; Sarma (2012) cites the maxim "aṅkānāṃ vāmato
   gatiḥ", "the digits go to the left".

The decoder reads IAST transliteration or Devanagari. In IAST, "kh", "gh" and
the other pairs ending in "h" are read as aspirates, as IAST writes them. The
encoder writes one of the many spellings of a number, 1 syllable per digit,
using the ka series for 1 to 9 and na for 0.

Python's ``int`` is the modern counterpart, so there is no separate comparison
function: ``decode`` returns one.
"""

from __future__ import annotations

import unicodedata

from ancient_algorithms._checks import check_at_least
from ancient_algorithms.place_value import from_digits, pad, to_digits

__all__ = [
    "DIGITS",
    "decode",
    "digits_in_order",
    "encode",
    "melakarta_number",
]

DIGITS: dict[str, int] = {
    **dict.fromkeys(["k", "ṭ", "p", "y"], 1),
    **dict.fromkeys(["kh", "ṭh", "ph", "r"], 2),
    **dict.fromkeys(["g", "ḍ", "b", "l"], 3),
    **dict.fromkeys(["gh", "ḍh", "bh", "v"], 4),
    **dict.fromkeys(["ṅ", "ṇ", "m", "ś"], 5),
    **dict.fromkeys(["c", "t", "ṣ"], 6),
    **dict.fromkeys(["ch", "th", "s"], 7),
    **dict.fromkeys(["j", "d", "h"], 8),
    **dict.fromkeys(["jh", "dh"], 9),
    **dict.fromkeys(["ñ", "n"], 0),
}
"""Value of each consonant, in IAST, from the table in Sarma (2012), p. 39."""

ENCODING_LETTERS = ("na", "ka", "kha", "ga", "gha", "ṅa", "ca", "cha", "ja", "jha")
"""The syllable ``encode`` writes for each digit 0 to 9."""

VOWELS = ("ai", "au", "a", "ā", "i", "ī", "u", "ū", "ṛ", "ṝ", "e", "o")
"""IAST vowels, the 2-letter diphthongs first so they match before ``a``. Vocalic ḷ is rejected."""

IGNORED = frozenset(" -'’|.,;:।॥ṃṁḥँंःऽ")
"""Spaces, punctuation, dandas, avagraha, anusvara and visarga: no value."""

DEVANAGARI_CONSONANTS = dict(
    zip(
        "कखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह",
        "k kh g gh ṅ c ch j jh ñ ṭ ṭh ḍ ḍh ṇ t th d dh n p ph b bh m y r l v ś ṣ s h".split(),
        strict=True,
    )
)
"""Devanagari consonant letters and their IAST spelling."""

VIRAMA = "्"
"""The Devanagari mark that removes a consonant's vowel."""

DEVANAGARI_VOWEL_SIGNS = frozenset(chr(c) for c in range(0x093E, 0x094D))
"""Devanagari vowel signs written after a consonant."""

DEVANAGARI_VOWELS = frozenset(chr(c) for c in range(0x0904, 0x0915) if c != 0x090C) | {"ॠ"}
"""Devanagari vowel letters that stand alone, without vocalic ḷ, to match the IAST reader."""


def digits_in_order(text: str) -> list[int]:
    """The digit of each syllable of ``text``, in the order written (units first)."""
    text = unicodedata.normalize("NFC", text)
    if any(char in DEVANAGARI_CONSONANTS or char in DEVANAGARI_VOWELS for char in text):
        return [_value(consonant) for consonant in _devanagari_syllables(text)]
    return [_value(consonant) for consonant in _iast_syllables(text.lower())]


def decode(text: str) -> int:
    """The number that ``text`` spells, reading the syllables from right to left."""
    digits = digits_in_order(text)
    if not digits:
        raise ValueError(f"no syllables in {text!r}")
    return from_digits(digits[::-1], 10)


def encode(number: int, places: int | None = None) -> str:
    """One IAST spelling of ``number``, units first, 1 syllable per digit.

    ``places`` pads with leading zeros (written last), for values such as 0;03
    in a table where every entry has the same width.
    """
    check_at_least("number", number, 0)
    digits = pad(to_digits(number, 10), places or 0)
    return "".join(ENCODING_LETTERS[d] for d in reversed(digits))


def melakarta_number(name: str) -> int:
    """The number the first 2 syllables of a melakarta raga's name spell, by the rule above.

    This reproduces the 4 names S. R. Sarma (2012) gives: Kanakangi 1, Rupavati
    12, Shanmukhapriya 56 and Rasikapriya 72. It does not give the standard
    number for 9 of the 72 names (standard numbers from the usual list, not from
    a scholarly edition): Cakravakam 16 (this returns 26), Simhendramadhyamam 57
    (87), Divyamani 48 (18), Visvambhari 54 (44), Syamalangi 55 (51), Citrambari
    66 (26), Jyotisvarupini 68 (61), Natabhairavi 20 (10) and Rshabhapriya 62 (60).
    """
    digits = digits_in_order(name)
    if len(digits) < 2:
        raise ValueError(f"a melakarta name needs at least 2 syllables, got {name!r}")
    return 10 * digits[1] + digits[0]


def _iast_syllables(text: str) -> list[str | None]:
    """The counted consonant of each syllable in IAST, or ``None`` for a vowel alone."""
    syllables: list[str | None] = []
    pending: str | None = None
    i = 0
    while i < len(text):
        if text[i] in IGNORED:
            i += 1
            continue
        vowel = _match(text, i, VOWELS)
        if vowel:
            syllables.append(pending)
            pending = None
            i += len(vowel)
            continue
        consonant = _match(text, i, DIGITS)
        if not consonant:
            raise ValueError(f"unknown letter {text[i]!r} in {text!r}")
        pending = consonant
        i += len(consonant)
    return syllables


def _devanagari_syllables(text: str) -> list[str | None]:
    """The counted consonant of each syllable in Devanagari, or ``None`` for a vowel alone."""
    syllables: list[str | None] = []
    for i, char in enumerate(text):
        if char in DEVANAGARI_CONSONANTS:
            next_char = text[i + 1] if i + 1 < len(text) else ""
            if next_char != VIRAMA:
                syllables.append(DEVANAGARI_CONSONANTS[char])
        elif char in DEVANAGARI_VOWELS:
            syllables.append(None)
        elif char not in IGNORED and char != VIRAMA and char not in DEVANAGARI_VOWEL_SIGNS:
            raise ValueError(f"unknown letter {char!r} in {text!r}")
    return syllables


def _match(text: str, i: int, options: tuple[str, ...] | dict[str, int]) -> str:
    """The longest option that ``text`` has at position ``i``, or an empty string."""
    for length in (2, 1):
        piece = text[i : i + length]
        if len(piece) == length and piece in options:
            return piece
    return ""


def _value(consonant: str | None) -> int:
    """The digit a syllable stands for: its consonant's value, or 0 for a vowel alone."""
    return 0 if consonant is None else DIGITS[consonant]
