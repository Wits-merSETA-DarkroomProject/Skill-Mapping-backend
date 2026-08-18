"""
ESCO Dataset Bulk Ingestion Script
Loads DataFrame/CSV containing the 8 ESCO columns into Supabase in optimized batches.

Expected DataFrame / CSV columns:
['conceptType', 'conceptUri', 'skillType', 'reuseLevel', 'preferredLabel', 'altLabels', 'inScheme', 'description']
"""

import os
import sys
import logging
from typing import Optional, List, Dict, Any
import pandas as pd

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.core.config import settings
from app.db.supabase_client import db_manager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("esco-ingestion")

def ingest_esco_skills_df(df: pd.DataFrame, batch_size: int = 500) -> int:
    """
    Ingests an ESCO DataFrame (up to 13,960+ entries) directly into Supabase.
    """
    if not db_manager.is_connected or not db_manager.client:
        logger.warning("Supabase is not connected. Ingestion requires active Supabase credentials.")
        return 0

    # Ensure required columns exist
    required_cols = ['conceptType', 'conceptUri', 'skillType', 'reuseLevel', 'preferredLabel', 'altLabels', 'inScheme', 'description']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"DataFrame is missing required columns: {missing}")

    logger.info(f"Preparing to ingest {len(df)} ESCO skill records into Supabase...")

    # Fill NaN values
    df_clean = df.fillna({
        'conceptType': 'KnowledgeSkillCompetence',
        'skillType': 'skill/competence',
        'reuseLevel': 'sector-specific',
        'preferredLabel': '',
        'altLabels': '',
        'inScheme': '',
        'description': ''
    })

    total_inserted = 0
    records: List[Dict[str, Any]] = []

    for idx, row in df_clean.iterrows():
        records.append({
            "concept_uri": str(row["conceptUri"]).strip(),
            "concept_type": str(row["conceptType"]).strip(),
            "skill_type": str(row["skillType"]).strip() if row["skillType"] else "skill/competence",
            "reuse_level": str(row["reuseLevel"]).strip() if row["reuseLevel"] else "sector-specific",
            "preferred_label": str(row["preferredLabel"]).strip(),
            "alt_labels": str(row["altLabels"]) if row["altLabels"] else "",
            "in_scheme": str(row["inScheme"]).strip(),
            "description": str(row["description"]).strip()
        })

        if len(records) >= batch_size:
            _upsert_batch(records)
            total_inserted += len(records)
            logger.info(f"Ingested {total_inserted}/{len(df)} records...")
            records = []

    if records:
        _upsert_batch(records)
        total_inserted += len(records)

    logger.info(f"Successfully finished ingesting {total_inserted} ESCO skills into Supabase!")
    return total_inserted

def _upsert_batch(batch: List[Dict[str, Any]]):
    try:
        db_manager.client.table("esco_skills").upsert(batch, on_conflict="concept_uri").execute()
    except Exception as e:
        logger.error(f"Failed to upsert batch: {e}")
        raise e

def ingest_from_csv_file(csv_path: str, batch_size: int = 500):
    if not os.path.exists(csv_path):
        logger.error(f"CSV file not found at: {csv_path}")
        return
    logger.info(f"Reading CSV from {csv_path}...")
    df = pd.read_csv(csv_path)
    ingest_esco_skills_df(df, batch_size=batch_size)

if __name__ == "__main__":
    default_csv = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "files", "df_esco_processed.csv")
    csv_file = sys.argv[1] if len(sys.argv) > 1 else default_csv
    if os.path.exists(csv_file):
        ingest_from_csv_file(csv_file)
    else:
        print(f"Error: CSV file not found at: {csv_file}")
        print("Usage: python -m app.db.ingest_esco_csv [path/to/csv]")
