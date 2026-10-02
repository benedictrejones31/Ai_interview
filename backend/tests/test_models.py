import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.session import Base
from app.models.candidate import Candidate
from app.models.interview import Interview
from app.models.question import Question
from app.models.answer import Answer


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_candidate_and_interview_creation(test_db):
    candidate = Candidate(
        name="Sarah Connor",
        email="sarah@example.com",
        resume_filename="sarah_resume.pdf",
        resume_text="Experienced Robotics and Systems Engineer",
        profile_json={"skills": ["C++", "ROS", "Python"], "projects": []}
    )
    test_db.add(candidate)
    test_db.commit()
    test_db.refresh(candidate)

    assert candidate.id is not None
    assert candidate.name == "Sarah Connor"

    interview = Interview(
        candidate_id=candidate.id,
        status="pending",
        total_questions=10
    )
    test_db.add(interview)
    test_db.commit()
    test_db.refresh(interview)

    assert interview.id is not None
    assert interview.candidate.name == "Sarah Connor"


def test_question_and_answer_relationship(test_db):
    candidate = Candidate(
        name="David Miller",
        resume_filename="david.pdf",
        resume_text="Full Stack Developer",
        profile_json={"skills": ["React", "Node.js"]}
    )
    test_db.add(candidate)
    test_db.commit()

    interview = Interview(
        candidate_id=candidate.id,
        status="in_progress",
        total_questions=5
    )
    test_db.add(interview)
    test_db.commit()

    question = Question(
        interview_id=interview.id,
        question_order=1,
        category="technical_skills",
        question_text="How do you handle state management in React?",
        skills_tested_json=["React", "State"],
        difficulty="intermediate",
        expected_topics_json=["Redux", "Context API", "Zustand"]
    )
    test_db.add(question)
    test_db.commit()

    answer = Answer(
        question_id=question.id,
        interview_id=interview.id,
        transcript="I use Zustand for lightweight global state and React Query for server state.",
        duration_seconds=18.5,
        evaluation_json={"score": 90, "strengths": ["Clear modern stack selection"]}
    )
    test_db.add(answer)
    test_db.commit()

    # Query back
    saved_q = test_db.query(Question).filter(Question.id == question.id).first()
    assert len(saved_q.answers) == 1
    assert saved_q.answers[0].evaluation_json["score"] == 90

