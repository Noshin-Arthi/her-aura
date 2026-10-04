# Her Aura Requirements

**Product goal:** Her Aura is a personal health record and assistant for women. Users log any health issue, see their history,
learn when and whom to consult and book doctors. Cycle, temperature, sleep, mindfulness and (later) fitness and nutrition
modules are aware of the user's cycle phase. Evidence for each feature: [RESEARCH.md](RESEARCH.md).

User stories with acceptance criteria (ACs). Every AC maps to at least one automated test
(see [TEST_STRATEGY.md](TEST_STRATEGY.md#traceability)). Run `python -m ai.test_planner US-05` to draft a test plan for a story.

Status: **Done** = built and tested. **Planned** = on the roadmap.

## US-01 Register an account (Done)
As a new user, I want to create an account so my health data is private to me.
- AC1: Registering with name, valid email and a password of 8+ characters logs me in and shows my dashboard.
- AC2: Registering with an email that already exists (any letter case) shows "already registered".
- AC3: Invalid email, short password or 1-letter name is rejected with a clear message.
- AC4: The password is never stored in plain text.

## US-02 Log in and out (Done)
- AC1: Correct email and password log me in.
- AC2: A wrong email or password shows the same generic error (no hint which one was wrong).
- AC3: Pages that need login redirect a logged-out user to the login page.

## US-03 Log daily symptoms (Done)
As a patient, I want to record my period, pain and symptoms each day.
- AC1: A saved log (date, flow, pain 0-10, symptoms, notes) appears on my dashboard.
- AC2: A future date is rejected.
- AC3: Only one log per day is allowed.
- AC4: Pain outside 0-10 is rejected.
- AC5: I can never see another user's logs.

## US-04 Red-flag insight (Done)
As a patient, I want to be told when my symptoms are frequent enough to see a doctor.
Rule: pelvic/abdominal pain, bloating or early fullness on 12+ of the last 30 days
(adapted from the Goff Ovarian Cancer Symptom Index).
- AC1: 12 or more symptom days in the last 30 shows a warning and a "Find a gynecologist" link.
- AC2: 11 symptom days does not show the warning.
- AC3: A disclaimer that the app does not diagnose is always shown.
- AC4: Symptoms older than 30 days and urinary urgency alone do not count.
- AC5: The dashboard always shows a neutral counter ("Symptom days: N of last 30") with a "How is this calculated?" explanation that says it is not a diagnosis.

## US-05 Book an appointment (Done)
As a patient, I want to book an open slot with a gynecologist near me.
- AC1: I can book an open future slot, optionally with a reason; it appears in My appointments as "booked".
- AC2: A booked slot is no longer offered to anyone.
- AC3: Two patients booking the same slot at the same moment: exactly one succeeds.
- AC4: Slots in the past cannot be booked.

## US-06 Cancel an appointment (Done)
- AC1: I can cancel a booked appointment; its status becomes "cancelled" and the slot is offered again.
- AC2: Cancelling less than 2 hours before the start is rejected.
- AC3: I cannot cancel someone else's appointment.

## US-07 Doctor portal (Planned)
As a doctor, I want to publish my available slots and see my upcoming patients.

## US-08 Referrals (Planned)
As a doctor, I want to refer a patient to a specialist (e.g. gynecologic oncology) and track the referral status.

## US-09 Nearby clinics on a map (Planned)
As a patient, I want to see clinics near my location, sorted by distance (OpenStreetMap).

## US-10 AI doctor-visit summary (Planned)
As a patient, I want a one-page summary of my last 3 months of logs to show my doctor.
The summary must only state what I logged, never a diagnosis.

## US-11 Reminders (Planned)
As a patient, I want an optional daily reminder to log, and a reminder for my next checkup. Reminders are opt-in and customizable.

## US-12 Delete my data (Planned)
As a patient, I want to permanently delete my account and all my health data.

## US-13 Same as yesterday (Done)
As a patient with a multi-day episode, I want to repeat yesterday's log in one tap.
- AC1: "Same as yesterday" copies flow, pain and symptoms from yesterday to today. Notes are not copied.
- AC2: If there is no log for yesterday, a clear error is shown.
- AC3: It never overwrites an existing log for today.

## US-14 Calendar heatmap (Planned)
As a patient, I want a monthly calendar colored by pain/symptom severity so I can spot monthly patterns.

## US-15 One-tap logging UI (Done)
Pain is a 0-10 slider, flow and symptoms are tap-to-select chips, notes are optional and collapsed, and the date cannot be set in the future.

## US-16 Log any health issue (Done)
As a user, I want to log what I'm feeling (headache, toothache, rash, hair fall, tiredness...) with a severity 1-10 and notes, so I have a personal history to review.
- AC1: A logged issue appears in my history with its label, severity and notes.
- AC2: Several different issues on the same day are allowed.
- AC3: Unknown categories, severity outside 1-10 and future dates are rejected.
- AC4: My history is private to me.

## US-17 Which doctor, and when? (Done, rule-based)
As a user, I want to be told when an issue needs a doctor and which specialist to see.
- AC1: Severity 8+ in the last 3 days → "See a doctor soon" with that issue's first specialty (e.g. toothache → Dentistry).
- AC2: The same issue on 4+ different days in 14 → "Consider a visit" to its specialist (e.g. recurring headache → Neurology).
- AC3: 3+ different general symptoms (tiredness, hair fall, rash, fever) in 14 days → general checkup suggestion.
- AC4: Emergency guidance (call 999) and a "not a diagnosis" note are always visible.
- AC5: Each suggestion explains why, gives lifestyle tips, and links to doctors of that specialty.
- AC6: Every specialty the rules can suggest has at least one bookable doctor.

## US-18 Doctors by specialty + call (Done)
- AC1: Doctors can be filtered by specialty.
- AC2: Each doctor shows a "Call clinic" phone link.

## US-19 Fitness and gym records (Planned)
Workouts (type, duration, sets/reps/weight), weekly goals, progress chart.

## US-20 Nutrition and calorie goals (Planned)
Daily meals with calories and protein, a goal based on age, height, weight and activity, and tips linked to logged issues (e.g. hair fall → protein/iron).

## US-21 Doctor reviews (Planned)
Rate a doctor 1-5 only after a completed appointment; one review per appointment; average shown on the doctor card.

## US-22 Hospitals by specialty (Planned)
Search hospitals and clinics by the specialties and diseases they treat; distance from the user.

## US-23 AI health assistant (Planned)
An LLM reads the user's history and explains patterns, suggests specialists and lifestyle changes. Must cite the user's own logs, never diagnose, always show emergency guidance, and fall back to the US-17 rules when unavailable. Tested with an eval suite.

## US-24 Landing page with a "Try it" demo (Done)
As a visitor, I want to see what Her Aura would suggest before I create an account.
- AC1: Picking symptoms, a severity (1-10) and a number of days (1-14) shows a live suggestion with no login; nothing is saved.
- AC2: The demo uses exactly the same rules as the real app (served by `POST /api/suggestions/preview`).
- AC3: Only true trust statements are shown; demo doctors are labelled fictional. No unverifiable security or credential badges, no invented testimonials.
- AC4: Logged-in users go straight to their dashboard.
- AC5: Severity, pain and day counts are entered as numbers, not sliders.

## US-25 Basal body temperature (Done)
As a user practising fertility awareness, I want to log my morning temperature and see when ovulation likely happened.
- AC1: The cycle form accepts an optional temperature from 35.0 to 38.5 °C; other values are rejected.
- AC2: A sustained rise (3-over-6 rule: three consecutive readings above the previous six, the third ≥ 0.2 °C above the highest of them) shows "ovulation likely happened just before" that date.
- AC3: Only readings since the current period start count; a missing day breaks the sequence.
- AC4: Whenever temperatures are shown, so is the warning that Her Aura is not a contraceptive. The app never shows "safe days".
- AC5: "Same as yesterday" never copies a temperature.

## US-26 Sleep (Done)
- AC1: Log hours (0-24) and quality (1-5) once per night; see a 7-night average.
- AC2: Wind-down routines are always available.
- AC3: In the estimated pre-period week (1-7 days before the expected period), a sleep tip is shown.

## US-27 Beginner mindfulness programme (Done)
- AC1: 7 short sessions; each day unlocks only after the previous one is completed; a day can't be completed twice.
- AC2: The current day has a timer and its steps; locked days show only their title.
- AC3: In the estimated pre-period week, an encouragement tip is shown.

## US-28 Runs, rides and outdoor workouts (Planned, see EXERCISES D3)
Log runs, rides, walks and outdoor workouts with distance and duration (pace calculated), weekly goals.
Community features (shared challenges, kudos) come later, opt-in only, never sharing health data.

## US-29 Digital contraception (Vision, regulated)
Only after regulatory clearance; see ROADMAP "Regulatory path". Until then, US-25 AC4 applies.

## US-30 Learn: featured articles (Done)
As a user, I want trustworthy, readable articles on women's health in one place.
- AC1: 10 featured articles are free for everyone: ovarian cysts, ovarian cancer symptoms, breast cancer, breast checks, PCOS, PMS, healthy diet, physical activity, mindfulness, five steps to wellbeing.
- AC2: Each article shows our own short summary and links to the original on WHO, NHS or ACOG. We never copy their text.
- AC3: Articles can be filtered by topic.
- AC4: Safety content (warning signs, screening) is marked "Always free" and can never be put behind the paywall, even by mistake.

## US-31 Monetization: Premium library and rewarded ads (Done, payments in demo mode)
- AC1: Library articles are locked for free users; their links are never sent to the browser while locked (HTTP 402 from the API).
- AC2: A free user can unlock one library article for 24 hours by watching an ad to the end (the server checks the watch time), up to 3 per day.
- AC3: Premium unlocks the whole library with no ads. In the demo, switching plans takes no payment.
- AC4: Ads are contextual (article topic) only; no health data is ever sent to an ad network.
- AC5: Tracking, suggestions, booking and all safety information stay free on every plan.

## US-32 Emotional load (Done)
As a user, I want to notice how I feel and what I'm carrying, so I can ask for help before I burn out.
- AC1: One check-in a day: mood 1-5, stress 1-10, energy 1-5, the areas weighing on me (work, household, caregiving, relationships, health, money, other), one thing I could hand off, private notes.
- AC2: A 14-day summary: averages, stress compared with the 14 days before, high-stress and low-mood day counts, top 3 load areas.
- AC3: Suggestions, most important first: low mood on 10+ of 14 days → talk to a doctor or counsellor (link to psychiatrists); stress ≥ 7 on 5+ days → mindfulness programme; top 2 load areas → hand-off tips that share the planning, not just the tasks.
- AC4: With cycle data (3+ check-ins in each group), stress in the pre-period week is compared with other days.
- AC5: Crisis support is always visible: 999, Kaan Pete Roi (09612-119911, 3pm-3am), findahelpline.com.
- AC6: Check-ins are private to the user.
