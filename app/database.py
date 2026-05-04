from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Date, DateTime, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, date
import enum

import os as _os

DATABASE_URL = _os.getenv("DATABASE_URL", "sqlite:///./dus_kocluk.db")

# Supabase/Heroku postgres:// → postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)
    phone = Column(String)
    is_working = Column(Boolean, default=False)
    work_hours_start = Column(String, nullable=True)
    work_hours_end = Column(String, nullable=True)
    has_shifts = Column(Boolean, default=False)
    exam_target_date = Column(Date, nullable=True)
    target_goal = Column(String, default="pass")
    target_branch = Column(String, nullable=True)
    profile_type = Column(String, default="moderate")
    study_preference = Column(String, default="flexible")
    previous_study = Column(Boolean, default=False)
    previous_resources = Column(Text, nullable=True)
    last_mock_score = Column(Integer, nullable=True)
    weak_topics = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    availability = relationship("WeeklyAvailability", back_populates="student")
    reports = relationship("DailyReport", back_populates="student")
    topic_progress = relationship("TopicProgress", back_populates="student")
    planned_sessions = relationship("PlannedSession", back_populates="student")


class WeeklyAvailability(Base):
    __tablename__ = "weekly_availability"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    day_of_week = Column(Integer)
    available_hours = Column(Float)
    student = relationship("Student", back_populates="availability")


class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    total_questions = Column(Integer, default=0)
    weight_percent = Column(Float, default=0)
    estimated_study_hours = Column(Integer, default=0)
    display_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    topics = relationship("Topic", back_populates="course")


class Topic(Base):
    __tablename__ = "topics"
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    name = Column(String)
    question_count = Column(Integer, default=0)
    difficulty = Column(String, default="medium")
    recommended_hours = Column(Float, default=2.0)
    priority = Column(String, default="medium")
    exam_probability = Column(Float, default=0.5)  # 0-1, sınavda çıkma olasılığı
    display_order = Column(Integer, default=0)
    course = relationship("Course", back_populates="topics")
    progress = relationship("TopicProgress", back_populates="topic")


class TopicProgress(Base):
    __tablename__ = "topic_progress"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    topic_id = Column(Integer, ForeignKey("topics.id"))
    status = Column(String, default="not_started")
    knowledge_level = Column(Integer, default=0)  # 0=bilmiyor, 1=zayıf, 2=orta, 3=iyi
    total_time_spent_minutes = Column(Integer, default=0)
    review_count = Column(Integer, default=0)
    last_difficulty_rating = Column(String, nullable=True)
    next_review_date = Column(Date, nullable=True)
    first_studied_at = Column(DateTime, nullable=True)
    last_studied_at = Column(DateTime, nullable=True)
    student = relationship("Student", back_populates="topic_progress")
    topic = relationship("Topic", back_populates="progress")


class PlannedSession(Base):
    __tablename__ = "planned_sessions"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    date = Column(Date)
    topic_id = Column(Integer, ForeignKey("topics.id"))
    planned_hours = Column(Float)
    session_type = Column(String, default="new")  # new / review
    order_in_day = Column(Integer, default=0)
    is_completed = Column(Boolean, default=False)
    is_skipped = Column(Boolean, default=False)
    student = relationship("Student", back_populates="planned_sessions")
    topic = relationship("Topic")


class SessionNote(Base):
    __tablename__ = "session_notes"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    topic_id = Column(Integer, ForeignKey("topics.id"))
    date = Column(Date)
    is_completed = Column(Boolean, default=True)
    notes_text = Column(Text, nullable=True)        # öğrencinin yazdığı not
    image_path = Column(String, nullable=True)       # yüklenen görselin yolu
    extracted_text = Column(Text, nullable=True)     # görseldan çıkarılan metin
    created_at = Column(DateTime, default=datetime.utcnow)
    student = relationship("Student")
    topic = relationship("Topic")


class DailyReport(Base):
    __tablename__ = "daily_reports"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    date = Column(Date)
    reported_at = Column(DateTime, default=datetime.utcnow)
    total_actual_hours = Column(Float, default=0)
    compliance_rate = Column(Float, default=0)
    extra_topics_studied = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    mood = Column(String, nullable=True)
    student = relationship("Student", back_populates="reports")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
    seed_data()


