"""JSON API. The UI uses the same rules through app/services, so API tests cover the core logic."""
from datetime import date, datetime, timedelta
from types import SimpleNamespace

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import current_user
from app.models import Appointment, Doctor, EmotionalCheckIn, HealthIssueLog, MindfulnessSession, Slot, SleepLog, SymptomLog, User
from app.schemas import (
    AppointmentOut, ArticleOut, BookIn, EmotionalIn, EmotionalOut, PlanOut, CycleStatusOut, DoctorOut, MindfulnessProgressOut, SleepIn, SleepOut, HealthIssueIn, HealthIssueOut, InsightOut, LoginIn, RegisterIn,
    PreviewIn, SlotOut, SuggestionsOut, SymptomLogIn, SymptomLogOut, UserOut,
)
from app.security import hash_password, verify_password
from app.services.daily_logs import LogError, copy_previous_day
from app.services import emotional_load, health_suggestions, learn_access, wellbeing
from app.services.cycle import cycle_status, pre_period_days
from app.services.health_insights import period_start_dates
from app.services.health_insights import build_insight
from app.services.scheduling import BookingError, book_slot, cancel_appointment

router = APIRouter(prefix="/api")


def _user_out(user: User) -> UserOut:
    return UserOut(id=user.id, email=user.email, full_name=user.full_name, role=user.role)


def _appointment_out(a: Appointment) -> AppointmentOut:
    return AppointmentOut(
        id=a.id, status=a.status, reason=a.reason, starts_at=a.slot.starts_at,
        doctor_name=a.slot.doctor.full_name, clinic_name=a.slot.doctor.clinic.name,
    )


# ---------- Auth ----------
@router.post("/auth/register", status_code=201, response_model=UserOut)
def register(body: RegisterIn, request: Request, db: Session = Depends(get_db)):
    email = body.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(email=email, full_name=body.full_name.strip(), password_hash=hash_password(body.password))
    db.add(user)
    db.commit()
    request.session["user_id"] = user.id
    return _user_out(user)


