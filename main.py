import datetime
from fastapi import FastAPI, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional

import models
import database

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Challenge Tracker")
templates = Jinja2Templates(directory="templates")


# ─── helpers ────────────────────────────────────────────────────────────────

def get_or_create_days(challenge: models.Challenge, db: Session):
    """Ensure all calendar days for a challenge exist in DB."""
    existing = {d.day_number for d in challenge.days}
    for n in range(1, challenge.total_days + 1):
        if n not in existing:
            day_date = challenge.start_date + datetime.timedelta(days=n - 1)
            db.add(models.ChallengeDay(
                challenge_id=challenge.id,
                day_number=n,
                date=day_date
            ))
    db.commit()
    db.refresh(challenge)


def calc_streak(days: list) -> int:
    """Current consecutive-done streak counting backwards from today."""
    sorted_days = sorted(
        [d for d in days if d.is_done],
        key=lambda d: d.date,
        reverse=True
    )
    today = datetime.date.today()
    streak = 0
    expected = today
    for d in sorted_days:
        if d.date == expected:
            streak += 1
            expected -= datetime.timedelta(days=1)
        elif d.date < expected:
            break
    return streak


def enrich(challenge: models.Challenge) -> dict:
    days = sorted(challenge.days, key=lambda d: d.day_number)
    done  = sum(1 for d in days if d.is_done)
    left  = challenge.total_days - done
    pct   = round(done / challenge.total_days * 100) if challenge.total_days else 0
    today = datetime.date.today()

    # find today's day entry
    today_day = next(
        (d for d in days if d.date == today), None
    )

    return {
        "challenge": challenge,
        "days": days,
        "done": done,
        "left": left,
        "pct": pct,
        "streak": calc_streak(days),
        "today_day": today_day,
        "today": today,
    }


# ─── routes ─────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(database.get_db)):
    challenges = db.query(models.Challenge).order_by(
        models.Challenge.created_at.desc()
    ).all()

    enriched = []
    for c in challenges:
        get_or_create_days(c, db)
        enriched.append(enrich(c))

    return templates.TemplateResponse(
        request,
        "index.html",
        {"items": enriched}
    )


@app.get("/create", response_class=HTMLResponse)
def create_form(request: Request):
    today = datetime.date.today().isoformat()
    return templates.TemplateResponse(
        request,
        "create.html",
        {"today": today}
    )


@app.post("/create")
def create_challenge(
    title: str = Form(...),
    description: str = Form(""),
    total_days: int = Form(90),
    time_from: str = Form("06:00"),
    time_to: str = Form("07:00"),
    start_date: str = Form(...),
    db: Session = Depends(database.get_db)
):
    challenge = models.Challenge(
        title=title,
        description=description,
        total_days=total_days,
        time_from=time_from,
        time_to=time_to,
        start_date=datetime.date.fromisoformat(start_date),
    )
    db.add(challenge)
    db.commit()
    db.refresh(challenge)
    get_or_create_days(challenge, db)
    return RedirectResponse(f"/challenge/{challenge.id}", status_code=302)


@app.get("/challenge/{challenge_id}", response_class=HTMLResponse)
def detail(
    challenge_id: int,
    request: Request,
    db: Session = Depends(database.get_db)
):
    c = db.query(models.Challenge).filter(
        models.Challenge.id == challenge_id
    ).first()
    if not c:
        raise HTTPException(status_code=404, detail="Challenge not found")
    get_or_create_days(c, db)
    data = enrich(c)
    return templates.TemplateResponse(
        request,
        "detail.html",
        data
    )


@app.post("/toggle/{day_id}")
def toggle_day(
    day_id: int,
    db: Session = Depends(database.get_db)
):
    day = db.query(models.ChallengeDay).filter(
        models.ChallengeDay.id == day_id
    ).first()
    if not day:
        raise HTTPException(status_code=404, detail="Day not found")

    day.is_done = not day.is_done
    day.completed_at = datetime.datetime.now() if day.is_done else None
    db.commit()
    return RedirectResponse(
        f"/challenge/{day.challenge_id}", status_code=302
    )


@app.post("/delete/{challenge_id}")
def delete_challenge(
    challenge_id: int,
    db: Session = Depends(database.get_db)
):
    c = db.query(models.Challenge).filter(
        models.Challenge.id == challenge_id
    ).first()
    if not c:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(c)
    db.commit()
    return RedirectResponse("/", status_code=302)
