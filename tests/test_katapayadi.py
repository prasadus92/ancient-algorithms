from datetime import date

import pytest
from hypothesis import given
from hypothesis import strategies as st

from ancient_algorithms.katapayadi import (
    DIGITS,
    decode,
    digits_in_order,
    encode,
    melakarta_number,
)

LETTERS_FOR = {d: sorted(c for c, v in DIGITS.items() if v == d) for d in range(10)}
PLAIN_VOWELS = ["a", "ā", "i", "ī", "u", "ū", "e", "ai", "o", "au"]

# Sarma (2012), note 20: Julian day number minus Kali day count is 588,466.
KALI_TO_JULIAN_DAY = 588_466
JULIAN_DAY_OF_ORDINAL_0 = 1_721_425


def kali_day_to_gregorian(days: int) -> date:
    """Proleptic Gregorian date of a Kali day count, by Sarma's constant offset."""
    return date.fromordinal(days + KALI_TO_JULIAN_DAY - JULIAN_DAY_OF_ORDINAL_0)


# Sadratnamala 4.2 (ed. K. V. Sarma, 2001): the circumference for diameter 10^17.
SADRATNAMALA_PI_IAST = "bhadrāmbudhisiddhajanmagaṇitaśraddhā sma yad bhūpagīḥ"
SADRATNAMALA_PI_DEVANAGARI = "भद्राम्बुधिसिद्धजन्मगणितश्रद्धा स्म यद् भूपगीः"


def test_sadratnamala_pi_in_iast() -> None:
    assert decode(SADRATNAMALA_PI_IAST) == 314159265358979324


def test_sadratnamala_pi_in_devanagari() -> None:
    assert decode(SADRATNAMALA_PI_DEVANAGARI) == 314159265358979324
    assert digits_in_order(SADRATNAMALA_PI_DEVANAGARI) == digits_in_order(SADRATNAMALA_PI_IAST)


def test_sadratnamala_pi_is_pi_to_17_places() -> None:
    pi_18 = "314159265358979323"
    assert str(decode(SADRATNAMALA_PI_IAST))[:17] == pi_18[:17]


# Karanapaddhati verse quoted by Whish (1834), p. 511: the numbers 10^10 and 31415926536.
def test_whish_karanapaddhati_numbers() -> None:
    assert decode("anūnanūnnānananunnanityaiḥ") == 10**10
    assert decode("caṇḍāṃśucandrādhamakumbhipālaiḥ") == 31415926536


# Whish (1834), p. 511: the circle in minutes, 21600, is "anantapura".
def test_whish_anantapura() -> None:
    assert decode("anantapura") == 21600


# Sarma (2012), pp. 38 to 44.
def test_sarma_naṭanara_is_2010() -> None:
    assert decode("naṭanara") == 2010


def test_narayaniyam_chronogram() -> None:
    assert decode("āyurārogyasaukhyam") == 1712210
    assert decode("आयुरारोग्यसौख्यम्") == 1712210
    assert kali_day_to_gregorian(1712210) == date(1586, 12, 8)


def test_suryadeva_birth_chronogram() -> None:
    assert decode("vijñānadīptāśayaḥ") == 1568004


def test_first_2_moon_sentences() -> None:
    # 12 degrees 3 minutes and 24 degrees 9 minutes.
    assert decode("gīr naḥ śreyaḥ") == 1203
    assert decode("dhenavaḥ śrīḥ") == 2409


@pytest.mark.parametrize(
    "name,number",
    [("kanakāṅgī", 1), ("rūpavatī", 12), ("ṣaṇmukhapriyā", 56), ("rasikapriyā", 72)],
)
def test_melakarta_numbers_from_sarma(name: str, number: int) -> None:
    assert melakarta_number(name) == number


def test_rules_of_the_verse() -> None:
    assert digits_in_order("a") == [0]
    assert digits_in_order("kta") == [6]
    assert digits_in_order("kat") == [1]
    assert digits_in_order("kaṃ kaḥ") == [1, 1]


def test_encode_writes_units_first() -> None:
    assert encode(2010) == "nakanakha"
    assert encode(3, places=4) == "gananana"


@given(st.integers(min_value=0, max_value=10**40))
def test_encode_then_decode(number: int) -> None:
    assert decode(encode(number)) == number


@given(st.data())
def test_any_spelling_decodes(data: st.DataObject) -> None:
    digits = data.draw(st.lists(st.integers(min_value=0, max_value=9), min_size=1, max_size=30))
    syllables = []
    for d in digits:
        cluster = data.draw(st.sampled_from(LETTERS_FOR[d]))
        prefix = data.draw(st.sampled_from(sorted(DIGITS)))
        # IAST reads "k" + "h" as the aspirate "kh", so skip prefixes that merge.
        if data.draw(st.booleans()) and prefix[-1] + cluster[0] not in DIGITS:
            cluster = prefix + cluster
        syllables.append(cluster + data.draw(st.sampled_from(PLAIN_VOWELS)))
    text = "".join(syllables)
    assert digits_in_order(text) == digits
    assert decode(text) == int("".join(map(str, reversed(digits))))


@pytest.mark.parametrize("text", ["", "ḥ ṃ", "क्"])
def test_rejects_text_without_syllables(text: str) -> None:
    with pytest.raises(ValueError, match="no syllables"):
        decode(text)


@pytest.mark.parametrize("text", ["kaqa", "क़", "ka1"])
def test_rejects_unknown_letters(text: str) -> None:
    with pytest.raises(ValueError):
        decode(text)


def test_rejects_bad_numbers_and_names() -> None:
    with pytest.raises(ValueError, match="at least 0"):
        encode(-1)
    with pytest.raises(ValueError):
        melakarta_number("ka")
