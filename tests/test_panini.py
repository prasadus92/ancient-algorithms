import pytest
from hypothesis import given
from hypothesis import strategies as st

from ancient_algorithms.panini import (
    GUNA,
    SHIVA_SUTRAS,
    VRDDHI,
    antaratama,
    derive,
    join,
    join_words,
    pratyahara,
    rewrite_to_fixpoint,
    savarnas,
)

# The 41 pratyaharas the Kasikavrtti lists, each with the Shiva Sutra whose marker ends it.
KASIKA_PRATYAHARAS = [
    ("aṇ", 1),
    ("ak", 2), ("ik", 2), ("uk", 2),
    ("eṅ", 3),
    ("ac", 4), ("ic", 4), ("ec", 4), ("aic", 4),
    ("aṭ", 5),
    ("aṇ", 6), ("iṇ", 6), ("yaṇ", 6),
    ("am", 7), ("yam", 7), ("ṅam", 7),
    ("yañ", 8),
    ("bhaṣ", 9), ("jhaṣ", 9),
    ("aś", 10), ("haś", 10), ("vaś", 10), ("jaś", 10), ("jhaś", 10), ("baś", 10),
    ("chav", 11),
    ("yay", 12), ("may", 12), ("jhay", 12), ("khay", 12),
    ("yar", 13), ("jhar", 13), ("khar", 13), ("car", 13), ("śar", 13),
    ("al", 14), ("hal", 14), ("val", 14), ("ral", 14), ("jhal", 14), ("śal", 14),
]  # fmt: skip


def test_kasika_pratyaharas_all_expand() -> None:
    for name, sutra in KASIKA_PRATYAHARAS:
        assert pratyahara(name, marker_sutra=sutra)


def test_kasika_verse_on_how_many_pratyaharas_each_marker_forms() -> None:
    # "ekasman nanavata dvabhyam sas tribhya eva kanamah syuh /
    #  jneyau cayau caturbhyo rah pancabhyah salau sadbhyah" (Kasikavrtti, end of the Shiva Sutras).
    per_sutra = [sum(1 for _, s in KASIKA_PRATYAHARAS if s == i) for i in range(1, 15)]
    assert per_sutra == [1, 3, 1, 4, 1, 3, 3, 1, 2, 6, 1, 4, 5, 6]
    assert len(KASIKA_PRATYAHARAS) == 41


def test_well_known_pratyaharas() -> None:
    assert pratyahara("ac") == ("a", "i", "u", "ṛ", "ḷ", "e", "o", "ai", "au")
    assert pratyahara("ik") == ("i", "u", "ṛ", "ḷ")
    assert pratyahara("yaṇ") == ("y", "v", "r", "l")
    assert pratyahara("eṅ") == ("e", "o")
    assert pratyahara("ec") == ("e", "o", "ai", "au")
    assert len(pratyahara("hal")) == 33
    assert pratyahara("śal") == ("ś", "ṣ", "s", "h")
    assert pratyahara("jaś") == ("j", "b", "g", "ḍ", "d")


def test_an_reads_differently_at_its_2_markers() -> None:
    # Kasikavrtti: every an ends at the first n, except in 1.1.69, which ends at the second.
    assert pratyahara("aṇ") == ("a", "i", "u")
    assert pratyahara("aṇ", marker_sutra=6)[-5:] == ("h", "y", "v", "r", "l")
    assert pratyahara("iṇ") == pratyahara("iṇ", marker_sutra=6)


def test_guna_and_vrddhi_from_their_definitions() -> None:
    # 1.1.2 ad eng gunah and 1.1.1 vrddhir ad aic.
    assert GUNA == ("a", "e", "o")
    assert VRDDHI == ("ā", "ai", "au")


def test_savarnas_adds_long_vowels() -> None:
    assert savarnas(pratyahara("ik")) == {"i", "ī", "u", "ū", "ṛ", "ṝ", "ḷ"}


def test_antaratama_picks_by_place() -> None:
    assert antaratama(frozenset({"lips"}), pratyahara("yaṇ")) == "v"
    assert antaratama(frozenset({"throat", "palate"}), GUNA) == "e"


def test_bad_pratyaharas_raise() -> None:
    with pytest.raises(ValueError):
        pratyahara("x")
    with pytest.raises(ValueError):
        pratyahara("aq")
    with pytest.raises(ValueError):
        pratyahara("ṛṇ", marker_sutra=1)
    with pytest.raises(ValueError):
        pratyahara("ak", marker_sutra=3)


