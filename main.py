#!/usr/bin/env python3
"""One Line, No Deadline Met -- entry generator.

Bounty brief, in my own words: write a single line that works as an
excuse for missing a deadline, and make it funny. The line itself is
the whole submission, so it has to do all of the work on its own.

The judges weigh five things, and I score every candidate against
all five:

  1. excuse -- does it actually read as an excuse for a missed
     deadline, not just a joke that happens to mention work?
  2. humour -- is it funny on first reading, without needing a
     setup or a second sentence to land?
  3. one-liner -- does it stand alone as one line, with a single
     clean image and no trailing explanation?
  4. human -- does it sound like something a real person would
     actually say out loud, not like a line written by a committee?
  5. fresh angle -- is the idea one you have not heard a hundred
     times before in deadline jokes?

This script drafts a slate of original candidates, scores each one
on those five axes, picks the highest scorer, writes it to
/output/entry.txt, and then reads the file back to prove the output
is exactly what was chosen. The selection is fully deterministic:
run it twice and you get byte-identical output.
"""

import hashlib
import os
import sys

# The brief caps the entry at 200 characters, and the gate refuses
# blank or whitespace-only text. We stay well inside both limits.
MAX_CHARS = 200
OUTPUT_PATH = "/output/entry.txt"

# ---------------------------------------------------------------------------
# Candidates
#
# Twelve original one-liners, each written for this brief. They all
# play the same game -- reframe the missed deadline as something
# that was, in the speaker's telling, almost reasonable -- but each
# one takes a different angle so the scoring has real choices to
# make. Candidate 7 is the one I expect to win: the marinating
# metaphor turns procrastination into slow cooking, and then the
# punchline admits the food went off.
# ---------------------------------------------------------------------------

CANDIDATES = [
    # 1. The calendar did it.
    "My calendar said the deadline was Friday, but it never said "
    "which Friday.",

    # 2. The deadline was shy.
    "I didn't miss the deadline, the deadline moved and forgot to "
    "tell me.",

    # 3. Time zones, blamed in earnest.
    "I finished it on time in a different time zone, which I feel "
    "should count for something.",

    # 4. The work needed rest too.
    "I gave the project a long weekend so it could come back "
    "refreshed, and now neither of us is ready.",

    # 5. A watched pot.
    "I kept checking on the deadline so often that it got nervous "
    "and left early.",

    # 6. The dog ate my homework, grown up.
    "My laptop updated itself at the worst possible moment and took "
    "my motivation with it.",

    # 7. The marinating excuse -- the winner.
    "I wasn't procrastinating, I was letting the work marinate "
    "\u2014 it just marinated three days past its expiry date.",

    # 8. The deadline as a mirage.
    "Every time I got close to the deadline it turned out to be a "
    "milestone in disguise, and milestones don't count.",

    # 9. Delegation, taken literally.
    "I delegated the deadline to future me, and future me has "
    "filed a formal complaint.",

    # 10. The deadline as a suggestion.
    "I treated the deadline as more of a rough guideline, and it "
    "turns out guidelines have feelings too.",

    # 11. Slow and steady, too steady.
    "I was pacing myself for a marathon and only just realised "
    "this was a sprint with a finish line last Tuesday.",

    # 12. The honest one.
    "I kept meaning to start early, and I meant it every single "
    "day right up until the day after it was due.",
]


# ---------------------------------------------------------------------------
# Scoring
#
# Each axis is scored 0-10 by hand, in the table below. The weights
# mirror how the brief reads to me: the excuse has to land first
# (it is, after all, an excuse), the joke has to be funny, and the
# rest -- standing alone, sounding human, feeling fresh -- share the
# remainder. Scores are fixed constants, not computed from the text,
# because judging a joke is a human call and pretending a formula
# could do it would be dishonest. What the code does guarantee is
# that the same scores always pick the same winner.
# ---------------------------------------------------------------------------

# Weights sum to 1.0.
WEIGHTS = {
    "excuse": 0.30,
    "humour": 0.30,
    "one_liner": 0.15,
    "human": 0.15,
    "fresh": 0.10,
}

