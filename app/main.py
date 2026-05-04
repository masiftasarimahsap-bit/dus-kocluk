from fastapi import FastAPI, Depends, HTTPException, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import date, timedelta
import json
import os
import base64
import uuid
import anthropic

from database import (
    get_db, init_db, Student, WeeklyAvailability, Course, Topic,
    TopicProgress, DailyReport, PlannedSession, SessionNote
)

app = FastAPI(title="DUS Koçluk Sistemi")
templates = Jinja2Templates(directory="templates")

UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

DAYS_TR = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
DAYS_SHORT = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]
PROFILE_LABELS = {"intensive": "Yoğun", "moderate": "Orta", "limited": "Sınırlı", "minimal": "Minimal"}
MOOD_LABELS = {"great": "Harika", "good": "İyi", "neutral": "Normal", "bad": "Kötü", "terrible": "Berbat"}
MOOD_EMOJI = {"great": "🌟", "good": "😊", "neutral": "😐", "bad": "😔", "terrible": "😞"}
STATUS_LABELS = {
    "not_started": "Başlanmadı", "studied": "Çalışıldı",
    "reviewed": "Tekrar edildi", "reinforced": "Pekiştirildi", "mastered": "Öğrenildi"
}
KL_LABELS = {0: "Bilmiyorum", 1: "Zayıf", 2: "Orta", 3: "İyi"}
KL_COLORS = {0: "#fee2e2", 1: "#fef9c3", 2: "#dbeafe", 3: "#dcfce7"}


@app.on_event("startup")
def startup():
    init_db()


# ── STUDENT ROUTES ───────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    students = db.query(Student).all()
    return templates.TemplateResponse("index.html", {"request": request, "students": students})


@app.get("/student/new", response_class=HTMLResponse)
def new_student_form(request: Request, db: Session = Depends(get_db)):
    courses = db.query(Course).filter(Course.is_active == True).order_by(Course.display_order).all()
    return templates.TemplateResponse("new_student.html", {
        "request": request,
        "days_tr": DAYS_TR,
        "courses": courses,
    })


@app.post("/student/new")
async def create_student(request: Request, db: Session = Depends(get_db)):
    form = await request.form()

    name = form.get("name", "")
    email = form.get("email", "")
    phone = form.get("phone", "")
    is_working = form.get("is_working", "no")
    work_start = form.get("work_start", "")
    work_end = form.get("work_end", "")
    exam_date = form.get("exam_date", "")
    target_goal = form.get("target_goal", "pass")
    study_pref = form.get("study_pref", "flexible")
    previous_study = form.get("previous_study", "no")
    last_mock = form.get("last_mock", "")

    day_keys = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    hours = [float(form.get(k, 0) or 0) for k in day_keys]
    weekly = sum(hours)

    if weekly >= 40:
        profile = "intensive"
    elif weekly >= 20:
        profile = "moderate"
    elif weekly >= 10:
        profile = "limited"
    else:
        profile = "minimal"

    student = Student(
        name=name, email=email, phone=phone,
        is_working=(is_working == "yes"),
        work_hours_start=work_start or None,
        work_hours_end=work_end or None,
        exam_target_date=date.fromisoformat(exam_date) if exam_date else None,
        target_goal=target_goal,
        profile_type=profile,
        study_preference=study_pref,
        previous_study=(previous_study == "yes"),
        last_mock_score=int(last_mock) if last_mock else None,
    )
    db.add(student)
    db.flush()

    for i, h in enumerate(hours):
        db.add(WeeklyAvailability(student_id=student.id, day_of_week=i, available_hours=h))

    # Save knowledge levels from form: topic_<id> = 0/1/2/3
    topics = db.query(Topic).all()
    for topic in topics:
        kl_val = form.get(f"topic_{topic.id}", "0")
        kl = int(kl_val) if kl_val in ("0", "1", "2", "3") else 0
        db.add(TopicProgress(
            student_id=student.id,
            topic_id=topic.id,
            knowledge_level=kl,
            status="not_started" if kl == 0 else "studied" if kl >= 2 else "not_started",
        ))

    db.flush()
    _generate_plan(student.id, db)
    db.commit()

    return RedirectResponse(f"/student/{student.id}", status_code=303)


