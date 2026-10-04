"""Server-rendered HTML pages. Every interactive element has a stable id or data-testid for automation."""

from datetime import date, datetime

from pathlib import Path

from urllib.parse import quote



from fastapi import APIRouter, Depends, Form, Request

from fastapi.responses import HTMLResponse, RedirectResponse

from fastapi.templating import Jinja2Templates

from sqlalchemy import func, select

from sqlalchemy.orm import Session



from app.db import get_db

from app.deps import optional_user

from app.models import Appointment, Doctor, EmotionalCheckIn, HealthIssueLog, MindfulnessSession, Slot, SleepLog, SymptomLog, User

from app.security import hash_password, verify_password

from app.services import articles, emotional_load, health_suggestions, learn_access, wellbeing
from app.routers.api import emotional_insights_for

from app.services.cycle import cycle_status

from app.services.daily_logs import LogError, copy_previous_day

from app.services.health_insights import build_insight

from app.services.scheduling import BookingError, book_slot, cancel_appointment



router = APIRouter()

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))





def _render(request: Request, name: str, user: User | None, **context):

    return templates.TemplateResponse(request, name, {"user": user, **context})





def _login_redirect():

    return RedirectResponse("/login", status_code=303)





@router.get("/", response_class=HTMLResponse)

def home(request: Request, user: User | None = Depends(optional_user), db: Session = Depends(get_db)):

    if user:

        return RedirectResponse("/dashboard", status_code=303)

    specialty_counts = db.execute(

        select(Doctor.specialty, func.count(Doctor.id)).group_by(Doctor.specialty).order_by(Doctor.specialty)

    ).all()

    return _render(request, "home.html", user, categories=health_suggestions.CATEGORIES,

                   specialty_counts=specialty_counts)





@router.get("/register", response_class=HTMLResponse)

def register_form(request: Request):

    return _render(request, "register.html", None)





@router.post("/register", response_class=HTMLResponse)

def register_submit(

    request: Request,

    full_name: str = Form(...), email: str = Form(...), password: str = Form(...),

    db: Session = Depends(get_db),

):

    email = email.strip().lower()

    error = None

    if len(full_name.strip()) < 2:

        error = "Please enter your full name."

    elif "@" not in email:

        error = "Please enter a valid email."

    elif len(password) < 8:

        error = "Password must be at least 8 characters."

    elif db.scalar(select(User).where(User.email == email)):

        error = "This email is already registered."

    if error:

        return _render(request, "register.html", None, error=error, full_name=full_name, email=email)



    user = User(email=email, full_name=full_name.strip(), password_hash=hash_password(password))

    db.add(user)

    db.commit()

    request.session["user_id"] = user.id

    return RedirectResponse("/dashboard", status_code=303)





@router.get("/login", response_class=HTMLResponse)

def login_form(request: Request):

    return _render(request, "login.html", None)





@router.post("/login", response_class=HTMLResponse)

def login_submit(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):

    user = db.scalar(select(User).where(User.email == email.strip().lower()))

    if user is None or not verify_password(password, user.password_hash):

        return _render(request, "login.html", None, error="Invalid email or password.", email=email)

    request.session["user_id"] = user.id

    return RedirectResponse("/dashboard", status_code=303)





@router.post("/logout")

def logout(request: Request):

    request.session.clear()

    return RedirectResponse("/", status_code=303)





@router.get("/dashboard", response_class=HTMLResponse)

def dashboard(request: Request, user: User | None = Depends(optional_user), db: Session = Depends(get_db)):

    if not user:

        return _login_redirect()

    logs = list(db.scalars(select(SymptomLog).where(SymptomLog.user_id == user.id).order_by(SymptomLog.log_date.desc())))

    issues = list(db.scalars(select(HealthIssueLog).where(HealthIssueLog.user_id == user.id)

                             .order_by(HealthIssueLog.log_date.desc(), HealthIssueLog.id.desc())))

    return _render(request, "dashboard.html", user, logs=logs[:14], insight=build_insight(logs, date.today()),

                   issues=issues[:10], suggestions=health_suggestions.suggest(issues, date.today()),

                   emergency_note=health_suggestions.EMERGENCY_NOTE, label=health_suggestions.label,

                   cycle=cycle_status(logs, date.today()))





@router.get("/health", response_class=HTMLResponse)

def health_form(request: Request, user: User | None = Depends(optional_user)):

    if not user:

        return _login_redirect()

    return _render(request, "health_log.html", user, today=date.today().isoformat(),

                   categories=health_suggestions.CATEGORIES)





@router.post("/health", response_class=HTMLResponse)

