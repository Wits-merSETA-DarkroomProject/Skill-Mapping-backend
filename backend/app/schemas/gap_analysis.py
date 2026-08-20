from typing import List, Optional
from pydantic import BaseModel, Field

# -----------------------------------------------------------------------------
# Extraction Schemas
# -----------------------------------------------------------------------------

class ExtractedSkillItem(BaseModel):
    skill_id: str
    concept_uri: Optional[str] = None
    preferred_label: str
    extracted_claim: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    confidence_tier: str = "direct"  # "direct", "related", "inferred"
    source_citation: Optional[str] = None
    skill_type: str = "skill/competence"
    reuse_level: Optional[str] = "sector-specific"

class AdjacentOccupation(BaseModel):
    occupation_id: str
    concept_uri: Optional[str] = None
    title: str
    isco_group: str
    category: str
    match_percent: int
    matched_count: int
    total_essential: int

class ExtractionResponse(BaseModel):
    profile_id: str
    full_name: str
    cv_file_name: Optional[str] = None
    extracted_skills: List[ExtractedSkillItem]
    adjacent_occupations: List[AdjacentOccupation]
    inferred_experience_summary: Optional[str] = None

# -----------------------------------------------------------------------------
# Occupation Schemas
# -----------------------------------------------------------------------------

class SkillRequirement(BaseModel):
    skill_id: str
    concept_uri: Optional[str] = None
    preferred_label: str
    relation_type: str = "essential"  # "essential" or "optional"
    importance_score: float = 1.0
    skill_type: Optional[str] = "skill/competence"
    reuse_level: Optional[str] = "sector-specific"
    description: Optional[str] = None
    alt_labels: List[str] = []

class OccupationSummary(BaseModel):
    id: str
    title: str
    isco_group: str
    category: str
    description: str
    essential_skills: List[SkillRequirement] = []
    optional_skills: List[SkillRequirement] = []

# -----------------------------------------------------------------------------
# Gap Evaluation Schemas
# -----------------------------------------------------------------------------

class EvaluationRequest(BaseModel):
    profile_id: str
    occupation_id: str

# class LearningPathwayItem(BaseModel):
#     skill_name: str
#     course_title: str
#     provider_name: str
#     nqf_level: str
#     funding_scheme: str
#     duration_weeks: Optional[int] = 4
#     description: Optional[str] = None

class SkillMatchResult(BaseModel):
    skill_id: str
    preferred_label: str
    relation_type: str = "essential"  # "essential" or "optional"
    is_matched: bool
    confidence_score: Optional[float] = None
    source_citation: Optional[str] = None
    confidence_tier: Optional[str] = None

class EvaluationResponse(BaseModel):
    run_id: str
    profile_id: str
    target_occupation: OccupationSummary
    essential_match_percent: int
    optional_match_percent: int
    overall_match_percent: int
    
    matched_essential: List[SkillMatchResult]
    missing_essential: List[SkillMatchResult]
    matched_optional: List[SkillMatchResult]
    missing_optional: List[SkillMatchResult]
    
    #recommended_pathways: List[LearningPathwayItem]
    ai_guidance_summary: str
