from jobs import split_jobs, summary_lines
from reader import parse_page

COMPILED = """Compiled Tuition Assignments (26 Nov 26)
Full Time Tutors Part 2 of 4

2611su:
2027 P5 English @ 45B Edgefield Plains, Waterbay (S)828712

2611sv:
2027 P6 Math @ 123 Bedok North Ave 3 (S)460123

2611sw:
Sec 2 Science @ Tampines St 81 (S)520123
Female tutor preferred"""

SINGLE = """💥 New Tuition Job 💥
🔻
Level and Subject(s): P5 Science

Location/Area: 401 Bedok North Avenue 3 (S)460401

Rate: $35-40/hr
Frequency: 1.5h x 1 weekly

Requirements:
1. Patient
2. Experienced with Sec 1 to Sec 4 students too"""

CODE_FIRST = """Code ID: 2611yh
(Full-Tutor or Ex/Current MOE Teacher)
Subject: P5 Science (Bedok Green Pri)
Address: 166 Bedok South Avenue 3 (S)460166"""


def test_compiled_post_splits_per_job():
    jobs = split_jobs(COMPILED)
    assert len(jobs) == 4  # header + 3 jobs
    assert "P6 Math" in jobs[2] and "Bedok" in jobs[2]
    assert "Edgefield" not in jobs[2]
    assert "Female tutor preferred" in jobs[3]


def test_single_job_stays_whole():
    jobs = split_jobs(SINGLE)
    assert len(jobs) == 1 or all("Sec 1" in j for j in jobs[1:])
    assert "P5 Science" in jobs[0] and "460401" in jobs[0] and "Rate" in jobs[0]


def test_code_first_job_stays_whole():
    assert split_jobs(CODE_FIRST) == [CODE_FIRST]


def test_summary_skips_emoji_and_header_lines():
    lines = summary_lines(SINGLE)
    assert lines[0] == "Level and Subject(s): P5 Science"
    assert lines[1].startswith("Location/Area: 401 Bedok")


def test_inline_tags_do_not_break_lines():
    html = (
        '<div class="tgme_widget_message" data-post="c/1">'
        '<div class="tgme_widget_message_text"><i class="emoji">💥</i> New Tuition Job<br/><br/>'
        "<b>Level and Subject(s):</b> P5 Science<br/><b>Rate:</b> $40/hr</div></div>"
    )
    text = parse_page(html, "c")[0].text
    assert text == "💥 New Tuition Job\n\nLevel and Subject(s): P5 Science\nRate: $40/hr"


def test_code_then_blank_line_then_fields_stays_whole():
    text = "Job Code: 12345\n\nLevel: P5 Math\n\nLocation: Bedok (S)460123\n\nRate: $40/hr"
    assert split_jobs(text) == [text.replace("\n\n", "\n")]


def test_only_matching_job_from_compiled_post_is_kept():
    from filters import matches
    from reader import Post

    criteria = {"levels": ["P5", "P6"], "subjects": ["Math"], "locations": {"postal_prefixes": ["46"]}}
    kept = [j for j in split_jobs(COMPILED) if matches(Post("c", 1, None, j, "l"), criteria)]
    assert len(kept) == 1 and "2611sv" in kept[0]
