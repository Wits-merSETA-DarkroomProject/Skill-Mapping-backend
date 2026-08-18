import pytest
import asyncio
from app.services.extraction_service import extraction_service
from app.services.ai_service import ai_service
from app.services.gap_engine import gap_engine
from app.db.supabase_client import db_manager

def test_db_manager_occupations():
    occupations = db_manager.get_all_occupations()
    assert len(occupations) > 0
    millwright = db_manager.get_occupation_by_id("occ_millwright_3231")
    assert millwright is not None
    assert millwright["title"] == "Industrial Machinery Mechanic / Millwright"
    assert len(millwright["skills"]) >= 8

def test_document_extraction_txt():
    sample_text = b"Experienced millwright with strong background in PLC troubleshooting and hydraulic systems."
    text, lines = extraction_service.extract_from_bytes(sample_text, "test.txt")
    assert "PLC troubleshooting" in text
    assert len(lines) >= 1

@pytest.mark.asyncio
async def test_ai_competency_extraction():
    sample_bio = """
    Sipho Ndlovu
    I have 4 years experience as a millwright apprentice. Confident with PLC troubleshooting,
    hydraulic systems, preventative maintenance, and welding. Currently studying for N4.
    """
    extracted = await ai_service.extract_competencies(sample_bio)
    assert extracted["full_name"] is not None
    assert len(extracted["claims"]) >= 3

@pytest.mark.asyncio
async def test_gap_analysis_engine_flow():
    # 1. Simulate claims
    sample_claims = [
        {"claim": "PLC troubleshooting and fault finding", "source_citation": "Line 2"},
        {"claim": "Industrial hydraulic systems maintenance", "source_citation": "Line 3"},
        {"claim": "Preventative maintenance execution", "source_citation": "Line 3"},
        {"claim": "Metal welding and fabrication", "source_citation": "Line 4"}
    ]
    
    # 2. Resolve skills and adjacent roles
    resolved, adjacent = await gap_engine.resolve_skills_and_adjacency("prof_test_123", sample_claims)
    assert len(resolved) >= 3
    assert len(adjacent) >= 1
    assert adjacent[0].title == "Industrial Machinery Mechanic / Millwright"
    assert adjacent[0].match_percent > 0

    # 3. Evaluate gap against Millwright
    profile_data = {
        "id": "prof_test_123",
        "full_name": "Sipho Ndlovu",
        "extracted_skills": [s.model_dump() for s in resolved]
    }
    
    evaluation = await gap_engine.evaluate_gap(profile_data, "occ_millwright_3231")
    assert evaluation.essential_match_percent > 0
    assert len(evaluation.matched_essential) >= 3
    assert len(evaluation.missing_essential) > 0
    assert len(evaluation.recommended_pathways) > 0
    assert "Sipho" in evaluation.ai_guidance_summary

if __name__ == "__main__":
    print("Running tests directly...")
    test_db_manager_occupations()
    test_document_extraction_txt()
    asyncio.run(test_ai_competency_extraction())
    asyncio.run(test_gap_analysis_engine_flow())
    print("ALL TESTS PASSED SUCCESSFULLY!")
