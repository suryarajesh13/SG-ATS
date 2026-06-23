from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ModelProvider(str, Enum):
    OLLAMA = "ollama"
    GEMINI = "gemini"
    OPENAI = "openai"


class Location(BaseModel):
    model_config = ConfigDict(extra="ignore")
    address: Optional[str] = None
    postalCode: Optional[str] = None
    city: Optional[str] = None
    countryCode: Optional[str] = None
    region: Optional[str] = None


class Profile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    network: Optional[str] = None
    username: Optional[str] = None
    url: Optional[str] = None


class Basics(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: Optional[str] = None
    label: Optional[str] = None
    image: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    url: Optional[str] = None
    summary: Optional[str] = None
    location: Optional[Location] = None
    profiles: List[Profile] = Field(default_factory=list)


class Work(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: Optional[str] = None
    position: Optional[str] = None
    url: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    summary: Optional[str] = None
    highlights: List[str] = Field(default_factory=list)


class Volunteer(BaseModel):
    model_config = ConfigDict(extra="ignore")
    organization: Optional[str] = None
    position: Optional[str] = None
    url: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    summary: Optional[str] = None
    highlights: List[str] = Field(default_factory=list)


class Education(BaseModel):
    model_config = ConfigDict(extra="ignore")
    institution: Optional[str] = None
    url: Optional[str] = None
    area: Optional[str] = None
    studyType: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    score: Optional[str] = None
    courses: List[str] = Field(default_factory=list)


class Award(BaseModel):
    model_config = ConfigDict(extra="ignore")
    title: Optional[str] = None
    date: Optional[str] = None
    awarder: Optional[str] = None
    summary: Optional[str] = None


class Certificate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: Optional[str] = None
    date: Optional[str] = None
    issuer: Optional[str] = None
    url: Optional[str] = None


class Publication(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: Optional[str] = None
    publisher: Optional[str] = None
    releaseDate: Optional[str] = None
    url: Optional[str] = None
    summary: Optional[str] = None


class Skill(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: Optional[str] = None
    level: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)


class Language(BaseModel):
    model_config = ConfigDict(extra="ignore")
    language: Optional[str] = None
    fluency: Optional[str] = None


class Interest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)


class Reference(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: Optional[str] = None
    reference: Optional[str] = None


class Project(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    description: Optional[str] = None
    highlights: List[str] = Field(default_factory=list)
    url: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)


class JSONResume(BaseModel):
    model_config = ConfigDict(extra="ignore")
    basics: Optional[Basics] = None
    work: List[Work] = Field(default_factory=list)
    volunteer: List[Volunteer] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    awards: List[Award] = Field(default_factory=list)
    certificates: List[Certificate] = Field(default_factory=list)
    publications: List[Publication] = Field(default_factory=list)
    skills: List[Skill] = Field(default_factory=list)
    languages: List[Language] = Field(default_factory=list)
    interests: List[Interest] = Field(default_factory=list)
    references: List[Reference] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
    meta: Dict = Field(default_factory=dict)


class CategoryScore(BaseModel):
    score: int = 0
    max: int = 0
    evidence: str = "Not provided"

    @field_validator("score", "max", mode="before")
    @classmethod
    def non_negative(cls, value: int) -> int:
        if value < 0:
            raise ValueError("Score values cannot be negative.")
        return value

    @field_validator("evidence")
    @classmethod
    def evidence_not_blank(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Evidence cannot be empty.")
        return value.strip()

    @model_validator(mode="after")
    def within_max(self) -> "CategoryScore":
        if self.score > self.max:
            raise ValueError(f"Score {self.score} cannot exceed max {self.max}.")
        return self


class SoftwareScores(BaseModel):
    open_source: CategoryScore = Field(
        default_factory=lambda: CategoryScore(score=0, max=35, evidence="Not provided")
    )
    self_projects: CategoryScore = Field(
        default_factory=lambda: CategoryScore(score=0, max=30, evidence="Not provided")
    )
    production: CategoryScore = Field(
        default_factory=lambda: CategoryScore(score=0, max=25, evidence="Not provided")
    )
    technical_skills: CategoryScore = Field(
        default_factory=lambda: CategoryScore(score=0, max=10, evidence="Not provided")
    )


class BonusPoints(BaseModel):
    total: int = 0
    breakdown: str = ""

    @field_validator("total")
    @classmethod
    def validate_total(cls, value: int) -> int:
        if value < 0:
            raise ValueError("Bonus points cannot be negative.")
        if value > 20:
            raise ValueError("Bonus points cannot exceed 20.")
        return value


class Deductions(BaseModel):
    total: int = 0
    reasons: str = ""

    @field_validator("total")
    @classmethod
    def validate_total(cls, value: int) -> int:
        if value < 0:
            raise ValueError("Deductions cannot be negative.")
        return value


class EvaluationData(BaseModel):
    scores: SoftwareScores = Field(default_factory=SoftwareScores)
    bonus_points: BonusPoints = Field(default_factory=BonusPoints)
    deductions: Deductions = Field(default_factory=Deductions)
    key_strengths: List[str] = Field(default_factory=list)
    areas_for_improvement: List[str] = Field(default_factory=list)

    @field_validator("key_strengths")
    @classmethod
    def strengths_limit(cls, value: List[str]) -> List[str]:
        if len(value) > 5:
            raise ValueError("key_strengths cannot exceed 5 items.")
        return value

    @field_validator("areas_for_improvement")
    @classmethod
    def improvements_limit(cls, value: List[str]) -> List[str]:
        if len(value) > 3:
            raise ValueError("areas_for_improvement cannot exceed 3 items.")
        return value

    def total_score(self) -> int:
        raw = (
            self.scores.open_source.score
            + self.scores.self_projects.score
            + self.scores.production.score
            + self.scores.technical_skills.score
        )
        return raw + self.bonus_points.total - self.deductions.total

    def max_score(self) -> int:
        return (
            self.scores.open_source.max
            + self.scores.self_projects.max
            + self.scores.production.max
            + self.scores.technical_skills.max
        )


ROLE_CATEGORY_MAP: Dict[str, List[str]] = {
    "it_sg": [
        "sg_technical_skills",
        "projects_and_delivery",
        "production_experience",
        "professional_readiness",
    ],
    "accounting_sg": [
        "sg_certifications",
        "accounting_experience",
        "finance_systems",
        "professional_communication",
    ],
    "audit_sg": [
        "sg_audit_credentials",
        "audit_experience",
        "controls_and_regulatory",
        "audit_tools_and_analysis",
    ],
    "hr_sg": [
        "sg_hr_credentials",
        "hr_operations_and_specialisation",
        "stakeholder_management",
        "hr_systems_and_compliance",
    ],
    "banking_sg": [
        "sg_banking_credentials",
        "banking_experience",
        "regulatory_and_risk",
        "systems_and_analysis",
    ],
}


class GenericSGEvaluation(BaseModel):
    scores: Dict[str, CategoryScore] = Field(default_factory=dict)
    bonus_points: BonusPoints = Field(default_factory=BonusPoints)
    deductions: Deductions = Field(default_factory=Deductions)
    key_strengths: List[str] = Field(default_factory=list)
    areas_for_improvement: List[str] = Field(default_factory=list)

    @field_validator("key_strengths")
    @classmethod
    def strengths_limit(cls, value: List[str]) -> List[str]:
        if len(value) > 5:
            raise ValueError("key_strengths cannot exceed 5 items.")
        return value

    @field_validator("areas_for_improvement")
    @classmethod
    def improvements_limit(cls, value: List[str]) -> List[str]:
        if len(value) > 3:
            raise ValueError("areas_for_improvement cannot exceed 3 items.")
        return value

    @model_validator(mode="after")
    def validate_category_count(self) -> "GenericSGEvaluation":
        if len(self.scores) != 4:
            raise ValueError(
                f"Exactly 4 score categories are required, got {len(self.scores)}."
            )
        return self

    def total_score(self) -> int:
        raw = sum(c.score for c in self.scores.values())
        return raw + self.bonus_points.total - self.deductions.total

    def max_score(self) -> int:
        return sum(c.max for c in self.scores.values())


def validate_sg_categories(evaluation: GenericSGEvaluation, role_type: str) -> List[str]:
    expected = ROLE_CATEGORY_MAP.get(role_type, [])
    actual = list(evaluation.scores.keys())
    warnings: List[str] = []
    for key in expected:
        if key not in actual:
            warnings.append(f"Missing expected category '{key}' for role '{role_type}'.")
    for key in actual:
        if key not in expected:
            warnings.append(f"Unexpected category '{key}' for role '{role_type}'.")
    return warnings


def assert_sg_categories(evaluation: GenericSGEvaluation, role_type: str) -> None:
    warnings = validate_sg_categories(evaluation, role_type)
    if warnings:
        raise ValueError(" ; ".join(warnings))