def health_submit(

    request: Request,

    log_date: date = Form(...), category: str = Form(...), severity: int = Form(...), notes: str = Form(""),

    user: User | None = Depends(optional_user), db: Session = Depends(get_db),

):

    if not user:

        return _login_redirect()

    error = None

    if category not in health_suggestions.CATEGORIES:

        error = "Please choose what you are feeling."

    elif not 1 <= severity <= 10:

        error = "Severity must be between 1 and 10."

    elif log_date > date.today():

        error = "You cannot log a future date."

    if error:

        return _render(request, "health_log.html", user, error=error, today=log_date.isoformat(),

                       categories=health_suggestions.CATEGORIES)

    db.add(HealthIssueLog(user_id=user.id, log_date=log_date, category=category, severity=severity, notes=notes[:1000]))

    db.commit()

    return RedirectResponse("/dashboard?saved=1", status_code=303)





@router.get("/log", response_class=HTMLResponse)

def log_form(request: Request, user: User | None = Depends(optional_user), db: Session = Depends(get_db)):

    if not user:

        return _login_redirect()

    return _render(request, "log_form.html", user, today=date.today().isoformat(),

                   error=request.query_params.get("error"))





@router.post("/log/same-as-yesterday")

def log_same_as_yesterday(user: User | None = Depends(optional_user), db: Session = Depends(get_db)):

    if not user:

        return _login_redirect()

    try:

        copy_previous_day(db, user.id, date.today())

    except LogError as e:

        return RedirectResponse(f"/log?error={quote(str(e))}", status_code=303)

    return RedirectResponse("/dashboard?saved=1", status_code=303)





@router.post("/log", response_class=HTMLResponse)

def log_submit(

    request: Request,

    log_date: date = Form(...),

    period_flow: str = Form("none"),

    pain_level: int = Form(0),

    pelvic_or_abdominal_pain: bool = Form(False),

    bloating: bool = Form(False),

    early_fullness: bool = Form(False),

    urinary_urgency: bool = Form(False),

    bbt_celsius: str = Form(""),

    notes: str = Form(""),

    user: User | None = Depends(optional_user),

    db: Session = Depends(get_db),

):

    if not user:

        return _login_redirect()

    error = None

    if log_date > date.today():

        error = "You cannot log a future date."

    elif not 0 <= pain_level <= 10:

        error = "Pain level must be between 0 and 10."

    elif period_flow not in ("none", "light", "medium", "heavy"):

        error = "Invalid period flow."

    bbt = None

    if not error and bbt_celsius.strip():

        try:

            bbt = float(bbt_celsius)

        except ValueError:

            bbt = -1

        if not 35.0 <= bbt <= 38.5:

            error = "Temperature must be between 35.0 and 38.5 °C."

    elif db.scalar(select(SymptomLog).where(SymptomLog.user_id == user.id, SymptomLog.log_date == log_date)):

        error = "You already have a log for this date."

    if error:

        return _render(request, "log_form.html", user, error=error, today=log_date.isoformat())



    db.add(SymptomLog(

        user_id=user.id, log_date=log_date, period_flow=period_flow, pain_level=pain_level,

        pelvic_or_abdominal_pain=pelvic_or_abdominal_pain, bloating=bloating,

        early_fullness=early_fullness, urinary_urgency=urinary_urgency, bbt_celsius=bbt, notes=notes[:1000],

    ))

    db.commit()

    return RedirectResponse("/dashboard?saved=1", status_code=303)





@router.get("/doctors", response_class=HTMLResponse)

def doctors(request: Request, user: User | None = Depends(optional_user), db: Session = Depends(get_db)):

    if not user:

        return _login_redirect()

    specialty = request.query_params.get("specialty") or None

    query = select(Doctor).order_by(Doctor.full_name)

    if specialty:

        query = query.where(Doctor.specialty == specialty)

    doctor_rows = list(db.scalars(query))

    specialties = sorted(set(db.scalars(select(Doctor.specialty))))

    slots = {

        d.id: list(db.scalars(

            select(Slot).where(Slot.doctor_id == d.id, Slot.is_booked.is_(False), Slot.starts_at > datetime.now())

            .order_by(Slot.starts_at).limit(6)

        ))

        for d in doctor_rows

    }

    return _render(request, "doctors.html", user, doctors=doctor_rows, slots=slots, specialties=specialties,

                   selected_specialty=specialty, error=request.query_params.get("error"))





@router.post("/appointments/book")

def book(request: Request, slot_id: int = Form(...), reason: str = Form(""),

         user: User | None = Depends(optional_user), db: Session = Depends(get_db)):

    if not user:

        return _login_redirect()

    try:

        book_slot(db, user.id, slot_id, reason[:255])

    except BookingError as e:

        return RedirectResponse(f"/doctors?error={quote(str(e))}", status_code=303)

    return RedirectResponse("/appointments?booked=1", status_code=303)





