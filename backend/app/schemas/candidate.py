from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class EducationItem(BaseModel):
    institution: Optional[str] = None
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    year: Optional[str] = None


class ProjectItem(BaseModel):
    title: str
    description: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)


class ExperienceItem(BaseModel):
    company: Optional[str] = None
    role: Optional[str] = None
    duration: Optional[str] = None
    highlights: List[str] = Field(default_factory=list)


class CandidateProfile(BaseModel):
    name: str = "Candidate"
    summary: str = ""
    skills: List[str] = Field(default_factory=list)
    education: List[Dict[str, Any]] = Field(default_factory=list)
    projects: List[Dict[str, Any]] = Field(default_factory=list)
    experience: List[Dict[str, Any]] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    target_roles: List[str] = Field(default_factory=list)


class CandidateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: Optional[str] = None
    resume_filename: str
    profile: CandidateProfile
    created_at: datetime