@router.post("/auth/login", response_model=UserOut)
def login(body: LoginIn, request: Request, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    request.session["user_id"] = user.id
    return _user_out(user)


@router.post("/auth/logout", status_code=204)
def logout(request: Request):
    request.session.clear()


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return _user_out(user)


# ---------- Symptom logs ----------
@router.post("/logs", status_code=201, response_model=SymptomLogOut)
def create_log(body: SymptomLogIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if body.log_date > date.today():
        raise HTTPException(status_code=422, detail="Cannot log a future date")
    log = SymptomLog(user_id=user.id, **body.model_dump())
    db.add(log)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="A log already exists for this date")
    return SymptomLogOut(id=log.id, **body.model_dump())


@router.get("/logs", response_model=list[SymptomLogOut])
def list_logs(user: User = Depends(current_user), db: Session = Depends(get_db)):
    logs = db.scalars(select(SymptomLog).where(SymptomLog.user_id == user.id).order_by(SymptomLog.log_date.desc()))
    return [
        SymptomLogOut(id=l.id, **{k: getattr(l, k) for k in SymptomLogIn.model_fields})
        for l in logs
    ]


@router.post("/logs/copy-previous", status_code=201, response_model=SymptomLogOut)
def copy_previous(log_date: date | None = None, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """'Same as yesterday': copies the previous day's log onto log_date (default today)."""
    try:
        log = copy_previous_day(db, user.id, log_date or date.today())
    except LogError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return SymptomLogOut(id=log.id, **{k: getattr(log, k) for k in SymptomLogIn.model_fields})


@router.get("/insights", response_model=InsightOut)
def insights(user: User = Depends(current_user), db: Session = Depends(get_db)):
    logs = list(db.scalars(select(SymptomLog).where(SymptomLog.user_id == user.id)))
    return build_insight(logs, date.today())


# ---------- Health issues (headache, rash, toothache...) ----------
def _issue_out(i: HealthIssueLog) -> HealthIssueOut:
    return HealthIssueOut(id=i.id, log_date=i.log_date, category=i.category, severity=i.severity,
                          notes=i.notes, label=health_suggestions.label(i.category))


@router.get("/health-issues/categories")
def issue_categories():
    return [{"key": k, "label": v[0], "specialty": v[1]} for k, v in health_suggestions.CATEGORIES.items()]


@router.post("/health-issues", status_code=201, response_model=HealthIssueOut)
def create_issue(body: HealthIssueIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if body.category not in health_suggestions.CATEGORIES:
        raise HTTPException(status_code=422, detail="Unknown category")
    if body.log_date > date.today():
        raise HTTPException(status_code=422, detail="Cannot log a future date")
    issue = HealthIssueLog(user_id=user.id, **body.model_dump())
    db.add(issue)
    db.commit()
    return _issue_out(issue)


@router.get("/health-issues", response_model=list[HealthIssueOut])
def list_issues(category: str | None = None, user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = select(HealthIssueLog).where(HealthIssueLog.user_id == user.id)
    if category:
        query = query.where(HealthIssueLog.category == category)
    return [_issue_out(i) for i in db.scalars(query.order_by(HealthIssueLog.log_date.desc(), HealthIssueLog.id.desc()))]


@router.get("/suggestions", response_model=SuggestionsOut)
def suggestions(user: User = Depends(current_user), db: Session = Depends(get_db)):
    logs = list(db.scalars(select(HealthIssueLog).where(HealthIssueLog.user_id == user.id)))
    return {"suggestions": health_suggestions.suggest(logs, date.today()),
            "emergency_note": health_suggestions.EMERGENCY_NOTE, "disclaimer": health_suggestions.DISCLAIMER}


@router.post("/suggestions/preview", response_model=SuggestionsOut)
def suggestions_preview(body: PreviewIn):
    """Public 'try it' endpoint for the home page: runs the real rules on a hypothetical history.
    Nothing is saved and no login is needed."""
    today = date.today()
    logs = []
    for issue in body.issues:
        if issue.category not in health_suggestions.CATEGORIES:
            raise HTTPException(status_code=422, detail=f"Unknown category: {issue.category}")
        # Most recent day carries the chosen severity; earlier days spread back over the 14-day window.
        for d in range(issue.days):
            logs.append(SimpleNamespace(category=issue.category, severity=issue.severity, log_date=today - timedelta(days=d)))
    return {"suggestions": health_suggestions.suggest(logs, today),
            "emergency_note": health_suggestions.EMERGENCY_NOTE, "disclaimer": health_suggestions.DISCLAIMER}


# ---------- Cycle status (BBT) ----------
@router.get("/cycle/status", response_model=CycleStatusOut)
def get_cycle_status(user: User = Depends(current_user), db: Session = Depends(get_db)):
    logs = list(db.scalars(select(SymptomLog).where(SymptomLog.user_id == user.id)))
    return cycle_status(logs, date.today())


# ---------- Sleep ----------
@router.post("/sleep", status_code=201, response_model=SleepOut)
def log_sleep(body: SleepIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if body.log_date > date.today():
        raise HTTPException(status_code=422, detail="Cannot log a future date")
    entry = SleepLog(user_id=user.id, **body.model_dump())
    db.add(entry)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Sleep already logged for this date")
    return SleepOut(id=entry.id, **body.model_dump())


@router.get("/sleep", response_model=list[SleepOut])
def list_sleep(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(SleepLog).where(SleepLog.user_id == user.id).order_by(SleepLog.log_date.desc()))
    return [SleepOut(id=r.id, log_date=r.log_date, hours=r.hours, quality=r.quality, notes=r.notes) for r in rows]


# ---------- Mindfulness programme ----------
def _completed_days(db: Session, user_id: int) -> set[int]:
    return set(db.scalars(select(MindfulnessSession.program_day).where(MindfulnessSession.user_id == user_id)))


@router.get("/mindfulness/progress", response_model=MindfulnessProgressOut)
def mindfulness_progress(user: User = Depends(current_user), db: Session = Depends(get_db)):
    done = _completed_days(db, user.id)
    return {"completed_days": sorted(done), "next_day": wellbeing.next_program_day(done), "total_days": wellbeing.PROGRAM_DAYS}


@router.post("/mindfulness/{day}/complete", response_model=MindfulnessProgressOut)
def complete_mindfulness_day(day: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    done = _completed_days(db, user.id)
    if not wellbeing.can_complete(day, done):
        raise HTTPException(status_code=409, detail="Complete the previous day first, or this day is already done")
    db.add(MindfulnessSession(user_id=user.id, program_day=day))
    db.commit()
    done.add(day)
    return {"completed_days": sorted(done), "next_day": wellbeing.next_program_day(done), "total_days": wellbeing.PROGRAM_DAYS}


# ---------- Learn: articles, plan, rewarded ads ----------
def _article_out(a: dict) -> ArticleOut:
    return ArticleOut(**{k: a[k] for k in ArticleOut.model_fields})


@router.get("/articles", response_model=list[ArticleOut])
def list_articles(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return [_article_out(a) for a in learn_access.catalogue(db, user, datetime.now())]


@router.get("/articles/{slug}", response_model=ArticleOut)
def get_article(slug: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    article = next((a for a in learn_access.catalogue(db, user, datetime.now()) if a["slug"] == slug), None)
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    if not article["unlocked"]:
        raise HTTPException(status_code=402, detail="Premium article: subscribe or watch an ad to unlock")
    return _article_out(article)


@router.post("/articles/{slug}/ad/start", status_code=201)
def start_ad(slug: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    try:
        learn_access.start_ad(db, user, slug, datetime.now())
    except learn_access.AccessError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return {"status": "playing"}


@router.post("/articles/{slug}/ad/claim", response_model=ArticleOut)
def claim_ad(slug: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    try:
        learn_access.claim_ad(db, user, slug, datetime.now())
    except learn_access.AccessError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return get_article(slug, user, db)


@router.get("/plan", response_model=PlanOut)
def get_plan(user: User = Depends(current_user)):
    return {"plan": user.plan}


@router.post("/plan/{plan}", response_model=PlanOut)
def set_plan(plan: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """DEMO ONLY: switches plan without payment. Real payments: see docs/EXERCISES.md (F1)."""
    if plan not in ("free", "premium"):
        raise HTTPException(status_code=422, detail="Unknown plan")
    user.plan = plan
    db.commit()
    return {"plan": user.plan}


# ---------- Emotional load ----------
def _emotional_out(c: EmotionalCheckIn) -> EmotionalOut:
    return EmotionalOut(id=c.id, log_date=c.log_date, mood=c.mood, stress=c.stress, energy=c.energy,
                        areas=emotional_load.parse_areas(c.areas), handoff=c.handoff, notes=c.notes)


@router.post("/emotional", status_code=201, response_model=EmotionalOut)
def create_checkin(body: EmotionalIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if body.log_date > date.today():
        raise HTTPException(status_code=422, detail="Cannot log a future date")
    unknown = [a for a in body.areas if a not in emotional_load.AREAS]
    if unknown:
        raise HTTPException(status_code=422, detail=f"Unknown area: {unknown[0]}")
    checkin = EmotionalCheckIn(user_id=user.id, log_date=body.log_date, mood=body.mood, stress=body.stress,
                               energy=body.energy, areas=",".join(dict.fromkeys(body.areas)),
                               handoff=body.handoff, notes=body.notes)
    db.add(checkin)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="You already checked in for this date")
    return _emotional_out(checkin)


@router.get("/emotional", response_model=list[EmotionalOut])
def list_checkins(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(EmotionalCheckIn).where(EmotionalCheckIn.user_id == user.id).order_by(EmotionalCheckIn.log_date.desc()))
    return [_emotional_out(c) for c in rows]


def emotional_insights_for(db: Session, user_id: int) -> dict:
    checkins = list(db.scalars(select(EmotionalCheckIn).where(EmotionalCheckIn.user_id == user_id)))
    cycle_logs = list(db.scalars(select(SymptomLog).where(SymptomLog.user_id == user_id)))
    starts = period_start_dates(cycle_logs)
    next_period = cycle_status(cycle_logs, date.today())["next_period"]
    return emotional_load.insights(checkins, date.today(), pre_period_days(starts, next_period) if starts else None)


@router.get("/emotional/insights")
def emotional_insights(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return emotional_insights_for(db, user.id)


# ---------- Doctors & booking ----------
@router.get("/doctors", response_model=list[DoctorOut])
def list_doctors(specialty: str | None = None, db: Session = Depends(get_db)):
    query = select(Doctor).order_by(Doctor.full_name)
    if specialty:
        query = query.where(Doctor.specialty == specialty)
    return [
        DoctorOut(id=d.id, full_name=d.full_name, specialty=d.specialty,
                  clinic_name=d.clinic.name, clinic_address=d.clinic.address)
        for d in db.scalars(query)
    ]


@router.get("/doctors/{doctor_id}/slots", response_model=list[SlotOut])
def open_slots(doctor_id: int, db: Session = Depends(get_db)):
    if db.get(Doctor, doctor_id) is None:
        raise HTTPException(status_code=404, detail="Doctor not found")
    slots = db.scalars(
        select(Slot)
        .where(Slot.doctor_id == doctor_id, Slot.is_booked.is_(False), Slot.starts_at > datetime.now())
        .order_by(Slot.starts_at)
    )
    return [SlotOut(id=s.id, doctor_id=s.doctor_id, starts_at=s.starts_at, duration_minutes=s.duration_minutes) for s in slots]


@router.post("/appointments", status_code=201, response_model=AppointmentOut)
def book(body: BookIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    try:
        appointment = book_slot(db, user.id, body.slot_id, body.reason)
    except BookingError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return _appointment_out(appointment)


@router.get("/appointments", response_model=list[AppointmentOut])
def my_appointments(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(Appointment).where(Appointment.patient_id == user.id).order_by(Appointment.id.desc()))
    return [_appointment_out(a) for a in rows]


@router.post("/appointments/{appointment_id}/cancel", response_model=AppointmentOut)
def cancel(appointment_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    try:
        appointment = cancel_appointment(db, user.id, appointment_id)
    except BookingError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return _appointment_out(appointment)