@app.get("/student/{student_id}", response_class=HTMLResponse)
def student_dashboard(request: Request, student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(404)

    availability = {a.day_of_week: a.available_hours for a in student.availability}
    weekly_hours = sum(availability.values())

    reports = db.query(DailyReport).filter(
        DailyReport.student_id == student_id
    ).order_by(DailyReport.date.desc()).limit(14).all()

    courses = db.query(Course).filter(Course.is_active == True).order_by(Course.display_order).all()
    progress_map = {
        tp.topic_id: tp for tp in db.query(TopicProgress).filter(TopicProgress.student_id == student_id).all()
    }

    course_stats = []
    for course in courses:
        topics = db.query(Topic).filter(Topic.course_id == course.id).all()
        total = len(topics)
        done = sum(1 for t in topics if progress_map.get(t.id) and progress_map[t.id].status != "not_started")
        course_stats.append({
            "course": course,
            "total": total,
            "done": done,
            "pct": round(done / total * 100) if total else 0
        })

    days_left = (student.exam_target_date - date.today()).days if student.exam_target_date else None
    avg_compliance = round(sum(r.compliance_rate for r in reports) / len(reports), 1) if reports else 0

    # Today's plan
    today_sessions = db.query(PlannedSession).filter(
        PlannedSession.student_id == student_id,
        PlannedSession.date == date.today()
    ).order_by(PlannedSession.order_in_day).all()

    # This week's plan (Mon–Sun of current week)
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_sessions = db.query(PlannedSession).filter(
        PlannedSession.student_id == student_id,
        PlannedSession.date >= week_start,
        PlannedSession.date < week_start + timedelta(days=7)
    ).order_by(PlannedSession.date, PlannedSession.order_in_day).all()

    week_by_day = {}
    for s in week_sessions:
        d = s.date
        week_by_day.setdefault(d, []).append(s)

    week_days = [week_start + timedelta(days=i) for i in range(7)]

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "student": student,
        "availability": availability,
        "days_tr": DAYS_TR,
        "days_short": DAYS_SHORT,
        "weekly_hours": weekly_hours,
        "reports": reports,
        "course_stats": course_stats,
        "progress_map": progress_map,
        "days_left": days_left,
        "avg_compliance": avg_compliance,
        "today_sessions": today_sessions,
        "week_by_day": week_by_day,
        "week_days": week_days,
        "today": today,
        "profile_label": PROFILE_LABELS.get(student.profile_type, student.profile_type),
        "mood_labels": MOOD_LABELS,
        "mood_emoji": MOOD_EMOJI,
        "status_labels": STATUS_LABELS,
        "kl_labels": KL_LABELS,
        "kl_colors": KL_COLORS,
    })


@app.post("/student/{student_id}/session/{session_id}/toggle")
def toggle_session(student_id: int, session_id: int, db: Session = Depends(get_db)):
    s = db.query(PlannedSession).filter(
        PlannedSession.id == session_id,
        PlannedSession.student_id == student_id
    ).first()
    if not s:
        raise HTTPException(404)
    s.is_completed = not s.is_completed
    db.commit()
    return RedirectResponse(f"/student/{student_id}", status_code=303)


@app.post("/student/{student_id}/session/{session_id}/skip")
def skip_session(student_id: int, session_id: int, db: Session = Depends(get_db)):
    s = db.query(PlannedSession).filter(
        PlannedSession.id == session_id,
        PlannedSession.student_id == student_id
    ).first()
    if not s:
        raise HTTPException(404)
    s.is_skipped = not s.is_skipped
    db.commit()
    return RedirectResponse(f"/student/{student_id}", status_code=303)


