# How the report is generated — plain English

Same order as the file itself. No code, just the logic.

---

## 1. What goes in

For every person who takes the test, the backend hands over:

- Their name, track, and the date they took it
- How many questions they answered, got right, got wrong
- A score out of 10 for each skill (SQL, Statistics, Algorithms, etc.), plus
  the cohort's average score on that same skill
- A short, pre-written sentence for each skill explaining *why* it's a gap
  or a strength (this one sentence per skill is the only part written by
  an AI model — everything else on this page is plain arithmetic)
- A fixed list of study resources (guides, links), each tagged with which
  skill it belongs to

Nothing else feeds into the report. Every number and every sentence you see
traces back to one of these five things.

---

## 2. The one rule that sorts every skill into a bucket

For each skill, take the person's score and subtract the cohort average.
That gap decides the bucket:

- **1 point or more behind average → "growth"** (a real weak spot)
- **1 point or more ahead of average → "strength"** (a real edge)
- **Anywhere in between → "developing"** (basically tied with everyone else)

That's it — one number, one rule, three buckets. This bucket is what
controls almost everything downstream: which section of the roadmap a
skill lands in, how many study sessions it gets, and what color dot it
gets throughout the report.

---

## 3. Top summary (questions answered, correct, incorrect)

No logic here at all — it just prints the numbers from the test session
as-is: how many questions, how many right, how many wrong, and the
accuracy percentage.

---

## 4. Skill fingerprint — the score table and the radar chart

For each skill, the report shows an arrow:

- **Up arrow** if the person is more than 0.4 points above the cohort average
- **Down arrow** if more than 0.4 points below
- **A flat dash** if it's closer than that

Notice this is a *different, more sensitive* cutoff than the growth /
developing / strength rule above (0.4 vs. 1.0). That's on purpose: the
table wants to flag *any* visible lean one way or the other, even a small
one, while the roadmap only wants to act on gaps that are big enough to
matter.

The radar chart (the spider-web shape) plots the same scores and averages
as points around a circle — one spoke per skill — so you can see the whole
shape of the person's ability at a glance. It doesn't use the bucket rule
at all for its shape, only for which color it dots each point.

---

## 5. The upskilling roadmap — what order skills are shown in

The roadmap always shows three groups, in this fixed order:

1. **Focus first** — every "growth" skill (the real gaps)
2. **Sharpen next** — every "developing" skill (near-average)
3. **Maintain & leverage** — every "strength" skill (real edges)

If nobody has any skills in a group (say, everyone did fine and there are
no growth skills), that whole group is just skipped — it doesn't show up
as an empty section.

Within "Focus first" and "Sharpen next," skills are sorted so the *widest
gap comes first* — the skill furthest behind the cohort gets top billing,
because that's where effort pays off fastest.

Within "Maintain & leverage," it's flipped — the *biggest strength comes
first*, since that's the skill most worth calling out in an interview or
on a resume.

For each skill in the list, the report shows: the gap versus average, the
one-line "why this matters" sentence written for that skill, and a link to
a study resource if one exists for that skill (some skills, like
Behavioral, don't have a dedicated resource yet, so it just says so).

---

## 6. The study calendar — how many days, and what to do each day

This section takes the exact same skill order as the roadmap above (widest
gaps first) and turns it into a day-by-day plan.

Each skill gets a number of study sessions based on which bucket it's in:

- **Growth skills get 4 sessions**, always in this order: first *learn* the
  concept, then *practice* untimed, then *practice under time pressure*,
  then *review what you got wrong*.
- **Developing skills get 2 sessions**: *practice* the specific weak spots,
  then *apply* it by mixing in some harder, related problems.
- **Strength skills get 1 session**: just a light *maintenance* rep so it
  doesn't get rusty — no need to relearn it.

So a skill that's badly behind gets a full four-day arc; a skill that's
merely near-average gets two days; a skill that's already ahead gets a
single check-in.

The days are numbered relative to a start point — "T+1," "T+2," and so on
— rather than real calendar dates, so the same plan works no matter when
someone actually opens the report. One day in every seven is treated as a
rest day and skipped in the numbering, so the plan isn't back-to-back with
no breaks.

---

## 7. The resource table at the bottom

This one has no logic either — it's just the complete, unfiltered list of
every study resource available, shown as-is, regardless of which skills
were weak or strong.

---

## Worked example, start to finish

Take "Algorithms": the person scored 0, the cohort averaged 2.3, so the
gap is -2.3. Since that's more than 1 point behind, it's bucketed as
**growth**. Because it's the single widest gap in the whole profile, it
appears **first** in "Focus first," and it's also **first** in the study
calendar — a 4-day run (T+1 through T+4): learn the fundamentals, untimed
practice, timed practice, then review the mistakes.

Compare that to "SQL": scored 4 against a cohort average of 3.7 — a gap of
only +0.3, well inside the ±1 window, so it's bucketed as **developing**.
It shows up in "Sharpen next," lower down the roadmap, and gets a lighter
2-day treatment in the calendar: practice the weak spots, then apply it.

And "Statistics": scored 9 against an average of 5.0 — a +4.0 gap, easily
over the +1 threshold, so it's a **strength**. It's the very last thing in
the roadmap, framed as something to maintain rather than fix, and gets
just one light session in the calendar to keep it sharp.

Same underlying number (the gap between score and average) — three
completely different treatments, because of where that one number falls.
