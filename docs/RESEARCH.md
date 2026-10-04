# Research notes

Why each Her Aura feature exists, what the evidence actually says, and where the line is.
Market scan source: Solu, ["Top 10 Health and Fitness Apps for Women"](https://www.solu.ae/blog/top-10-health-and-fitness-apps-for-women) (2026). That article cites no studies, so every claim below was checked separately.

## Market scan (from the Solu article)

| App | Category | What it's known for | What Her Aura takes from it |
|---|---|---|---|
| Solu | Cycle-aware wellness | Movement, nutrition, sleep and energy guidance mapped to cycle phase | The overall idea: one app, every health area, cycle-aware |
| Clue | Period tracking | Symptom tracking that improves predictions over time | Cycle log, period predictions |
| Natural Cycles | Fertility / contraception | BBT confirms ovulation and predicts fertile days; certified digital contraceptive | BBT logging + retrospective ovulation confirmation (**not** contraception, see below) |
| MyFitnessPal | Nutrition | Large food database, calories and macros | Nutrition module (planned, US-20) |
| Cronometer | Micronutrients | Iron, magnesium, vitamin D, B12 | Micronutrient focus for women (planned) |
| Strava | Endurance / social | Runs, rides, outdoor workouts; community for accountability | Fitness module (planned, US-19, US-28) |
| Nike Training Club | Workouts | Structured, mostly free programmes | Structured programme idea (used for Mind) |
| Oura | Sleep / recovery (ring) | Sleep, recovery, skin temperature | Sleep log; wearable import later |
| Headspace | Mindfulness | Structured beginner mindfulness | 7-day beginner programme (US-27) |
| Calm | Sleep / relaxation | Sleep stories, relaxation | Wind-down routines + pre-period sleep tip (US-26) |

## Evidence by feature

### Basal body temperature (BBT) and contraception
- After ovulation, progesterone raises BBT by roughly 0.2-0.5 °C. The **"3 over 6" rule** (Marshall, 1968): three consecutive readings above the previous six, the third at least 0.2 °C above the highest of the six, confirms ovulation **after** it happened. ([overview](https://unanswered.io/guide/what-is-the-3-over-6-rule-for-ovulation), [wearables study, PMC6265623](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6265623/))
- Natural Cycles is an FDA De Novo **Class II medical device**, cleared in 2018 as the first app for birth control in the US. Its study covered 22,785 women and 224,563 cycles: 1.8% perfect-use and 6.5% typical-use failure rates (about 93% effective with typical use). ([MobiHealthNews](https://www.mobihealthnews.com/content/fda-grants-natural-cycles-contraception-app-de-novo-marketing-approval), [BioSpace](https://www.biospace.com/us-food-and-drug-administration-fda-clears-natural-cycles-as-the-first-digital-method-of-birth-control-in-the-united-states))
- **Decision:** Her Aura confirms ovulation after the fact and **never shows "safe days"**. Marketing an app as contraception without clearance would be illegal in regulated markets and could cause unintended pregnancies. See the regulatory path in `ROADMAP.md`.

### Sleep in the late luteal phase
- Sleep disturbance is more commonly reported in the last premenstrual days and early menstruation, especially by women with PMS or painful cramps. Patterns vary between individuals, and in severe PMS, *perceived* sleep quality drops without matching changes in lab-measured sleep. ([Baker & Driver review, PMC2817387](https://pmc.ncbi.nlm.nih.gov/articles/PMC2817387/), [AASM summary](https://aasm.org/new-study-in-the-journal-sleep-finds-that-women-with-severe-pms-perceive-their-sleep-quality-to-be-poor/))
- **Decision:** a gentle "many people sleep worse this week" tip in the estimated pre-period week. We say "many people", not "your sleep will drop".

### Mindfulness and PMS
- Randomized trials found that 8-week mindfulness programmes (MBCT, MBSR) reduced premenstrual symptoms compared with no intervention, in samples of 60-90 students. Researchers note the evidence base is still small. ([MBSR RCT, PubMed 37335817](https://pubmed.ncbi.nlm.nih.gov/37335817/), [MBCT data](https://womensmentalhealth.org/posts/preliminary-data-supporting-the-use-of-mindfulness-based-cognitive-therapy-for-premenstrual-symptoms/))
- **Decision:** Her Aura says "small studies link mindfulness training to fewer premenstrual symptoms". We don't claim "research consistently shows" or "lowers cortisol"; we didn't verify those.

### Symptom red flags (cycle module)
- Goff Ovarian Cancer Symptom Index: pelvic/abdominal pain, bloating or early fullness on 12+ days a month (for under a year) is a reason to see a doctor. ([PMC2736546](https://pmc.ncbi.nlm.nih.gov/articles/PMC2736546))

### Health content: sources and copyright
- Featured and library articles link to **WHO fact sheets, NHS pages and ACOG FAQs**. We write our own 1-2 sentence summaries and never copy their text. All links were checked (HTTP 200) on 2026-10-04; re-check them regularly (exercise idea: an automated link checker in CI).

### Monetization and privacy
- In 2021 the US Federal Trade Commission (FTC) finalized an order against **Flo Health**. It said Flo shared sensitive health data (including pregnancy) with Facebook, Google and other analytics firms despite promising privacy. Flo now needs users' affirmative consent before sharing, and independent privacy reviews. ([Healthcare IT Today](https://www.healthcareittoday.com/2021/01/14/ftc-settlement-with-fertility-tracking-app-maker-flo-health-over-data-disclosure-allegations/), [Bitdefender summary](https://www.bitdefender.com/en-us/blog/hotforsecurity/ftc-orders-popular-womens-fertility-predictor-app-to-stop-misleading-users-about-health-info-shared-with-data-analytics-providers))
- **Decision:** ads are contextual only (article topic), never targeted on health data; safety information is never paywalled.

### Emotional load
- Sociologist Allison Daminger describes household **cognitive labour** as anticipating needs, researching options, deciding and monitoring, and finds women in different-gender couples do most of it, even when couples aim for equality. ([Radcliffe Institute](https://www.radcliffe.harvard.edu/news-and-ideas/the-unseen-inequity-of-cognitive-labor), [Princeton University Press](https://press.princeton.edu/isbn/9780691283142))
- **Decision:** track *where* the load comes from, and give hand-off tips that move whole responsibilities (including the planning), not single chores.
- The reference [Belle article](https://bellehealth.co/best-apps-for-womens-health-content-2025/) frames mental health as part of hormonal health; we compare stress in the pre-period week with other days.
- **Crisis support:** Kaan Pete Roi, Bangladesh's first emotional-support and suicide-prevention helpline, 09612-119911, 3pm-3am daily, free. ([Find A Helpline](https://findahelpline.com/organizations/kaan-pete-roi)). The "low mood on most days for two weeks" threshold mirrors common depression-screening wording; it prompts a conversation with a professional, never a diagnosis.

## Wording rules (enforced by tests where possible)
1. Never "diagnose", never "safe days", never a probability of disease.
2. Health claims say how strong the evidence is ("small studies", "many people").
3. Competitor names appear only in this research file, never in the product.
4. No made-up badges, testimonials or certifications.