@app.post("/student/{student_id}/plan/regenerate")
def regenerate_plan(student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(404)
    # Only delete future (non-completed) sessions
    db.query(PlannedSession).filter(
        PlannedSession.student_id == student_id,
        PlannedSession.date >= date.today(),
        PlannedSession.is_completed == False
    ).delete()
    _generate_plan(student_id, db)
    db.commit()
    return RedirectResponse(f"/student/{student_id}", status_code=303)


@app.get("/student/{student_id}/plan", response_class=HTMLResponse)
def full_plan(request: Request, student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(404)

    sessions = db.query(PlannedSession).filter(
        PlannedSession.student_id == student_id,
        PlannedSession.date >= date.today()
    ).order_by(PlannedSession.date, PlannedSession.order_in_day).all()

    by_week = {}
    for s in sessions:
        week_num = (s.date - date.today()).days // 7
        by_week.setdefault(week_num, {}).setdefault(s.date, []).append(s)

    return templates.TemplateResponse("plan.html", {
        "request": request,
        "student": student,
        "by_week": by_week,
        "today": date.today(),
        "days_tr": DAYS_TR,
        "profile_label": PROFILE_LABELS.get(student.profile_type, student.profile_type),
    })


@app.post("/student/{student_id}/report")
async def submit_report(request: Request, student_id: int, db: Session = Depends(get_db)):
    form = await request.form()
    actual_hours = float(form.get("actual_hours", 0) or 0)
    mood = form.get("mood", "neutral")
    general_notes = form.get("general_notes", "")

    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(404)

    availability = {a.day_of_week: a.available_hours for a in student.availability}
    today_dow = date.today().weekday()
    planned = availability.get(today_dow, 0)
    compliance = round(min(actual_hours / planned * 100, 100), 1) if planned > 0 else 0

    existing = db.query(DailyReport).filter(
        DailyReport.student_id == student_id, DailyReport.date == date.today()
    ).first()
    if existing:
        existing.total_actual_hours = actual_hours
        existing.compliance_rate = compliance
        existing.mood = mood
        existing.notes = general_notes
    else:
        db.add(DailyReport(
            student_id=student_id, date=date.today(),
            total_actual_hours=actual_hours, compliance_rate=compliance,
            mood=mood, notes=general_notes
        ))

    # Konu bazlı notları kaydet
    today_sessions = db.query(PlannedSession).filter(
        PlannedSession.student_id == student_id,
        PlannedSession.date == date.today()
    ).all()

    for s in today_sessions:
        completed = form.get(f"topic_done_{s.topic_id}") == "1"
        topic_note = form.get(f"topic_note_{s.topic_id}", "").strip()

        if completed or topic_note:
            existing_note = db.query(SessionNote).filter(
                SessionNote.student_id == student_id,
                SessionNote.topic_id == s.topic_id,
                SessionNote.date == date.today()
            ).first()
            if existing_note:
                existing_note.is_completed = completed
                existing_note.notes_text = topic_note or existing_note.notes_text
            else:
                db.add(SessionNote(
                    student_id=student_id,
                    topic_id=s.topic_id,
                    date=date.today(),
                    is_completed=completed,
                    notes_text=topic_note or None,
                ))

        if completed:
            s.is_completed = True
            tp = db.query(TopicProgress).filter(
                TopicProgress.student_id == student_id,
                TopicProgress.topic_id == s.topic_id
            ).first()
            if tp and tp.status == "not_started":
                tp.status = "studied"

    db.commit()
    return RedirectResponse(f"/student/{student_id}", status_code=303)


@app.post("/api/student/{student_id}/topic/{topic_id}/upload")
async def upload_screenshot(
    student_id: int,
    topic_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    content = await file.read()
    ext = os.path.splitext(file.filename or "img.png")[1].lower() or ".png"
    filename = f"{student_id}_{topic_id}_{uuid.uuid4().hex[:8]}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(content)

    # Claude vision ile metne dönüştür
    extracted = _extract_text_from_image(content, ext)

    # Bugünün notuna ekle veya oluştur
    note = db.query(SessionNote).filter(
        SessionNote.student_id == student_id,
        SessionNote.topic_id == topic_id,
        SessionNote.date == date.today()
    ).first()
    if note:
        note.image_path = filepath
        note.extracted_text = extracted
    else:
        db.add(SessionNote(
            student_id=student_id,
            topic_id=topic_id,
            date=date.today(),
            image_path=filepath,
            extracted_text=extracted,
        ))
    db.commit()

    return JSONResponse({"extracted_text": extracted, "image_url": f"/static/uploads/{filename}"})


@app.get("/student/{student_id}/notes", response_class=HTMLResponse)
def student_notes(request: Request, student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(404)
    notes = db.query(SessionNote).filter(
        SessionNote.student_id == student_id
    ).order_by(SessionNote.date.desc()).all()
    return templates.TemplateResponse("notes.html", {
        "request": request,
        "student": student,
        "notes": notes,
        "profile_label": PROFILE_LABELS.get(student.profile_type, student.profile_type),
    })


@app.get("/admin", response_class=HTMLResponse)
def admin_panel(request: Request, db: Session = Depends(get_db)):
    students = db.query(Student).all()
    student_data = []
    for s in students:
        reports = db.query(DailyReport).filter(DailyReport.student_id == s.id).order_by(DailyReport.date.desc()).limit(7).all()
        avg = round(sum(r.compliance_rate for r in reports) / len(reports), 1) if reports else 0
        last_active = reports[0].date if reports else None
        risk = "high" if avg < 50 else "medium" if avg < 75 else "low"
        student_data.append({
            "student": s, "avg_compliance": avg,
            "last_active": last_active, "risk": risk,
            "profile_label": PROFILE_LABELS.get(s.profile_type, s.profile_type)
        })
    courses = db.query(Course).order_by(Course.display_order).all()
    return templates.TemplateResponse("admin.html", {
        "request": request, "student_data": student_data, "courses": courses
    })


@app.get("/api/student/{student_id}/progress")
def api_progress(student_id: int, db: Session = Depends(get_db)):
    reports = db.query(DailyReport).filter(
        DailyReport.student_id == student_id
    ).order_by(DailyReport.date).all()
    return [{"date": str(r.date), "hours": r.total_actual_hours, "compliance": r.compliance_rate} for r in reports]


# ── IMAGE → TEXT ─────────────────────────────────────────────────────────────

def _extract_text_from_image(content: bytes, ext: str) -> str:
    mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
                ".gif": "image/gif", ".webp": "image/webp"}
    media_type = mime_map.get(ext.lower(), "image/png")
    b64 = base64.standard_b64encode(content).decode()

    try:
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": media_type, "data": b64},
                    },
                    {
                        "type": "text",
                        "text": (
                            "Bu görsel bir DUS (Diş Hekimliği Uzmanlık Sınavı) öğrencisinin ders notu veya ekran görüntüsüdür. "
                            "Görseldeki tüm metni, şema açıklamalarını ve önemli bilgileri Türkçe olarak düzenli biçimde yaz. "
                            "Eğer görsel bir tablo, şema veya liste içeriyorsa yapısını koru. "
                            "Sadece içeriği yaz, açıklama ekleme."
                        ),
                    },
                ],
            }],
        )
        return msg.content[0].text
    except Exception as e:
        return f"[Metin çıkarılamadı: {e}]"


