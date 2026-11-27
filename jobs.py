"""Split one Telegram post into separate jobs, and pick the lines worth showing.

Many agencies post one job per message, but some post compiled lists with many jobs.
A post is cut into chunks at blank lines and at job-code lines ("2611su:", "Job Code: ...").
A new job starts when a chunk mentions a level (P5, Sec 3, JC1...) and the current job
already has one, or at a job-code line (unless the current job is only a code so far). Chunks with no
level (address, rate, requirements) stay with the job above them.
"""

from __future__ import annotations

import re

LEVEL = re.compile(
    r"(?<![A-Za-z0-9])("
    r"P[1-6]|Pri(?:mary)?\s*[1-6]|Sec(?:ondary)?\s*[1-5]|S[1-5]|JC\s*[12]?|J[12]|K[12]|N[12]"
    r"|Nursery|Kindergarten|Pre-?school|IGCSE|IB|[OAN][\s-]*Levels?|Poly(?:technic)?"
    r")(?![A-Za-z0-9])",
    re.I,
)
JOB_MARKER = re.compile(
    r"^\W*("
    r"\d{4}[a-z]{2,3}\s*:"  # 2611su:
    r"|(?:job|assignment)\s*(?:code|id|no\.?)\b"  # Job Code / Assignment code / Job ID
    r"|code\s*(?:id)?\s*:"  # Code ID:
    r")",
    re.I,
)
HAS_WORD = re.compile(r"[A-Za-z0-9]")
BOILERPLATE = re.compile(r"^\W*(new\s+)?(urgent\s+)?tuition\s+(job|assignment)s?\W*$", re.I)


def _chunks(text: str) -> list[str]:
    chunks: list[list[str]] = [[]]
    for line in text.splitlines():
        if not line.strip():
            chunks.append([])
            continue
        if JOB_MARKER.match(line) and chunks[-1]:
            chunks.append([])
        chunks[-1].append(line)
    return ["\n".join(c) for c in chunks if c]


def split_jobs(text: str) -> list[str]:
    jobs: list[str] = []
    has_level = False
    job_has_marker = False
    for chunk in _chunks(text):
        chunk_level = bool(LEVEL.search(chunk))
        starts_with_marker = bool(JOB_MARKER.match(chunk))
        new_job = (
            not jobs
            or (has_level and chunk_level)
            # A job code starts a new job, unless the current job is just a code with no details yet.
            or (starts_with_marker and (has_level or not job_has_marker))
        )
        if new_job:
            jobs.append(chunk)
            has_level = chunk_level
            job_has_marker = starts_with_marker
        else:
            jobs[-1] += "\n" + chunk
            has_level = has_level or chunk_level
    return jobs or [text]


def summary_lines(job: str, max_lines: int = 6, max_chars: int = 140) -> list[str]:
    """The lines to show in the digest: no emoji-only or 'New Tuition Job' header lines."""
    out = []
    for line in job.splitlines():
        line = line.strip()
        if not HAS_WORD.search(line) or BOILERPLATE.match(line):
            continue
        out.append(line if len(line) <= max_chars else line[: max_chars - 1] + "…")
        if len(out) == max_lines:
            break
    return out
