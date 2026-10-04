"""Request/response shapes for the JSON API (validated by Pydantic)."""

from datetime import date, datetime

from typing import Literal



from pydantic import BaseModel, EmailStr, Field





class RegisterIn(BaseModel):

    email: EmailStr

    full_name: str = Field(min_length=2, max_length=120)

    password: str = Field(min_length=8, max_length=128)





class LoginIn(BaseModel):

    email: EmailStr

    password: str





class UserOut(BaseModel):

    id: int

    email: str

    full_name: str

    role: str





class SymptomLogIn(BaseModel):

    log_date: date

    period_flow: Literal["none", "light", "medium", "heavy"] = "none"

    pain_level: int = Field(ge=0, le=10, default=0)

    pelvic_or_abdominal_pain: bool = False

    bloating: bool = False

    early_fullness: bool = False

    urinary_urgency: bool = False

    bbt_celsius: float | None = Field(default=None, ge=35.0, le=38.5, description="Basal body temperature in °C")

    notes: str = Field(default="", max_length=1000)





class SymptomLogOut(SymptomLogIn):

    id: int





class DoctorOut(BaseModel):

    id: int

    full_name: str

    specialty: str

    clinic_name: str

    clinic_address: str





class SlotOut(BaseModel):

    id: int

    doctor_id: int

    starts_at: datetime

    duration_minutes: int





class BookIn(BaseModel):

    slot_id: int

    reason: str = Field(default="", max_length=255)





class AppointmentOut(BaseModel):

    id: int

    status: str

    reason: str

    starts_at: datetime

    doctor_name: str

    clinic_name: str





class InsightOut(BaseModel):

    days_logged: int

    symptom_days: int

    window_days: int

    threshold_days: int

    average_cycle_length: float | None

    red_flag: bool

    message: str

    disclaimer: str





class HealthIssueIn(BaseModel):

    log_date: date

    category: str = Field(description="One of app.services.health_suggestions.CATEGORIES")

    severity: int = Field(ge=1, le=10)

    notes: str = Field(default="", max_length=1000)





class HealthIssueOut(HealthIssueIn):

    id: int

    label: str





class SuggestionOut(BaseModel):

    category: str

    label: str

    specialty: str

    urgency: Literal["soon", "routine"]

    reason: str

    tips: list[str]





class SuggestionsOut(BaseModel):

    suggestions: list[SuggestionOut]

    emergency_note: str

    disclaimer: str





class PreviewIssue(BaseModel):

    category: str

    severity: int = Field(ge=1, le=10)

    days: int = Field(ge=1, le=14, description="On how many of the last 14 days it happened")





class PreviewIn(BaseModel):

    issues: list[PreviewIssue] = Field(min_length=1, max_length=10)





class SleepIn(BaseModel):

    log_date: date

    hours: float = Field(ge=0, le=24)

    quality: int = Field(ge=1, le=5)

    notes: str = Field(default="", max_length=500)





class SleepOut(SleepIn):

    id: int





class CycleStatusOut(BaseModel):

    last_period_start: date | None

    average_cycle_length: float | None

    next_period: date | None

    late_luteal: bool

    bbt_readings: int

    ovulation_confirmed_from: date | None

    not_contraception: str





class MindfulnessProgressOut(BaseModel):

    completed_days: list[int]

    next_day: int | None

    total_days: int



class ArticleOut(BaseModel):
    slug: str
    title: str
    topic: str
    source: str
    summary: str
    minutes: int
    tier: Literal["free", "premium"]
    unlocked: bool
    url: str | None  # only sent when unlocked


class PlanOut(BaseModel):
    plan: Literal["free", "premium"]


class EmotionalIn(BaseModel):
    log_date: date
    mood: int = Field(ge=1, le=5)
    stress: int = Field(ge=1, le=10)
    energy: int = Field(ge=1, le=5)
    areas: list[str] = Field(default_factory=list, max_length=7)
    handoff: str = Field(default="", max_length=300)
    notes: str = Field(default="", max_length=1000)


class EmotionalOut(EmotionalIn):
    id: int
