import os
import logging
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query

from app.services.ingestion_service import ingestion_service
from app.db.supabase_client import db_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingestion", tags=["Data Ingestion & ETL"])

@router.post("/upload")
async def ingest_single_file(
    file: UploadFile = File(...),
    batch_size: int = Form(500)
):
    """
    Ingests a single CSV, Excel, or JSON dataset into Supabase in optimized batches.
    Automatically detects whether it contains ESCO skills or occupations.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    file_bytes = await file.read()
    result = ingestion_service.ingest_bytes(file_bytes, file.filename, batch_size=batch_size)

    if not result.get("success", False) and result.get("error"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result

@router.post("/batch-upload")
async def ingest_batch_files(
    files: List[UploadFile] = File(...),
    batch_size: int = Form(500)
):
    """
    Ingests multiple files in a single batch request (e.g. skills.csv + occupations.csv).
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    file_tuples = []
    for f in files:
        if f.filename:
            content = await f.read()
            file_tuples.append((content, f.filename))

    result = ingestion_service.ingest_batch_files(file_tuples, batch_size=batch_size)
    return result

@router.post("/trigger-scan")
async def trigger_dropzone_scan(
    directory_path: str = Form("ingestion_dropzone"),
    processed_dir: Optional[str] = Form("ingestion_dropzone/processed")
):
    """
    Scans a local directory on the server, automatically ingesting any CSV/XLSX/JSON files found.
    """
    result = ingestion_service.scan_and_ingest_directory(directory_path, processed_dir=processed_dir)
    return result

@router.get("/status")
async def get_ingestion_status():
    """
    Returns current count and health status of ingested datasets in Supabase.
    """
    total_skills_count = 0
    total_occupations_count = 0

    if db_manager.is_connected and db_manager.client:
        try:
            sk_resp = db_manager.client.table("skills").select("concept_uri", count="exact").head().execute()
            occ_resp = db_manager.client.table("occupations").select("concept_uri", count="exact").head().execute()
            total_skills_count = getattr(sk_resp, "count", 0) or 0
            total_occupations_count = getattr(occ_resp, "count", 0) or 0
        except Exception as e:
            logger.warning(f"Could not fetch Supabase count: {e}")

    return {
        "supabase_connected": db_manager.is_connected,
        "supabase_skills_count": total_skills_count,
        "supabase_occupations_count": total_occupations_count,
        "in_memory_occupations_count": len(db_manager.get_all_occupations()),
        "in_memory_skills_count": len(db_manager.get_all_skills_flat()),
        "supported_formats": [".csv", ".xlsx", ".xls", ".json", ".parquet"]
    }
