"""Database side of article access: which premium articles a user has unlocked, and the rewarded-ad flow."""
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import AdUnlock, User
from app.services import articles


class AccessError(Exception):
    """Raised when an article or ad action isn't allowed."""


def unlocked_slugs(db: Session, user_id: int, now: datetime) -> set[str]:
    return set(db.scalars(select(AdUnlock.article_slug).where(
        AdUnlock.user_id == user_id, AdUnlock.unlocked_until.is_not(None), AdUnlock.unlocked_until > now)))


def claimed_today(db: Session, user_id: int, now: datetime) -> int:
    start_of_day = datetime.combine(now.date(), datetime.min.time())
    return db.scalar(select(func.count(AdUnlock.id)).where(
        AdUnlock.user_id == user_id, AdUnlock.claimed_at.is_not(None), AdUnlock.claimed_at >= start_of_day)) or 0


def catalogue(db: Session, user: User, now: datetime) -> list[dict]:
    """Every article with an `unlocked` flag. The URL is only included when unlocked."""
    slugs = unlocked_slugs(db, user.id, now)
    out = []
    for a in articles.ARTICLES:
        unlocked = articles.is_unlocked(a, user.plan, slugs)
        out.append({**a, "unlocked": unlocked, "url": a["url"] if unlocked else None})
    return out


def _premium_article(slug: str) -> dict:
    article = articles.BY_SLUG.get(slug)
    if article is None:
        raise AccessError("Article not found")
    return article


def start_ad(db: Session, user: User, slug: str, now: datetime) -> AdUnlock:
    article = _premium_article(slug)
    if articles.is_unlocked(article, user.plan, unlocked_slugs(db, user.id, now)):
        raise AccessError("This article is already unlocked")
    view = AdUnlock(user_id=user.id, article_slug=slug, started_at=now)
    db.add(view)
    db.commit()
    return view


def claim_ad(db: Session, user: User, slug: str, now: datetime) -> AdUnlock:
    _premium_article(slug)
    view = db.scalar(select(AdUnlock).where(
        AdUnlock.user_id == user.id, AdUnlock.article_slug == slug, AdUnlock.claimed_at.is_(None)
    ).order_by(AdUnlock.started_at.desc()).limit(1))
    error = articles.ad_claim_error(view.started_at if view else None, now, claimed_today(db, user.id, now))
    if error:
        raise AccessError(error)
    view.claimed_at = now
    view.unlocked_until = articles.unlock_until(now)
    db.commit()
    return view