def seed_data():
    db = SessionLocal()
    if db.query(Course).count() > 0:
        db.close()
        return

    courses_data = [
        ("Periodontoloji", 22, 11, 40, 1),
        ("Oral Diagnoz ve Radyoloji", 18, 9, 30, 2),
        ("Ağız, Diş ve Çene Cerrahisi", 20, 10, 35, 3),
        ("Ortodonti", 16, 8, 30, 4),
        ("Protetik Diş Tedavisi", 20, 10, 35, 5),
        ("Endodonti", 22, 11, 40, 6),
        ("Restoratif Diş Tedavisi", 20, 10, 35, 7),
        ("Pedodonti", 16, 8, 28, 8),
        ("Oral Patoloji", 18, 9, 32, 9),
        ("Farmakoloji", 14, 7, 25, 10),
        ("Temel Tıp Bilimleri", 14, 7, 20, 11),
    ]
    courses = []
    for name, tq, wp, esh, order in courses_data:
        c = Course(name=name, total_questions=tq, weight_percent=wp, estimated_study_hours=esh, display_order=order)
        db.add(c)
        courses.append(c)
    db.flush()

    # (name, question_count, difficulty, recommended_hours, priority, exam_probability)
    all_topics = {
        "Periodontoloji": [
            ("Periodontal Anatomi ve Histoloji", 3, "easy", 3, "high", 0.75),
            ("Periodontal Hastalıkların Sınıflandırılması (2018)", 5, "medium", 5, "high", 0.95),
            ("Periodontal Muayene ve Tanı", 3, "medium", 4, "high", 0.85),
            ("Non-Cerrahi Periodontal Tedavi", 4, "medium", 5, "high", 0.90),
            ("Periodontal Cerrahi", 4, "hard", 6, "medium", 0.70),
            ("İmplant Periodontolojisi ve Periimplantit", 3, "hard", 5, "medium", 0.65),
        ],
        "Oral Diagnoz ve Radyoloji": [
            ("Anamnez ve Klinik Muayene Yöntemleri", 3, "easy", 3, "high", 0.80),
            ("Periapikal ve Bitewing Radyografi", 4, "medium", 5, "high", 0.90),
            ("Panoramik Radyografi Yorumlama", 3, "medium", 4, "high", 0.85),
            ("KIBT ve İleri Görüntüleme", 3, "hard", 5, "medium", 0.60),
            ("Oral Mukoza Lezyonları (Beyaz/Kırmızı)", 3, "medium", 5, "high", 0.80),
            ("Tükürük Bezi Hastalıkları", 2, "medium", 3, "medium", 0.55),
        ],
        "Ağız, Diş ve Çene Cerrahisi": [
            ("Diş Çekimi: Endikasyon, Kontrendikasyon, Teknik", 4, "easy", 4, "high", 0.85),
            ("Lokal Anestezi Teknikleri", 4, "medium", 5, "high", 0.90),
            ("Komplike Çekimler ve Komplikasyonlar", 3, "medium", 4, "high", 0.80),
            ("Çene Kistleri: Sınıflandırma ve Tedavi", 4, "hard", 6, "high", 0.85),
            ("Odontojenik Tümörler", 3, "hard", 5, "medium", 0.65),
            ("Temporomandibuler Eklem Bozuklukları", 2, "medium", 4, "medium", 0.60),
        ],
        "Ortodonti": [
            ("Kraniofasiyal Büyüme ve Gelişim", 3, "medium", 5, "high", 0.80),
            ("Ortodontik Tanı ve Sefalometri", 3, "medium", 5, "high", 0.85),
            ("Maloklüzyon Sınıflandırması (Angle)", 4, "easy", 4, "high", 0.90),
            ("Ortodontik Tedavi Mekanikleri", 3, "hard", 6, "medium", 0.70),
            ("Retansiyon ve Relaps", 3, "medium", 4, "medium", 0.65),
        ],
        "Protetik Diş Tedavisi": [
            ("Sabit Protez: Temel İlkeler ve Preparasyon", 4, "medium", 6, "high", 0.85),
            ("Hareketli Bölümlü Protez Tasarımı", 4, "hard", 7, "high", 0.80),
            ("Tam Protez: Yapım Aşamaları", 4, "hard", 7, "high", 0.80),
            ("İmplant Üstü Protez", 3, "hard", 5, "medium", 0.70),
            ("Oklüzyon Kavramları", 3, "medium", 5, "medium", 0.65),
            ("Geçici Restorasyon ve Provizyon", 2, "medium", 3, "low", 0.45),
        ],
        "Endodonti": [
            ("Pulpa Biyolojisi ve Patolojisi", 3, "easy", 4, "high", 0.85),
            ("Kök Kanal Morfolojisi", 5, "medium", 7, "high", 0.95),
            ("Endodontik Tanı ve Ayırıcı Tanı", 4, "medium", 5, "high", 0.90),
            ("Kök Kanal Şekillendirme ve Irrigasyon", 4, "hard", 8, "high", 0.90),
            ("Kök Kanal Dolgusu", 3, "medium", 4, "medium", 0.75),
            ("Endodontik Retreatment ve Cerrahi", 3, "hard", 5, "medium", 0.65),
        ],
        "Restoratif Diş Tedavisi": [
            ("Diş Çürüğü: Etiyoloji ve Sınıflandırma", 4, "easy", 4, "high", 0.85),
            ("Kavite Preparasyonu İlkeleri", 4, "medium", 5, "high", 0.80),
            ("Adeziv Sistemler ve Bonding", 3, "medium", 5, "high", 0.85),
            ("Kompozit Rezin Restorasyonlar", 4, "medium", 5, "high", 0.85),
            ("Amalgam Restorasyonlar", 2, "easy", 3, "medium", 0.55),
            ("İnley, Onley ve Veneer Restorasyonlar", 3, "hard", 5, "medium", 0.65),
        ],
        "Pedodonti": [
            ("Çocuklarda Diş ve Çene Gelişimi", 3, "easy", 4, "high", 0.85),
            ("Süt Dişi Tedavileri (Çürük Yönetimi)", 4, "medium", 5, "high", 0.85),
            ("Pedodontik Pulpa Tedavileri", 3, "medium", 5, "high", 0.85),
            ("Yer Tutucu Apareyler", 3, "medium", 4, "medium", 0.70),
            ("Çocuklarda Dental Travma", 3, "hard", 5, "medium", 0.75),
        ],
        "Oral Patoloji": [
            ("Epitelyal Patolojiler ve Potansiyel Malign Lezyonlar", 4, "medium", 6, "high", 0.90),
            ("Odontojenik Kistler (Patoloji)", 3, "medium", 5, "high", 0.85),
            ("Kemik Patolojileri (Fibröz Displazi vb.)", 4, "hard", 6, "high", 0.80),
            ("Tükürük Bezi Tümörleri", 3, "hard", 5, "medium", 0.70),
            ("Sistemik Hastalıkların Oral Bulguları", 2, "medium", 4, "medium", 0.65),
            ("Bağ Dokusu ve Mezenkimal Tümörler", 2, "hard", 4, "low", 0.50),
        ],
        "Farmakoloji": [
            ("Antibiyotikler (Penisilin, Klindamisin, Metronidazol)", 4, "medium", 5, "high", 0.90),
            ("Analjezikler, NSAİİ ve Steroidler", 4, "medium", 5, "high", 0.90),
            ("Lokal Anestezikler: Farmakodinamik", 3, "medium", 4, "high", 0.85),
            ("Antifungal ve Antiviral İlaçlar", 2, "medium", 3, "medium", 0.65),
            ("İlaç Etkileşimleri ve Yan Etkiler", 1, "hard", 3, "medium", 0.60),
        ],
        "Temel Tıp Bilimleri": [
            ("Baş-Boyun Anatomisi (Sinirler, Arterler)", 4, "medium", 5, "high", 0.85),
            ("Diş ve Destek Dokuların Histolojisi", 3, "medium", 4, "high", 0.80),
            ("Kraniofasiyal Embriyoloji", 2, "hard", 4, "medium", 0.65),
            ("Oral Mikrobiyoloji ve Biyofilm", 3, "medium", 4, "medium", 0.70),
            ("Temel İmmünoloji ve İnflamasyon", 2, "hard", 3, "low", 0.55),
        ],
    }

    course_map = {c.name: c for c in courses}
    for course_name, topics in all_topics.items():
        course = course_map[course_name]
        for i, (name, qc, diff, hours, priority, prob) in enumerate(topics):
            db.add(Topic(
                course_id=course.id, name=name, question_count=qc,
                difficulty=diff, recommended_hours=hours, priority=priority,
                exam_probability=prob, display_order=i + 1
            ))

    # Demo student
    from datetime import timedelta
    import random
    student = Student(
        name="Ahmet Yılmaz", email="ahmet@example.com", phone="05551234567",
        is_working=True, work_hours_start="09:00", work_hours_end="18:00",
        exam_target_date=date(2026, 10, 15),
        target_goal="top500", profile_type="moderate",
        study_preference="evening", previous_study=True,
        last_mock_score=52
    )
    db.add(student)
    db.flush()

    for i, hours in enumerate([0, 0, 2, 2, 2, 4, 4]):
        db.add(WeeklyAvailability(student_id=student.id, day_of_week=i, available_hours=hours))

    for i in range(10):
        d = date.today() - timedelta(days=9 - i)
        planned = 3.0
        actual = round(random.uniform(1.5, 4.0), 1)
        db.add(DailyReport(
            student_id=student.id, date=d,
            total_actual_hours=actual,
            compliance_rate=round(min(actual / planned * 100, 100), 1),
            mood=random.choice(["great", "good", "neutral", "good"])
        ))

    db.commit()
    db.close()
