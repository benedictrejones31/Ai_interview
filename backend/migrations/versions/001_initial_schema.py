"""initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-02 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. candidates table
    op.create_table(
        'candidates',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('resume_filename', sa.String(length=255), nullable=False),
        sa.Column('resume_text', sa.Text(), nullable=False),
        sa.Column('profile_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_candidates_id'), 'candidates', ['id'], unique=False)

    # 2. interviews table
    op.create_table(
        'interviews',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('candidate_id', sa.String(length=36), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('total_questions', sa.Integer(), nullable=False),
        sa.Column('completed_questions', sa.Integer(), nullable=False),
        sa.Column('overall_score', sa.Float(), nullable=True),
        sa.Column('final_report_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_interviews_candidate_id'), 'interviews', ['candidate_id'], unique=False)
    op.create_index(op.f('ix_interviews_id'), 'interviews', ['id'], unique=False)

    # 3. questions table
    op.create_table(
        'questions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('interview_id', sa.String(length=36), nullable=False),
        sa.Column('question_order', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('skills_tested_json', sa.JSON(), nullable=False),
        sa.Column('difficulty', sa.String(length=50), nullable=False),
        sa.Column('expected_topics_json', sa.JSON(), nullable=False),
        sa.Column('is_follow_up', sa.Boolean(), nullable=False),
        sa.Column('parent_question_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['interview_id'], ['interviews.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_question_id'], ['questions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_questions_id'), 'questions', ['id'], unique=False)
    op.create_index(op.f('ix_questions_interview_id'), 'questions', ['interview_id'], unique=False)
    op.create_index(op.f('ix_questions_question_order'), 'questions', ['question_order'], unique=False)

    # 4. answers table
    op.create_table(
        'answers',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('question_id', sa.String(length=36), nullable=False),
        sa.Column('interview_id', sa.String(length=36), nullable=False),
        sa.Column('transcript', sa.Text(), nullable=False),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('evaluation_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['interview_id'], ['interviews.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_answers_id'), 'answers', ['id'], unique=False)
    op.create_index(op.f('ix_answers_interview_id'), 'answers', ['interview_id'], unique=False)
    op.create_index(op.f('ix_answers_question_id'), 'answers', ['question_id'], unique=False)


def downgrade() -> None:
    op.drop_table('answers')
    op.drop_table('questions')
    op.drop_table('interviews')
    op.drop_table('candidates')