# Hand scores, one row per candidate, in the same order as above.
# Rationale for the winner, candidate 7: it is a genuine excuse
# ("I wasn't procrastinating" is the classic opening of one), the
# marinating image is funny and visual, it is a single self-contained
# line, it sounds like something a person would actually say to a
# manager, and the expiry-date twist is a fresher turn than blaming
# the calendar or the laptop. The runners-up lose on freshness
# (calendar jokes, laptop jokes) or on the excuse axis (several are
# jokes about deadlines rather than excuses for missing one).
SCORES = [
    # excuse, humour, one-liner, human, fresh
    (7, 6, 9, 8, 4),    # 1: calendar -- clean, but an old joke
    (8, 6, 8, 7, 5),    # 2: shy deadline -- decent excuse, thin joke
    (8, 7, 8, 8, 5),    # 3: time zones -- likeable, not new
    (6, 7, 7, 7, 6),    # 4: long weekend -- more joke than excuse
    (6, 7, 8, 6, 6),    # 5: watched pot -- cute, excuse is weak
    (7, 5, 7, 8, 3),    # 6: laptop update -- everyone has said it
    (10, 9, 9, 9, 8),   # 7: marinating -- the winner
    (6, 7, 7, 6, 6),    # 8: mirage -- clever, but it dodges blame
    (7, 8, 8, 8, 6),    # 9: future me -- strong, second place
    (8, 6, 7, 7, 5),    # 10: guideline -- solid, forgettable
    (7, 6, 8, 7, 5),    # 11: marathon -- fine, no punch
    (8, 7, 9, 9, 4),    # 12: honest one -- human, but no twist
]


def weighted_total(row):
    """Combine one candidate's five axis scores into a total.

    The tuple order matches AXES below, so the pairing is explicit
    and cannot silently drift if the weights dict is reordered.
    """
    axes = ["excuse", "humour", "one_liner", "human", "fresh"]
    total = 0.0
    for axis, score in zip(axes, row):
        total += score * WEIGHTS[axis]
    return round(total, 2)


def rank_candidates():
    """Score every candidate and return them best-first.

    Ties are broken by original order (stable sort), so the ranking
    is deterministic and the winner never depends on dict ordering
    or hash randomisation.
    """
    ranked = []
    for index, (line, row) in enumerate(zip(CANDIDATES, SCORES)):
        ranked.append((weighted_total(row), index, line))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return ranked


def check_entry(line):
    """Enforce the brief's hard limits before anything is written."""
    if not line or not line.strip():
        raise ValueError("entry must not be blank")
    if len(line) > MAX_CHARS:
        raise ValueError(
            "entry is %d characters, over the %d limit"
            % (len(line), MAX_CHARS)
        )
    if "\n" in line or "\r" in line:
        raise ValueError("entry must be a single line")


def write_entry(line):
    """Write the entry and prove the file matches, byte for byte.

    The file is written with no trailing newline: the brief asks for
    one line of text, and a trailing newline would make the file
    contain a second, empty line. After writing, the file is read
    back and compared against the chosen line, and its SHA-256 is
    printed so any later run can be checked for drift.
    """
    check_entry(line)
    directory = os.path.dirname(OUTPUT_PATH)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8", newline="") as handle:
        handle.write(line)
    with open(OUTPUT_PATH, "rb") as handle:
        raw = handle.read()
    if raw != line.encode("utf-8"):
        raise ValueError("written file does not match the chosen entry")
    digest = hashlib.sha256(raw).hexdigest()
    print("wrote %s (%d chars)" % (OUTPUT_PATH, len(line)))
    print("sha256: %s" % digest)
    return digest


def main():
    # Sanity checks on the slate itself, before any scoring runs:
    # enough candidates to choose from, one score row per candidate,
    # and every axis score inside its 0-10 range. A typo in the
    # table should fail loudly here, not silently pick a wrong line.
    if len(CANDIDATES) < 10:
        raise ValueError("need at least 10 candidates, have %d"
                         % len(CANDIDATES))
    if len(SCORES) != len(CANDIDATES):
        raise ValueError("score rows (%d) do not match candidates (%d)"
                         % (len(SCORES), len(CANDIDATES)))
    for row in SCORES:
        if len(row) != 5 or any(not 0 <= s <= 10 for s in row):
            raise ValueError("bad score row: %r" % (row,))
    if len(set(CANDIDATES)) != len(CANDIDATES):
        raise ValueError("duplicate candidate lines")
    ranked = rank_candidates()
    print("candidate scores (best first):")
    for total, index, line in ranked:
        print("  #%02d  %.2f  %s" % (index + 1, total, line))
    best_total, _, winner = ranked[0]
    print("winner: #%02d with %.2f" % (ranked[0][1] + 1, best_total))
    write_entry(winner)
    return 0


if __name__ == "__main__":
    sys.exit(main())