# ── PLAN GENERATION ───────────────────────────────────────────────────────────

def _generate_plan(student_id: int, db: Session):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        return

    availability = {a.day_of_week: a.available_hours for a in student.availability}
    if not any(h > 0 for h in availability.values()):
        return

    today = date.today()
    end_date = student.exam_target_date if student.exam_target_date else today + timedelta(days=120)
    if end_date <= today:
        end_date = today + timedelta(days=90)

    knowledge_map = {
        tp.topic_id: tp.knowledge_level
        for tp in db.query(TopicProgress).filter(TopicProgress.student_id == student_id).all()
    }

    topics = db.query(Topic).join(Course).filter(Course.is_active == True).all()

    # Score: sınavda çıkma olasılığı × bilgi açığı (3 - seviye) / 3
    def topic_score(t):
        kl = knowledge_map.get(t.id, 0)
        return t.exam_probability * (3 - kl) / 3

    scored = sorted(topics, key=topic_score, reverse=True)

    # Build session blocks: her konu için gerekli toplam saat → 2h'lik parçalara böl
    blocks = []  # (topic, hours, session_type)
    for t in scored:
        kl = knowledge_map.get(t.id, 0)
        if kl >= 3:
            # Çok iyi biliyor, sadece kısa tekrar
            blocks.append((t, 0.5, "review"))
            continue
        adj_hours = t.recommended_hours * (3 - kl) / 3
        remaining = round(adj_hours, 1)
        first = True
        while remaining >= 0.5:
            session_h = min(remaining, 2.0)
            blocks.append((t, round(session_h, 1), "new" if first else "review"))
            remaining = round(remaining - session_h, 1)
            first = False

    # Günlere dağıt
    block_idx = 0
    current = today
    while current <= end_date and block_idx < len(blocks):
        dow = current.weekday()
        day_hours = availability.get(dow, 0)
        if day_hours > 0:
            remaining_today = day_hours
            order = 0
            while remaining_today >= 0.5 and block_idx < len(blocks):
                topic, h, stype = blocks[block_idx]
                if h <= remaining_today + 0.1:
                    db.add(PlannedSession(
                        student_id=student_id,
                        date=current,
                        topic_id=topic.id,
                        planned_hours=h,
                        session_type=stype,
                        order_in_day=order,
                    ))
                    remaining_today = round(remaining_today - h, 1)
                    block_idx += 1
                    order += 1
                else:
                    break
        current += timedelta(days=1)