@router.get("/appointments", response_class=HTMLResponse)

def appointments(request: Request, user: User | None = Depends(optional_user), db: Session = Depends(get_db)):

    if not user:

        return _login_redirect()

    rows = list(db.scalars(select(Appointment).where(Appointment.patient_id == user.id).order_by(Appointment.id.desc())))

    return _render(request, "appointments.html", user, appointments=rows,

                   booked=request.query_params.get("booked"), error=request.query_params.get("error"))





@router.post("/appointments/{appointment_id}/cancel")

def cancel(appointment_id: int, user: User | None = Depends(optional_user), db: Session = Depends(get_db)):

    if not user:

        return _login_redirect()

    try:

        cancel_appointment(db, user.id, appointment_id)

    except BookingError as e:

        return RedirectResponse(f"/appointments?error={quote(str(e))}", status_code=303)

    return RedirectResponse("/appointments", status_code=303)





# ---------- Sleep ----------

@router.get("/sleep", response_class=HTMLResponse)

def sleep_page(request: Request, user: User | None = Depends(optional_user), db: Session = Depends(get_db)):

    if not user:

        return _login_redirect()

    nights = list(db.scalars(select(SleepLog).where(SleepLog.user_id == user.id).order_by(SleepLog.log_date.desc())))

    cycle_logs = list(db.scalars(select(SymptomLog).where(SymptomLog.user_id == user.id)))

    return _render(request, "sleep.html", user, nights=nights[:14], today=date.today().isoformat(),

                   summary=wellbeing.sleep_summary(nights, date.today()), wind_down=wellbeing.WIND_DOWN,

                   late_luteal=cycle_status(cycle_logs, date.today())["late_luteal"],

                   tip=wellbeing.LATE_LUTEAL_SLEEP_TIP, error=request.query_params.get("error"),

                   saved=request.query_params.get("saved"))





@router.post("/sleep")

def sleep_submit(log_date: date = Form(...), hours: float = Form(...), quality: int = Form(...), notes: str = Form(""),

                 user: User | None = Depends(optional_user), db: Session = Depends(get_db)):

    if not user:

        return _login_redirect()

    error = None

    if log_date > date.today():

        error = "You cannot log a future date."

    elif not 0 <= hours <= 24:

        error = "Hours must be between 0 and 24."

    elif not 1 <= quality <= 5:

        error = "Quality must be between 1 and 5."

    elif db.scalar(select(SleepLog.id).where(SleepLog.user_id == user.id, SleepLog.log_date == log_date)):

        error = "You already logged sleep for this date."

    if error:

        return RedirectResponse(f"/sleep?error={quote(error)}", status_code=303)

    db.add(SleepLog(user_id=user.id, log_date=log_date, hours=hours, quality=quality, notes=notes[:500]))

    db.commit()

    return RedirectResponse("/sleep?saved=1", status_code=303)





# ---------- Mindfulness ----------

@router.get("/mind", response_class=HTMLResponse)

def mind_page(request: Request, user: User | None = Depends(optional_user), db: Session = Depends(get_db)):

    if not user:

        return _login_redirect()

    done = set(db.scalars(select(MindfulnessSession.program_day).where(MindfulnessSession.user_id == user.id)))

    cycle_logs = list(db.scalars(select(SymptomLog).where(SymptomLog.user_id == user.id)))

    return _render(request, "mind.html", user, program=wellbeing.PROGRAM, done=done,

                   next_day=wellbeing.next_program_day(done),

                   late_luteal=cycle_status(cycle_logs, date.today())["late_luteal"],

                   tip=wellbeing.LATE_LUTEAL_MIND_TIP, error=request.query_params.get("error"))





@router.post("/mind/{day}/complete")

def mind_complete(day: int, user: User | None = Depends(optional_user), db: Session = Depends(get_db)):

    if not user:

        return _login_redirect()

    done = set(db.scalars(select(MindfulnessSession.program_day).where(MindfulnessSession.user_id == user.id)))

    if not wellbeing.can_complete(day, done):

        return RedirectResponse(f"/mind?error={quote('Complete the previous day first.')}", status_code=303)

    db.add(MindfulnessSession(user_id=user.id, program_day=day))

    db.commit()

    return RedirectResponse("/mind", status_code=303)



# ---------- Learn ----------
@router.get("/learn", response_class=HTMLResponse)
def learn(request: Request, user: User | None = Depends(optional_user), db: Session = Depends(get_db)):
    if not user:
        return _login_redirect()
    topic = request.query_params.get("topic") or None
    items = learn_access.catalogue(db, user, datetime.now())
    if topic:
        items = [a for a in items if a["topic"] == topic]
    return _render(request, "learn.html", user, featured=[a for a in items if a["tier"] == "free"],
                   library=[a for a in items if a["tier"] == "premium"], topics=articles.TOPICS, topic=topic,
                   ads_left=articles.MAX_AD_UNLOCKS_PER_DAY - learn_access.claimed_today(db, user.id, datetime.now()),
                   error=request.query_params.get("error"), unlocked=request.query_params.get("unlocked"))


