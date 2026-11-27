from filters import matches
from reader import Post

# Fixed criteria so these tests don't change when you edit config.yaml.
CRITERIA = {
    "levels": ["JC", "JC1", "JC2", "J1", "J2", "Junior College", "A Level", "H1", "H2"],
    "subjects": ["Math", "Maths", "Mathematics", "Physics"],
    "locations": {"postal_prefixes": ["51"], "towns": ["Pasir Ris"]},
    "exclude_online": True,
    "exclude_keywords": ["female tutor only"],
}


def p(text):
    return Post(channel="c", id=1, date=None, text=text, link="https://t.me/c/1")


def test_jc_math_pasir_ris_postal_matches():
    assert matches(p("Level: JC2\nSubject: H2 Math\nLocation: 21 Pasir Ris Rise (518090)"), CRITERIA)


def test_town_name_without_postal_code_matches():
    assert matches(p("J1 Physics @ Pasir Ris Drive 6\nRate: $70/hr"), CRITERIA)


def test_postal_prefix_without_town_matches():
    assert matches(p("A-Level Mathematics\nBlk 123 (510123)"), CRITERIA)


def test_wrong_level_rejected():
    assert not matches(p("Sec 2 Exp Math\nLocation: Pasir Ris (518090)"), CRITERIA)


def test_wrong_subject_rejected():
    assert not matches(p("JC1 H2 Chemistry\nPasir Ris (518090)"), CRITERIA)


def test_wrong_area_rejected():
    assert not matches(p("JC2 Physics\nLocation: Bishan Street 13 (570123)"), CRITERIA)


def test_job_code_digits_are_not_a_postal_code():
    assert not matches(p("Job Code: 511310CW2\nJC1 Math @ Toa Payoh"), CRITERIA)


def test_online_rejected():
    assert not matches(p("JC2 Math, Online lessons\nPasir Ris (518090)"), CRITERIA)


def test_female_tutor_only_rejected():
    assert not matches(p("JC1 Physics\nPasir Ris (518090)\nFemale tutor only"), CRITERIA)


def test_jc_inside_other_word_not_matched():
    assert not matches(p("ABJCD Math\nPasir Ris (518090)"), CRITERIA)


def test_postal_code_outranks_town_name():
    crit = {"locations": {"postal_prefixes": ["47"], "towns": ["Bedok"]}}
    assert not matches(p("P5 Science\n166 Bedok South Avenue 3 (S)460166"), crit)
    assert matches(p("P5 Science\n629 Bedok Reservoir Rd (S)470629"), crit)
    assert matches(p("P5 Science\nBedok North Ave 3, near MRT"), crit)
