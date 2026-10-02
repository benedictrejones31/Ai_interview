import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.session import Base, get_db
from app.models.candidate import Candidate
from app.models.interview import Interview
from app.models.question import Question


from sqlalchemy.pool import StaticPool

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
Base.metadata.create_all(bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "ai-voice-interviewer"


def test_invalid_resume_upload_filetype():
    files = {"file": ("test.png", b"fake image bytes", "image/png")}
    response = client.post("/api/resumes/upload", files=files)
    assert response.status_code == 400
    assert "Only PDF files are supported" in response.json()["detail"]


def test_interview_lifecycle():
    # Setup test candidate and interview in test DB
    db = TestingSessionLocal()
    cand = Candidate(
        name="Elena Rostova",
        email="elena@example.com",
        resume_filename="elena.pdf",
        resume_text="Cloud Engineer with Kubernetes and Go experience",
        profile_json={"skills": ["Go", "Kubernetes", "AWS"]}
    )
    db.add(cand)
    db.commit()
    db.refresh(cand)

    it = Interview(candidate_id=cand.id, status="pending", total_questions=1)
    db.add(it)
    db.commit()
    db.refresh(it)

    q = Question(
        interview_id=it.id,
        question_order=1,
        category="technical_skills",
        question_text="How does Kubernetes scheduler work?",
        skills_tested_json=["Kubernetes"],
        difficulty="advanced",
        expected_topics_json=["Kube-scheduler", "Filtering", "Scoring"]
    )
    db.add(q)
    interview_id = it.id
    db.commit()
    db.close()

    # 1. Get interview
    res = client.get(f"/api/interviews/{interview_id}")
    assert res.status_code == 200
    assert res.json()["candidate"]["name"] == "Elena Rostova"
    assert len(res.json()["questions"]) == 1

    # 2. Start interview
    start_res = client.post(f"/api/interviews/{interview_id}/start")
    assert start_res.status_code == 200
    assert start_res.json()["first_question"]["question_order"] == 1
    assert "Elena Rostova" in start_res.json()["welcome_message"]

    # 3. Admin list
    admin_res = client.get("/api/admin/interviews")
    assert admin_res.status_code == 200
    assert len(admin_res.json()) >= 1

