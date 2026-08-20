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
    # assert len(evaluation.recommended_pathways) > 0
    assert "Sipho" in evaluation.ai_guidance_summary

@pytest.mark.asyncio
async def test_decoupled_matcher():
    candidates = [
        {"id": "sk_python", "label": "Python", "alt_labels": ["Python programming", "Python language"]},
        {"id": "sk_sql", "label": "SQL", "alt_labels": ["SQL databases", "structured query language"]},
        {"id": "sk_ml", "label": "machine learning", "alt_labels": ["Deep learning", "neural networks"]},
        {"id": "sk_data_vis", "label": "data visualisation", "alt_labels": ["Tableau dashboards", "charts"]}
    ]

    # 1. Test "Python programming" -> "Python"
    res1 = await gap_engine.match_skill("Python programming", candidates)
    assert res1 is not None
    assert res1["label"] == "Python"
    assert res1["confidence"] == "High"

    # 2. Test "SQL databases" -> "SQL"
    res2 = await gap_engine.match_skill("SQL databases", candidates)
    assert res2 is not None
    assert res2["label"] == "SQL"
    assert res2["confidence"] == "High"

    # 3. Test "Deep learning" -> "machine learning"
    res3 = await gap_engine.match_skill("Deep learning", candidates)
    assert res3 is not None
    assert res3["label"] == "machine learning"
    assert res3["confidence"] == "High"

    # 4. Test "Tableau dashboards" -> "data visualisation"
    res4 = await gap_engine.match_skill("Tableau dashboards", candidates)
    assert res4 is not None
    assert res4["label"] == "data visualisation"
    assert res4["confidence"] == "High"

if __name__ == "__main__":
    print("Running tests directly...")
    test_db_manager_occupations()
    test_document_extraction_txt()
    asyncio.run(test_ai_competency_extraction())
    asyncio.run(test_gap_analysis_engine_flow())
    asyncio.run(test_decoupled_matcher())
    print("ALL TESTS PASSED SUCCESSFULLY!")
