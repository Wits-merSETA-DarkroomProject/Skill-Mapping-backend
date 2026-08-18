import uuid
import logging
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Body

from app.services.extraction_service import extraction_service
from app.services.ai_service import ai_service
from app.services.gap_engine import gap_engine
from app.db.supabase_client import db_manager
from app.schemas.gap_analysis import (
    ExtractionResponse,
    OccupationSummary,
    SkillRequirement,
    EvaluationRequest,
    EvaluationResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gap-analysis", tags=["Skills Gap Analysis"])

@router.post("/extract", response_model=ExtractionResponse)
async def extract_candidate_profile(
    file: Optional[UploadFile] = File(None),
    profile_text: Optional[str] = Form(None),
    full_name: Optional[str] = Form("Candidate"),
    linkedin_url: Optional[str] = Form(None)
):
    """
    Ingests CV document or biography text, extracts competencies via AI,
    maps them to canonical ESCO skills, and computes adjacent occupations.
    """
    raw_text = ""
    filename = None

    # 1. Process uploaded document if provided
    if file:
        filename = file.filename
        file_bytes = await file.read()
        extracted_text, _ = extraction_service.extract_from_bytes(file_bytes, filename)
        raw_text = extracted_text

    # 2. Append profile_text if provided
    if profile_text and profile_text.strip():
        if raw_text:
            raw_text = f"{raw_text}\n\nAdditional Summary:\n{profile_text}"
        else:
            raw_text = profile_text

    if not raw_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Please provide a CV document or profile experience text."
        )

    # 3. AI Extraction of claims
    extracted_data = await ai_service.extract_competencies(raw_text)
    candidate_name = full_name if full_name and full_name != "Candidate" else extracted_data.get("full_name", "Candidate")
    claims = extracted_data.get("claims", [])
    inferred_exp = extracted_data.get("inferred_experience_summary", "")

    # 4. Resolve against ESCO and compute Adjacent Occupations
    profile_id = f"prof_{uuid.uuid4().hex[:12]}"
    resolved_skills, adjacent_occupations = await gap_engine.resolve_skills_and_adjacency(
        profile_id=profile_id,
        claims=claims
    )

    # 5. Persist profile in DB
    profile_record = {
        "id": profile_id,
        "full_name": candidate_name,
        "cv_file_name": filename,
        "raw_text": raw_text,
        "linkedin_url": linkedin_url,
        "extracted_skills": [s.model_dump() for s in resolved_skills],
        "adjacent_occupations": [a.model_dump() for a in adjacent_occupations],
        "inferred_experience_summary": inferred_exp
    }
    db_manager.save_profile(profile_record)

    return ExtractionResponse(
        profile_id=profile_id,
        full_name=candidate_name,
        cv_file_name=filename,
        extracted_skills=resolved_skills,
        adjacent_occupations=adjacent_occupations,
        inferred_experience_summary=inferred_exp
    )

@router.get("/occupations", response_model=List[OccupationSummary])
async def list_occupations():
    """
    Returns available ESCO trade occupations with their Essential and Optional skill sets.
    """
    occupations = db_manager.get_all_occupations()
    summaries = []
    
    for occ in occupations:
        essential = [
            SkillRequirement(
                skill_id=s["id"],
                preferred_label=s["label"],
                relation_type="essential",
                importance_score=s.get("importance_score", 1.0),
                description=s.get("description"),
                alt_labels=s.get("alt_labels", [])
            )
            for s in occ["skills"] if s.get("relation_type") == "essential"
        ]
        optional = [
            SkillRequirement(
                skill_id=s["id"],
                preferred_label=s["label"],
                relation_type="optional",
                importance_score=s.get("importance_score", 0.5),
                description=s.get("description"),
                alt_labels=s.get("alt_labels", [])
            )
            for s in occ["skills"] if s.get("relation_type") == "optional"
        ]
        
        summaries.append(OccupationSummary(
            id=occ["id"],
            title=occ["title"],
            isco_group=occ.get("isco_group", "3231"),
            category=occ.get("category", "General"),
            description=occ.get("description", ""),
            essential_skills=essential,
            optional_skills=optional
        ))

    return summaries

@router.get("/occupations/{occupation_id}", response_model=OccupationSummary)
async def get_occupation_detail(occupation_id: str):
    """
    Returns a single ESCO occupation profile by ID.
    """
    occ = db_manager.get_occupation_by_id(occupation_id)
    if not occ:
        raise HTTPException(status_code=404, detail="Occupation not found")
    
    essential = [
        SkillRequirement(
            skill_id=s["id"],
            preferred_label=s["label"],
            relation_type="essential",
            importance_score=s.get("importance_score", 1.0),
            description=s.get("description"),
            alt_labels=s.get("alt_labels", [])
        )
        for s in occ["skills"] if s.get("relation_type") == "essential"
    ]
    optional = [
        SkillRequirement(
            skill_id=s["id"],
            preferred_label=s["label"],
            relation_type="optional",
            importance_score=s.get("importance_score", 0.5),
            description=s.get("description"),
            alt_labels=s.get("alt_labels", [])
        )
        for s in occ["skills"] if s.get("relation_type") == "optional"
    ]

    return OccupationSummary(
        id=occ["id"],
        title=occ["title"],
        isco_group=occ.get("isco_group", "3231"),
        category=occ.get("category", "General"),
        description=occ.get("description", ""),
        essential_skills=essential,
        optional_skills=optional
    )

@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_skills_gap(payload: EvaluationRequest = Body(...)):
    """
    Evaluates candidate profile against target ESCO occupation.
    Returns matched vs missing skills, confidence citations, learning pathways, and AI advice.
    """
    profile_data = db_manager.get_profile(payload.profile_id)
    if not profile_data:
        raise HTTPException(
            status_code=404,
            detail="Candidate profile not found. Please extract CV / profile first."
        )

    try:
        response = await gap_engine.evaluate_gap(
            profile_data=profile_data,
            occupation_id=payload.occupation_id
        )
        return response
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error during gap evaluation: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate gap analysis.")

@router.get("/profile/{profile_id}")
async def get_candidate_profile(profile_id: str):
    """
    Retrieves stored profile and parsed competencies for dashboard hydration.
    """
    profile_data = db_manager.get_profile(profile_id)
    if not profile_data:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile_data