@router.post("/learn/{slug}/ad/start")
def learn_ad_start(slug: str, user: User | None = Depends(optional_user), db: Session = Depends(get_db)):
    if not user:
        return _login_redirect()
    try:
        learn_access.start_ad(db, user, slug, datetime.now())
    except learn_access.AccessError as e:
        return RedirectResponse(f"/learn?error={quote(str(e))}", status_code=303)
    return RedirectResponse(f"/learn/{slug}/ad", status_code=303)


@router.get("/learn/{slug}/ad", response_class=HTMLResponse)
def learn_ad(slug: str, request: Request, user: User | None = Depends(optional_user)):
    if not user:
        return _login_redirect()
    article = articles.BY_SLUG.get(slug)
    if article is None:
        return RedirectResponse("/learn", status_code=303)
    return _render(request, "ad.html", user, article=article, seconds=articles.ad_seconds(),
                   error=request.query_params.get("error"))


@router.post("/learn/{slug}/ad/claim")
def learn_ad_claim(slug: str, user: User | None = Depends(optional_user), db: Session = Depends(get_db)):
    if not user:
        return _login_redirect()
    try:
        learn_access.claim_ad(db, user, slug, datetime.now())
    except learn_access.AccessError as e:
        return RedirectResponse(f"/learn/{slug}/ad?error={quote(str(e))}", status_code=303)
    return RedirectResponse(f"/learn?unlocked={slug}", status_code=303)


@router.get("/premium", response_class=HTMLResponse)
def premium(request: Request, user: User | None = Depends(optional_user)):
    if not user:
        return _login_redirect()
    return _render(request, "premium.html", user, premium_count=sum(1 for a in articles.ARTICLES if a["tier"] == "premium"),
                   max_ads=articles.MAX_AD_UNLOCKS_PER_DAY)


@router.post("/premium/{plan}")
def premium_switch(plan: str, user: User | None = Depends(optional_user), db: Session = Depends(get_db)):
    """DEMO ONLY: no payment is taken."""
    if not user:
        return _login_redirect()
    if plan in ("free", "premium"):
        user.plan = plan
        db.commit()
    return RedirectResponse("/learn" if plan == "premium" else "/premium", status_code=303)


# ---------- Emotional load ----------
@router.get("/load", response_class=HTMLResponse)
def load_page(request: Request, user: User | None = Depends(optional_user), db: Session = Depends(get_db)):
    if not user:
        return _login_redirect()
    history = list(db.scalars(select(EmotionalCheckIn).where(EmotionalCheckIn.user_id == user.id)
                              .order_by(EmotionalCheckIn.log_date.desc()).limit(14)))
    return _render(request, "load.html", user, areas=emotional_load.AREAS, today=date.today().isoformat(),
                   insight=emotional_insights_for(db, user.id), history=history, parse_areas=emotional_load.parse_areas,
                   error=request.query_params.get("error"), saved=request.query_params.get("saved"))


@router.post("/load")
async def load_submit(request: Request, user: User | None = Depends(optional_user), db: Session = Depends(get_db)):
    if not user:
        return _login_redirect()
    form = await request.form()
    try:
        log_date = date.fromisoformat(form.get("log_date", ""))
        mood, stress, energy = int(form.get("mood", 0)), int(form.get("stress", 0)), int(form.get("energy", 0))
    except ValueError:
        return RedirectResponse(f"/load?error={quote('Please fill in date, mood, stress and energy.')}", status_code=303)
    areas = [a for a in form.getlist("areas") if a in emotional_load.AREAS]
    error = None
    if log_date > date.today():
        error = "You cannot check in for a future date."
    elif not (1 <= mood <= 5 and 1 <= stress <= 10 and 1 <= energy <= 5):
        error = "Mood and energy are 1-5, stress is 1-10."
    elif db.scalar(select(EmotionalCheckIn.id).where(EmotionalCheckIn.user_id == user.id, EmotionalCheckIn.log_date == log_date)):
        error = "You already checked in for this date."
    if error:
        return RedirectResponse(f"/load?error={quote(error)}", status_code=303)
    db.add(EmotionalCheckIn(user_id=user.id, log_date=log_date, mood=mood, stress=stress, energy=energy,
                            areas=",".join(dict.fromkeys(areas)), handoff=str(form.get("handoff", ""))[:300],
                            notes=str(form.get("notes", ""))[:1000]))
    db.commit()
    return RedirectResponse("/load?saved=1", status_code=303)
