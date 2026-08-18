import pytest
import io
import pandas as pd
from app.services.ingestion_service import ingestion_service

def test_ingest_single_csv_bytes():
    # Sample ESCO 8-column CSV
    csv_content = """conceptType,conceptUri,skillType,reuseLevel,preferredLabel,altLabels,inScheme,description
KnowledgeSkillCompetence,http://data.europa.eu/esco/skill/test-01,skill/competence,sector-specific,operate lathe machines,lathe operator\\nturning,http://data.europa.eu/esco/concept-scheme/skills,Operate manual and CNC turning lathes.
KnowledgeSkillCompetence,http://data.europa.eu/esco/skill/test-02,skill/competence,cross-sector,conduct electrical tests,test circuits\\nmultimeter diagnostics,http://data.europa.eu/esco/concept-scheme/skills,Perform voltage and insulation testing.
"""
    result = ingestion_service.ingest_bytes(csv_content.encode("utf-8"), "esco_sample.csv")
    assert result["success"] is True
    assert result["total_rows"] == 2
    assert result["dataset_type"] == "esco_skills"
    assert result["rows_inserted"] == 2

def test_ingest_batch_multi_files():
    csv1 = """conceptType,conceptUri,skillType,reuseLevel,preferredLabel,altLabels,inScheme,description
KnowledgeSkillCompetence,http://data.europa.eu/esco/skill/batch-01,skill/competence,sector-specific,calibrate sensors,sensor calibration,http://data.europa.eu/esco/concept-scheme/skills,Calibrate thermal and pressure sensors.
"""
    csv2 = """conceptType,conceptUri,skillType,reuseLevel,preferredLabel,altLabels,inScheme,description
KnowledgeSkillCompetence,http://data.europa.eu/esco/skill/batch-02,skill/competence,sector-specific,solder electronic components,soldering,http://data.europa.eu/esco/concept-scheme/skills,Solder PCB through-hole pins.
"""
    file_tuples = [
        (csv1.encode("utf-8"), "file_1.csv"),
        (csv2.encode("utf-8"), "file_2.csv")
    ]
    
    batch_res = ingestion_service.ingest_batch_files(file_tuples)
    assert batch_res["batch_success"] is True
    assert batch_res["files_processed_count"] == 2
    assert batch_res["total_rows_processed"] == 2
    assert batch_res["total_rows_inserted"] == 2

def test_ingest_excel_bytes():
    df = pd.DataFrame({
        "conceptType": ["KnowledgeSkillCompetence"],
        "conceptUri": ["http://data.europa.eu/esco/skill/excel-01"],
        "skillType": ["skill/competence"],
        "reuseLevel": ["sector-specific"],
        "preferredLabel": ["diagnose hydraulic pumps"],
        "altLabels": ["hydraulic pump testing"],
        "inScheme": ["http://data.europa.eu/esco/concept-scheme/skills"],
        "description": ["Inspect flow rates and pressures on hydraulic gear pumps."]
    })
    
    excel_buffer = io.BytesIO()
    df.to_excel(excel_buffer, index=False)
    excel_bytes = excel_buffer.getvalue()

    result = ingestion_service.ingest_bytes(excel_bytes, "skills_excel.xlsx")
    assert result["success"] is True
    assert result["total_rows"] == 1
    assert result["rows_inserted"] == 1