# Examples from Varadaraja's Laghusiddhantakaumudi, vowel-sandhi section (GRETIL e-text).
LSK_EXAMPLES = [
    ("sudhī", "upāsyaḥ", True, "sudhyupāsyaḥ", "6.1.77"),
    ("madhu", "ariḥ", True, "madhvariḥ", "6.1.77"),
    ("dhātṛ", "aṃśaḥ", True, "dhātraṃśaḥ", "6.1.77"),
    ("ḷ", "ākṛtiḥ", True, "lākṛtiḥ", "6.1.77"),
    ("hare", "e", False, "haraye", "6.1.78"),
    ("viṣṇo", "e", False, "viṣṇave", "6.1.78"),
    ("nai", "akaḥ", False, "nāyakaḥ", "6.1.78"),
    ("pau", "akaḥ", False, "pāvakaḥ", "6.1.78"),
    ("upa", "indraḥ", True, "upendraḥ", "6.1.87"),
    ("gaṅgā", "udakam", True, "gaṅgodakam", "6.1.87"),
    ("kṛṣṇa", "ṛddhiḥ", True, "kṛṣṇarddhiḥ", "6.1.87"),
    ("tava", "ḷkāraḥ", True, "tavalkāraḥ", "6.1.87"),
    ("kṛṣṇa", "ekatvam", True, "kṛṣṇaikatvam", "6.1.88"),
    ("gaṅgā", "oghaḥ", True, "gaṅgaughaḥ", "6.1.88"),
    ("deva", "aiśvaryam", True, "devaiśvaryam", "6.1.88"),
    ("kṛṣṇa", "autkaṇṭhyam", True, "kṛṣṇautkaṇṭhyam", "6.1.88"),
    ("daitya", "ariḥ", True, "daityāriḥ", "6.1.101"),
    ("śrī", "īśaḥ", True, "śrīśaḥ", "6.1.101"),
    ("viṣṇu", "udayaḥ", True, "viṣṇūdayaḥ", "6.1.101"),
    ("hotṛ", "ṛkāraḥ", True, "hotṝkāraḥ", "6.1.101"),
    ("hare", "ava", True, "hare'va", "6.1.109"),
    ("viṣṇo", "ava", True, "viṣṇo'va", "6.1.109"),
]


@pytest.mark.parametrize(("left", "right", "boundary", "form", "rule"), LSK_EXAMPLES)
def test_laghusiddhantakaumudi_examples(
    left: str, right: str, boundary: bool, form: str, rule: str
) -> None:
    steps = derive(left, right, word_boundary=boundary)
    assert join(left, right, word_boundary=boundary) == form
    assert [step.chosen for step in steps] == [rule]


def test_the_later_rule_wins_a_conflict() -> None:
    # 1.4.2: in each pair of applicable rules, the later sutra wins.
    assert derive("daitya", "ariḥ")[0].applicable == ["6.1.87", "6.1.101"]
    assert derive("śrī", "īśaḥ")[0].applicable == ["6.1.77", "6.1.101"]
    assert derive("kṛṣṇa", "ekatvam")[0].applicable == ["6.1.87", "6.1.88"]


def test_word_final_e_absorbs_a_only_at_a_word_boundary() -> None:
    # 6.1.109 needs the end of a word; inside a word 6.1.78 applies, as in nayanam from ne + anam.
    assert join("hare", "ava") == "hare'va"
    assert join("ne", "anam", word_boundary=False) == "nayanam"


def test_kiparsky_sentence() -> None:
    # Kiparsky, "On the architecture of Panini's grammar", example (24).
    assert join_words(["adya", "iha", "apāci", "odanaḥ"]) == "adyehāpācyodanaḥ"


def test_tripadi_deletion_is_invisible_to_earlier_rules() -> None:
    # Laghusiddhantakaumudi on 8.2.1: hara iha or harayiha, visna iha or visnaviha.
    assert join("hare", "iha") == "harayiha"
    assert join("hare", "iha", sakalya=True) == "hara iha"
    assert join("viṣṇo", "iha", sakalya=True) == "viṣṇa iha"


def test_without_asiddha_the_rules_run_on_to_a_wrong_form() -> None:
    assert rewrite_to_fixpoint("hare", "iha") == "hareha"


def test_tripadi_deletion_needs_a_before_the_glide() -> None:
    assert join("sudhy", "iha", sakalya=True) == "sudhyiha"


def test_tripadi_deletion_needs_a_voiced_sound_after() -> None:
    assert join("tay", "kaḥ", sakalya=True) == "taykaḥ"


def test_join_words_needs_a_word() -> None:
    with pytest.raises(ValueError):
        join_words([])


def test_l_vowel_has_no_long_form() -> None:
    with pytest.raises(ValueError):
        join("ḷ", "ḷ")


def textbook_vowel_sandhi(first: str, second: str) -> str:
    """The standard vowel-sandhi table at a word boundary, written without Panini's rules."""
    long_of = {"a": "ā", "i": "ī", "u": "ū", "ṛ": "ṝ"}
    short_of = {v: k for k, v in long_of.items()} | {k: k for k in long_of}
    a_with = {"i": "e", "u": "o", "ṛ": "ar", "e": "ai", "ai": "ai", "o": "au", "au": "au"}
    glide = {"i": "y", "u": "v", "ṛ": "r"}
    if first in short_of and short_of.get(second) == short_of[first]:
        return long_of[short_of[first]]
    if short_of.get(first) == "a":
        return a_with[short_of.get(second, second)]
    if first in short_of:
        return glide[short_of[first]] + second
    if first in ("e", "o") and second == "a":
        return first + "'"
    return {"e": "ay", "o": "av", "ai": "āy", "au": "āv"}[first] + second


vowel = st.sampled_from(["a", "ā", "i", "ī", "u", "ū", "ṛ", "ṝ", "e", "o", "ai", "au"])


@given(first=vowel, second=vowel)
def test_rules_reproduce_the_textbook_table(first: str, second: str) -> None:
    assert join("k" + first, second + "t") == "k" + textbook_vowel_sandhi(first, second) + "t"


@given(first=vowel, second=vowel)
def test_one_rule_closes_every_vowel_junction(first: str, second: str) -> None:
    assert len(derive("k" + first, second + "t")) == 1


def test_shiva_sutras_list_43_sounds_with_h_twice() -> None:
    listed = [sound for sounds, _ in SHIVA_SUTRAS for sound in sounds]
    assert len(SHIVA_SUTRAS) == 14
    assert len(listed) == 43
    assert len(set(listed)) == 42
