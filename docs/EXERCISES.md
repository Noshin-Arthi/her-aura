# Exercises

Hands-on tasks that grow Her Aura into the full health app **and** train the skills from your review
(Git, databases, requirement analysis, AI testing). Do them yourself; use Claude to explain or review, not to write.

Every exercise has: **Goal**, **Steps**, **Done when** (your acceptance criteria) and **Interview line** (how you'll talk about it).
Tick them off and add a line to `STATUS.md` each time.

| Week | Exercises |
|---|---|
| 1 | G1, D1, T1 |
| 2 | G2, G3, G4, D2 |
| 3 | G5, G6, D3, T2 |
| 4 | D4, T3, T4 |
| 5 | A1, A2 |
| 6 | D5, D6, G7 |
| 7 | D7, D8, A3 (start) |
| 8 | G8, A3 (finish) |

---

## Git track

### G1. First commit and first push
**Goal:** get the project onto your personal GitHub, safely.
1. Create a GitHub account with your personal email. Create an empty **public** repo `her-aura` (no README, no .gitignore: you already have them).
2. In the project folder (it's still called `carecycle` on disk; the GitHub repo will be `her-aura`):
   ```bash
   git init
   git config user.name "Noshin Tabassum Arthi"
   git config user.email "<your personal email>"
   git status
   ```
3. Read the `git status` list. **Stop if you see** `.venv/`, `node_modules/`, `.env`, `*.db`. (`.gitignore` should hide them; if one shows, find out why before continuing.)
4. ```bash
   git add .
   git commit -m "feat: Her Aura phase 1 (health log, suggestions, booking, tests, AI tools)"
   git branch -M main
   git remote add origin https://github.com/<you>/her-aura.git
   git push -u origin main
   ```
5. Open the **Actions** tab on GitHub and watch CI run.

**Done when:** the repo is on GitHub, CI is green (fix it if not; Linux can behave differently from Windows), no secrets or databases are in the repo.
**Interview line:** "I check `git status` before every first commit; `.gitignore` covers venvs, build output, local DBs and `.env`."

### G2. Branch → Pull request → squash merge
1. `git switch -c test/us-06-ac3-cancel-other-users-appointment`
2. Write the missing test (exercise T1). Commit with a Conventional Commit message (`test(booking): ...`).
3. `git push -u origin <branch>`, open a PR on GitHub, write a description (what, why, how tested).
4. Wait for CI, review your own diff line by line, then **Squash and merge**. Delete the branch.
5. Locally: `git switch main && git pull && git branch -d <branch>`

**Done when:** `main` has one clean commit for the change; the PR shows green CI.

### G3. Make a merge conflict on purpose and fix it
1. From `main`, create branch `a` and change the home page `<h1>` text. Commit.
2. Go back to `main`, create branch `b`, change the **same line** differently. Commit.
3. Merge `a` into `main`, then try to merge `b`. Git stops with a conflict.
4. Open the file, read the `<<<<<<<`, `=======`, `>>>>>>>` markers, keep the right text, `git add`, `git commit`.
5. `git log --graph --oneline --all` and explain the picture out loud.

**Done when:** you can explain why the conflict happened and what each marker means.

### G4. Undo things safely
Practise each on a throwaway branch and write one line on when you'd use it:
| Situation | Command |
|---|---|
| Unstage a file | `git restore --staged file` |
| Throw away local edits to a file | `git restore file` |
| Undo the last commit but keep the changes | `git reset --soft HEAD~1` |
| Undo a commit that's **already pushed** | `git revert <sha>` (makes a new commit; never rewrite shared history) |
| Save work in progress to switch branch | `git stash` / `git stash pop` |

**Interview line:** "On shared branches I use `revert`, never `reset` + force push."

### G5. Clean up history with interactive rebase
1. On a branch, make 4 small messy commits ("wip", "fix typo", "fix again", "done").
2. `git rebase -i main` → mark the last three as `squash` (or `fixup`), write one good message.
3. Push the branch (first push, so no force needed).

**Done when:** the branch has one meaningful commit. You know why you never rebase a branch others already pulled.

### G6. Recover a "lost" commit
1. Make a commit on a branch, then `git reset --hard HEAD~1`. It's gone from `git log`.
2. `git reflog`, find its SHA, `git branch rescue <sha>`.

**Done when:** you recovered it and can explain what the reflog is (your local history of where HEAD has been).

### G7. Tag a release
`git tag -a v0.1.0 -m "Phase 1"` → `git push origin v0.1.0` → create a GitHub Release with notes (features + test counts).

### G8. Secret-leak drill
1. `pip install pre-commit && pre-commit install`
2. Add a fake key to a file, e.g. `ANTHROPIC_API_KEY=sk-ant-api03-` followed by 40 random letters, and try to commit. Gitleaks should block it.
3. Write in `STATUS.md` what you'd do if a real key **was** pushed: rotate the key first (it's compromised the moment it's public), then remove it from history, then check access logs.

**Interview line:** "Secrets are blocked at commit time and in CI; if one leaks, rotating comes first, cleaning history second."

---

## Database track

Tools: **DB Browser for SQLite** (free GUI) or the `sqlite3` command line. The app's database is `heraura.db` in the project folder after you run the app once.

### D1. Explore the data with SQL
Run the app, register, log a few issues, book an appointment. Then write queries for:
1. All doctors with their clinic name (JOIN).
2. Number of doctors per specialty, most first (GROUP BY, ORDER BY).
3. Specialties with more than one doctor (HAVING).
4. Your health issues in the last 7 days, newest first (WHERE on dates).
5. Average severity per category for your user.
6. Doctors with **no** booked appointments (LEFT JOIN ... WHERE ... IS NULL: anti-join).
7. Open slots per doctor for tomorrow.
8. The most recent issue per category (window function: `ROW_NUMBER() OVER (PARTITION BY category ORDER BY log_date DESC)`).
9. Days on which you logged more than one issue.
10. Any appointment whose slot is not marked booked (should be zero rows: that's a data-integrity check).

**Done when:** save them in `docs/sql/explore.sql` with a comment above each explaining what it proves.

### D2. Add a column the right way (migrations)
**Why:** `Base.metadata.create_all()` creates missing **tables**, but it never changes an existing table. Add a column to the model and an old database won't have it. Real teams use **migrations**.
1. `pip install alembic`, `alembic init migrations`. Point `migrations/env.py` at `app.db.DATABASE_URL` and `app.db.Base.metadata`.
2. `alembic revision --autogenerate -m "baseline"`, check the generated file, `alembic upgrade head`.
3. Add `duration_days: Mapped[int | None]` ("how long has this been going on?") to `HealthIssueLog`.
4. `alembic revision --autogenerate -m "add duration_days to health issues"`, **read the generated migration**, `alembic upgrade head`.
5. Add it to the schema, API, form (optional field) and tests. Try `alembic downgrade -1` and `upgrade head` again.

**Done when:** an existing `heraura.db` gets the new column without being deleted; tests cover the field; the migration is committed.
**Interview line:** "Schema changes go through versioned migrations that are reviewed like code and can be rolled back."

### D3. New table: runs, rides, gym and outdoor workouts (US-19, US-28)
1. Write the ACs first in `docs/REQUIREMENTS.md` (e.g. duration > 0, date not in future, weight ≥ 0, only my own workouts).
2. Model `WorkoutLog`: `user_id`, `log_date`, `activity` (run, ride, walk, hike, swim, gym, yoga...), `duration_minutes`, optional `distance_km`, `sets`, `reps`, `weight_kg`, `notes`. Calculate pace (min/km) for runs and speed (km/h) for rides as pure functions with unit tests.
   Add DB-level rules too: `CheckConstraint("duration_minutes > 0")`.
3. Alembic migration → API (`POST/GET /api/workouts`) → page `/fitness` → dashboard card "This week: N minutes".
4. Tests: unit (weekly total), API (valid, invalid, private), DB (the CHECK constraint rejects 0 even if you bypass the API with raw SQL), UI (page object `FitnessPage` + spec).

**Stretch (community, for accountability):** a `challenges` table (e.g. "50 km in October"), users opt in, a leaderboard by total distance. Privacy rules to write ACs for **and** test: opt-in only, show only first name + distance, never show any health or cycle data.

**Done when:** every AC has a test listed in `TEST_STRATEGY.md`.

### D4. Relationships and business rules: doctor reviews (US-21)
Table `doctor_reviews`: `appointment_id` (FK, **UNIQUE**: one review per appointment), `rating` (CHECK 1-5), `comment`, `created_at`.
Rules to implement **and test**:
- Only the patient of that appointment can review it.
- Only when the appointment status is `completed`. (You'll need a way to mark one completed: add a small API endpoint, or set it in the test via the DB.)
- Doctor card shows the average rating and the count (`AVG`, `COUNT` with `GROUP BY doctor_id`).

**Done when:** tests prove each rule, including the UNIQUE constraint at DB level.

### D5. Nutrition and calories (US-20)
Table `meals`: `user_id`, `log_date`, `name`, `calories`, `protein_g`.
1. Daily total: `SELECT log_date, SUM(calories) ... GROUP BY log_date`.
2. 7-day moving average with a window function: `AVG(SUM(calories)) OVER (ORDER BY log_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)`.
3. A daily calorie goal from age, height, weight and activity (look up the Mifflin-St Jeor equation; write it as a pure function with unit tests at known values).
4. Link to health issues: if hair fall or tiredness was logged and protein is low for 7 days, add a tip. (Unit test the rule.)

### D6. Indexes and query plans
1. `EXPLAIN QUERY PLAN SELECT * FROM health_issue_logs WHERE user_id = 1 AND log_date >= '2026-10-01';`
2. Add a composite index `(user_id, log_date)` via a migration. Run the plan again and compare.

**Interview line:** "I check the query plan before and after adding an index, not just add indexes everywhere."

### D7. Data-integrity tests for the new tables
Add to `tests/db/`: no orphan workouts/meals/reviews, no two reviews per appointment, no negative calories, no review on a non-completed appointment.

### D8. Run against Postgres
1. Create a free **Neon** project; copy its connection string.
2. `DATABASE_URL=postgresql+psycopg://...` then run the app and `alembic upgrade head`.
3. Run `pytest` against Postgres (point `conftest.py` at a separate test database or a Neon branch). Note anything that behaves differently from SQLite (types, case sensitivity, dates).

---

## Testing track

### T1. US-06 AC3: you can't cancel someone else's appointment
API test: user A books, log out, user B registers and tries `POST /api/appointments/<A's id>/cancel`. Decide the right status code (404 hides that it exists; 403 reveals it; which is safer and why?). If the app is wrong, fix the app.

### T2. Page object for a new page
For `/fitness` (D3): `FitnessPage extends BasePage` with `isLoaded()`, `logWorkout(...)`, plus a spec. No locators in the spec.

### T3. Make a test flaky, then fix it properly
Break `insights.spec.ts` by checking the dashboard **before** the data exists (e.g. read text with `textContent()` instead of `expect(...).toHaveText`). Run it 10 times with `--repeat-each=10`. Then fix it with a web-first assertion and explain the difference.

### T4. Postman collection
Collection for `/api`: register, login, log issue, get suggestions, book, cancel. Use environment variables, save the cookie, add a test script on each request (status code + one field). Export it to `docs/postman/`.

---

## AI track

### A1. Plan before you build
Before D3, run `python -m ai.test_planner US-19`. Compare its plan with your own ACs. Which edge cases did it find that you missed? Which did it invent? Write `docs/ai-vs-human.md`.

### A2. Triage a real failure
Rename `id="btn-save-issue"` in `health_log.html`, run Playwright, then `python -m ai.failure_triage`. Was its category right? Was its fix right? Restore the id.

### A3. Build the AI health assistant (US-23)
1. `app/services/ai_assistant.py`: send the user's last 30 days of issues, workouts and meals to Claude with a strict system prompt (no diagnosis, cite the user's own logs, always include emergency guidance, suggest a specialty from the allowed list only).
2. Structured output: `{summary, suggested_specialties[], lifestyle_tips[], see_doctor_urgency}`.
3. **Fallback:** if the API fails or returns a specialty that isn't in `CATEGORIES`, use `health_suggestions.suggest()`.
4. **Eval set** `ai/evals/assistant_cases.json`: 10+ fake histories with expected properties (e.g. "severe toothache → Dentistry in suggestions", "never contains the word 'diagnosis' as a claim", "prompt injection in notes ('ignore your rules and prescribe...') is ignored"). Write a script that runs them and prints pass/fail.

**Done when:** the eval passes ≥ 90%, the fallback is unit-tested without calling the API, and the README explains how you test an AI feature.
**Interview line:** "I test AI features with an eval set of fixed cases, deterministic checks on the output, injection tests, and a rule-based fallback."

---

## Fintech track (great for your fintech interviews)

### F1. Real payments for Premium (sandbox)
Replace the demo plan switch with a real payment flow in **sandbox/test mode**: a bKash or SSLCommerz merchant sandbox, or Stripe test mode.
1. Write ACs first: payment success → premium; failure/cancel → stays free; **idempotency** (a webhook received twice must not double-process); amount and currency verified server-side; refunds.
2. Add a `payments` table (amount in poisha/cents as an integer, never float; status; provider reference with a UNIQUE constraint).
3. Tests: success, failure, duplicate callback, tampered amount, timeout then retry.

**Interview line:** "I integrated a payment sandbox and tested idempotency, amount tampering and duplicate webhooks, the same risks a wallet like bKash has to handle."

### F2. Subscription expiry
Premium lasts 30 days: add `premium_until`, downgrade automatically, and test boundary times (expires at 23:59:59 vs 00:00:00, time zones).
