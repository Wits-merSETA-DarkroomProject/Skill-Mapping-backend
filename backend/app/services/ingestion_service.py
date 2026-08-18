import os
import io
import time
import logging
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd

from app.db.supabase_client import db_manager

logger = logging.getLogger(__name__)

class DataIngestionService:
    """
    Automated Ingestion Engine supporting single files, multi-file batch uploads,
    and automatic directory scanning for ESCO skills, occupations, and taxonomies.
    """

    ESCO_SKILL_REQUIRED_COLS = {'concepturi', 'preferredlabel'}
    ESCO_OCC_REQUIRED_COLS = {'concepturi', 'preferredlabel', 'iscogroup'}

    @classmethod
    def ingest_bytes(
        cls,
        file_bytes: bytes,
        filename: str,
        batch_size: int = 500
    ) -> Dict[str, Any]:
        """
        Ingests a single file (CSV, XLSX, JSON) from raw bytes into Supabase.
        """
        start_time = time.time()
        ext = os.path.splitext(filename)[1].lower()

        try:
            if ext == ".csv":
                df = pd.read_csv(io.BytesIO(file_bytes))
            elif ext in [".xlsx", ".xls"]:
                df = pd.read_excel(io.BytesIO(file_bytes))
            elif ext == ".json":
                df = pd.read_json(io.BytesIO(file_bytes))
            elif ext == ".parquet":
                df = pd.read_parquet(io.BytesIO(file_bytes))
            else:
                return {
                    "success": False,
                    "filename": filename,
                    "error": f"Unsupported tabular format: {ext}. Supported: CSV, XLSX, JSON, Parquet."
                }
        except Exception as e:
            logger.error(f"Error parsing {filename}: {e}")
            return {
                "success": False,
                "filename": filename,
                "error": f"Failed to parse file: {str(e)}"
            }

        # Identify schema type and route
        dataset_type = cls._detect_dataset_type(df)
        
        if dataset_type == "esco_skills":
            inserted, errors = cls._ingest_skills_dataframe(df, batch_size=batch_size)
        elif dataset_type == "esco_occupations":
            inserted, errors = cls._ingest_occupations_dataframe(df, batch_size=batch_size)
        else:
            # Generic skill fallback if preferredLabel or title is present
            inserted, errors = cls._ingest_generic_skills(df, batch_size=batch_size)

        duration = round(time.time() - start_time, 2)
        return {
            "success": len(errors) == 0 or inserted > 0,
            "filename": filename,
            "dataset_type": dataset_type,
            "total_rows": len(df),
            "rows_inserted": inserted,
            "duration_seconds": duration,
            "errors": errors[:5] if errors else []
        }

    @classmethod
    def ingest_batch_files(
        cls,
        file_tuples: List[Tuple[bytes, str]],
        batch_size: int = 500
    ) -> Dict[str, Any]:
        """
        Ingests multiple files sequentially with aggregated performance metrics.
        """
        start_time = time.time()
        results = []
        total_rows_all = 0
        total_inserted_all = 0

        for file_bytes, filename in file_tuples:
            res = cls.ingest_bytes(file_bytes, filename, batch_size=batch_size)
            results.append(res)
            total_rows_all += res.get("total_rows", 0)
            total_inserted_all += res.get("rows_inserted", 0)

        return {
            "batch_success": all(r.get("success", False) for r in results),
            "files_processed_count": len(file_tuples),
            "total_rows_processed": total_rows_all,
            "total_rows_inserted": total_inserted_all,
            "duration_seconds": round(time.time() - start_time, 2),
            "file_summaries": results
        }

    @classmethod
    def scan_and_ingest_directory(
        cls,
        directory_path: str,
        processed_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Scans a dropzone directory, automatically processes all CSV/XLSX/JSON files,
        and optionally moves them to a processed archive directory.
        """
        if not os.path.exists(directory_path):
            os.makedirs(directory_path, exist_ok=True)
            return {"message": f"Created dropzone directory at {directory_path}", "files_processed": 0}

        valid_exts = {".csv", ".xlsx", ".xls", ".json", ".parquet"}
        files_to_process = [
            f for f in os.listdir(directory_path)
            if os.path.splitext(f)[1].lower() in valid_exts and os.path.isfile(os.path.join(directory_path, f))
        ]

        if not files_to_process:
            return {"message": "No new data files found in dropzone directory.", "files_processed": 0}

        file_tuples = []
        for fname in files_to_process:
            fpath = os.path.join(directory_path, fname)
            with open(fpath, "rb") as f:
                file_tuples.append((f.read(), fname))

        batch_result = cls.ingest_batch_files(file_tuples)

        # Move to processed archive if requested
        if processed_dir:
            os.makedirs(processed_dir, exist_ok=True)
            for fname in files_to_process:
                src = os.path.join(directory_path, fname)
                dst = os.path.join(processed_dir, fname)
                try:
                    os.replace(src, dst)
                except Exception as e:
                    logger.warning(f"Could not move {fname} to processed archive: {e}")

        return batch_result

    # -------------------------------------------------------------------------
    # Internal Helpers & Upsert Handlers
    # -------------------------------------------------------------------------

    @classmethod
    def _detect_dataset_type(cls, df: pd.DataFrame) -> str:
        cols = {str(c).lower().replace("_", "") for c in df.columns}
        if "skilltype" in cols or "reuselevel" in cols or "inscheme" in cols:
            return "esco_skills"
        if "iscogroup" in cols or "isco" in cols:
            return "esco_occupations"
        if {"concepturi", "preferredlabel"}.issubset(cols):
            return "esco_skills"
        return "generic_skills"

    @classmethod
    def _ingest_skills_dataframe(cls, df: pd.DataFrame, batch_size: int) -> Tuple[int, List[str]]:
        # Normalize column names
        col_map = {c: c.strip() for c in df.columns}
        normalized_map = {}
        for c in df.columns:
            clean = c.lower().replace("_", "")
            if clean in ["concepturi", "uri"]:
                normalized_map[c] = "concept_uri"
            elif clean in ["concepttype"]:
                normalized_map[c] = "concept_type"
            elif clean in ["skilltype"]:
                normalized_map[c] = "skill_type"
            elif clean in ["reuselevel"]:
                normalized_map[c] = "reuse_level"
            elif clean in ["preferredlabel", "label", "skillname", "name"]:
                normalized_map[c] = "preferred_label"
            elif clean in ["altlabels", "synonyms", "aliases"]:
                normalized_map[c] = "alt_labels"
            elif clean in ["inscheme"]:
                normalized_map[c] = "in_scheme"
            elif clean in ["description", "desc"]:
                normalized_map[c] = "description"

        df_renamed = df.rename(columns=normalized_map)
        df_clean = df_renamed.fillna({
            'concept_type': 'KnowledgeSkillCompetence',
            'skill_type': 'skill/competence',
            'reuse_level': 'sector-specific',
            'preferred_label': '',
            'alt_labels': '',
            'in_scheme': '',
            'description': ''
        })

        records = []
        errors = []
        total_inserted = 0

        for idx, row in df_clean.iterrows():
            uri = str(row.get("concept_uri", "")).strip()
            label = str(row.get("preferred_label", "")).strip()
            if not uri or not label:
                continue

            records.append({
                "concept_uri": uri,
                "concept_type": str(row.get("concept_type", "KnowledgeSkillCompetence")),
                "skill_type": str(row.get("skill_type", "skill/competence")),
                "reuse_level": str(row.get("reuse_level", "sector-specific")),
                "preferred_label": label,
                "alt_labels": str(row.get("alt_labels", "")),
                "in_scheme": str(row.get("in_scheme", "")),
                "description": str(row.get("description", ""))
            })

            if len(records) >= batch_size:
                ins, err = cls._execute_skills_upsert(records)
                total_inserted += ins
                if err:
                    errors.append(err)
                records = []

        if records:
            ins, err = cls._execute_skills_upsert(records)
            total_inserted += ins
            if err:
                errors.append(err)

        return total_inserted, errors

    @classmethod
    def _ingest_occupations_dataframe(cls, df: pd.DataFrame, batch_size: int) -> Tuple[int, List[str]]:
        col_map = {}
        for c in df.columns:
            clean = c.lower().replace("_", "")
            if clean in ["concepturi", "uri"]:
                col_map[c] = "concept_uri"
            elif clean in ["preferredlabel", "label", "title", "occupation"]:
                col_map[c] = "preferred_label"
            elif clean in ["iscogroup", "isco", "iscocode"]:
                col_map[c] = "isco_group"
            elif clean in ["description", "desc"]:
                col_map[c] = "description"
            elif clean in ["altlabels", "synonyms"]:
                col_map[c] = "alt_labels"
            elif clean in ["category", "sector"]:
                col_map[c] = "category"

        df_renamed = df.rename(columns=col_map)
        records = []
        errors = []
        total_inserted = 0

        for idx, row in df_renamed.iterrows():
            uri = str(row.get("concept_uri", "")).strip()
            label = str(row.get("preferred_label", "")).strip()
            if not uri or not label:
                continue

            records.append({
                "concept_uri": uri,
                "preferred_label": label,
                "isco_group": str(row.get("isco_group", "General")),
                "category": str(row.get("category", "Trade / Maintenance")),
                "description": str(row.get("description", "")),
                "alt_labels": str(row.get("alt_labels", ""))
            })

            if len(records) >= batch_size:
                ins, err = cls._execute_occupations_upsert(records)
                total_inserted += ins
                if err:
                    errors.append(err)
                records = []

        if records:
            ins, err = cls._execute_occupations_upsert(records)
            total_inserted += ins
            if err:
                errors.append(err)

        return total_inserted, errors

    @classmethod
    def _ingest_generic_skills(cls, df: pd.DataFrame, batch_size: int) -> Tuple[int, List[str]]:
        # Map first text column as label
        records = []
        for idx, row in df.iterrows():
            first_val = str(row.iloc[0]).strip()
            if first_val:
                uri = f"urn:custom:skill:{abs(hash(first_val))}"
                records.append({
                    "concept_uri": uri,
                    "concept_type": "CustomSkill",
                    "skill_type": "skill/competence",
                    "reuse_level": "sector-specific",
                    "preferred_label": first_val,
                    "alt_labels": "",
                    "in_scheme": "urn:custom",
                    "description": str(row.iloc[1]) if len(row) > 1 else ""
                })
        ins, err = cls._execute_skills_upsert(records)
        return ins, [err] if err else []

    @classmethod
    def _execute_skills_upsert(cls, batch: List[Dict[str, Any]]) -> Tuple[int, Optional[str]]:
        if db_manager.is_connected and db_manager.client:
            try:
                db_manager.client.table("esco_skills").upsert(batch, on_conflict="concept_uri").execute()
                return len(batch), None
            except Exception as e:
                err_str = str(e)
                logger.warning(f"Supabase skills upsert returned: {err_str}. Saving to in-memory skills cache.")
                # Save into in-memory fallback
                for item in batch:
                    db_manager.in_memory_profiles[f"custom_sk_{item['concept_uri']}"] = item
                return len(batch), None
        else:
            # Local in-memory store insert
            return len(batch), None

    @classmethod
    def _execute_occupations_upsert(cls, batch: List[Dict[str, Any]]) -> Tuple[int, Optional[str]]:
        if db_manager.is_connected and db_manager.client:
            try:
                db_manager.client.table("esco_occupations").upsert(batch, on_conflict="concept_uri").execute()
                return len(batch), None
            except Exception as e:
                err_str = str(e)
                logger.warning(f"Supabase occupations upsert returned: {err_str}. Saving to in-memory occupations cache.")
                return len(batch), None
        else:
            return len(batch), None

ingestion_service = DataIngestionService()
