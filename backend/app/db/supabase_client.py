import logging
from typing import Optional, Dict, Any, List
from supabase import create_client, Client
from app.core.config import settings
from app.db.seed_esco_data import ESCO_OCCUPATIONS, LEARNING_PATHWAYS_MAP

logger = logging.getLogger(__name__)

class SupabaseManager:
    """
    Manages connections to Supabase PostgreSQL database.
    Queries the live `skills` table (13,939 records) and handles profiles/runs.
    """
    def __init__(self):
        self.client: Optional[Client] = None
        self._is_connected: bool = False
        
        # In-Memory Cache Store (fallback & fast querying)
        self.in_memory_profiles: Dict[str, Dict[str, Any]] = {}
        self.in_memory_runs: Dict[str, Dict[str, Any]] = {}
        self.occupations_cache: List[Dict[str, Any]] = ESCO_OCCUPATIONS
        self.pathways_cache: Dict[str, Dict[str, Any]] = LEARNING_PATHWAYS_MAP

        self._init_client()

    def _init_client(self):
        if settings.SUPABASE_URL and (settings.SUPABASE_SECRET_KEY or settings.SUPABASE_KEY):
            key = settings.SUPABASE_SECRET_KEY or settings.SUPABASE_KEY
            try:
                self.client = create_client(settings.SUPABASE_URL, key)
                self._is_connected = True
                logger.info("Successfully connected to Supabase.")
            except Exception as e:
                logger.warning(f"Could not connect to Supabase: {e}. Falling back to in-memory store.")
                self._is_connected = False
        else:
            logger.info("Supabase credentials not set. Running in local in-memory mode.")
            self._is_connected = False

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    # -------------------------------------------------------------------------
    # Occupations & Taxonomies
    # -------------------------------------------------------------------------
    def get_all_occupations(self) -> List[Dict[str, Any]]:
        if self._is_connected and self.client:
            if not hasattr(self, "_db_occupations_cache") or self._db_occupations_cache is None:
                try:
                    logger.info("Fetching all occupations from Supabase...")
                    # Try querying the 'occupations' table with nested 'occupation_skills' and 'skills'
                    resp = self.client.table("occupations").select(
                        "concept_uri, preferred_label, alt_labels, description, isco_group, "
                        "occupation_skills(relation_type, importance_score, skill_uri, skills(preferred_label, alt_labels, skill_type, description))"
                    ).execute()
                    data = resp.data or []
                    relation_key = "occupation_skills"
                    skills_key = "skills"

                    formatted_occs = []
                    for item in (data or []):
                        skills_list = []
                        for os in item.get(relation_key) or []:
                            sk_data = os.get(skills_key) or {}
                            alt_labels_str = sk_data.get("alt_labels") or ""
                            alt_list = [a.strip() for a in alt_labels_str.split("\n") if a.strip()]
                            skills_list.append({
                                "id": os.get("skill_uri"),
                                "label": sk_data.get("preferred_label") or "",
                                "alt_labels": alt_list,
                                "relation_type": os.get("relation_type", "essential"),
                                "importance_score": os.get("importance_score", 1.0),
                                "skill_type": sk_data.get("skill_type") or "skill/competence",
                                "description": sk_data.get("description") or ""
                            })

                        # Determine category dynamically from ISCO-08 group prefix
                        isco_val = str(item.get("isco_group") or "")
                        category_val = "General"
                        if isco_val:
                            first_digit = isco_val[0]
                            if first_digit == "3":
                                category_val = "Technicians / Associate Professionals"
                            elif first_digit == "7":
                                category_val = "Trade / Maintenance"
                            elif first_digit == "8":
                                category_val = "Operators / Assemblers"

                        formatted_occs.append({
                            "id": item["concept_uri"],
                            "concept_uri": item["concept_uri"],
                            "title": item["preferred_label"],
                            "isco_group": isco_val or "General",
                            "category": category_val,
                            "description": item.get("description") or "",
                            "skills": skills_list
                        })
                    self._db_occupations_cache = formatted_occs
                    logger.info(f"Successfully loaded and cached {len(self._db_occupations_cache)} occupations from Supabase.")
                except Exception as e:
                    logger.error(f"Error caching occupations from Supabase: {e}")
                    self._db_occupations_cache = None

            if self._db_occupations_cache:
                return self._db_occupations_cache

        return self.occupations_cache

    def get_occupation_by_id(self, occupation_id: str) -> Optional[Dict[str, Any]]:
        all_occs = self.get_all_occupations()
        for occ in all_occs:
            if occ["id"] == occupation_id or occ["concept_uri"] == occupation_id:
                return occ
        return None

    def get_all_skills_flat(self) -> List[Dict[str, Any]]:
        """Returns a flat, deduplicated list of canonical ESCO skills."""
        if self._is_connected and self.client:
            if not hasattr(self, "_db_skills_cache") or self._db_skills_cache is None:
                try:
                    logger.info("Fetching all skills from Supabase...")
                    all_skills = []
                    limit = 1000
                    offset = 0
                    while True:
                        resp = self.client.table("skills").select(
                            "concept_uri, preferred_label, alt_labels, skill_type, reuse_level, description, vector_embedding"
                        ).range(offset, offset + limit - 1).execute()
                        data = resp.data
                        if not data:
                            break
                        all_skills.extend(data)
                        if len(data) < limit:
                            break
                        offset += limit
                    
                    formatted_skills = []
                    for item in all_skills:
                        alt_labels_str = item.get("alt_labels") or ""
                        alt_list = [a.strip() for a in alt_labels_str.split("\n") if a.strip()]
                        formatted_skills.append({
                            "id": item["concept_uri"],
                            "label": item["preferred_label"],
                            "alt_labels": alt_list,
                            "skill_type": item.get("skill_type"),
                            "reuse_level": item.get("reuse_level"),
                            "description": item.get("description"),
                            "vector_embedding": item.get("vector_embedding")
                        })
                    self._db_skills_cache = formatted_skills
                    logger.info(f"Successfully loaded and cached {len(self._db_skills_cache)} skills from Supabase.")
                except Exception as e:
                    logger.error(f"Error caching skills from Supabase: {e}")
                    self._db_skills_cache = None

            if self._db_skills_cache:
                return self._db_skills_cache

        seen = set()
        skills = []
        for occ in self.occupations_cache:
            for sk in occ["skills"]:
                if sk["id"] not in seen:
                    seen.add(sk["id"])
                    skills.append(sk)
        return skills

    def search_skills_in_supabase(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Queries the live 13,939 Supabase skills table by keyword/trigram."""
        if not self._is_connected or not self.client:
            return []
        try:
            resp = self.client.table("skills").select(
                "concept_uri, preferred_label, skill_type, reuse_level, alt_labels, description"
            ).ilike("preferred_label", f"%{query}%").limit(limit).execute()
            
            # Map database columns back to standard dictionary format
            results = []
            for item in (resp.data or []):
                alt_labels_str = item.get("alt_labels") or ""
                alt_list = [a.strip() for a in alt_labels_str.split("\n") if a.strip()]
                results.append({
                    "id": item["concept_uri"],
                    "label": item["preferred_label"],
                    "skill_type": item.get("skill_type"),
                    "reuse_level": item.get("reuse_level"),
                    "alt_labels": alt_list,
                    "description": item.get("description")
                })
            return results
        except Exception as e:
            logger.error(f"Error querying Supabase skills: {e}")
            return []

    # -------------------------------------------------------------------------
    # Profiles & Gap Analysis Runs
    # -------------------------------------------------------------------------
    def save_profile(self, profile_data: Dict[str, Any]) -> str:
        profile_id = profile_data["id"]
        self.in_memory_profiles[profile_id] = profile_data
        
        if self._is_connected and self.client:
            try:
                # 1. Upsert user profile
                prof_record = {
                    "id": profile_id,
                    "full_name": profile_data.get("full_name") or "Candidate",
                    "cv_file_name": profile_data.get("cv_file_name"),
                    "raw_text": profile_data.get("raw_text"),
                    "linkedin_url": profile_data.get("linkedin_url"),
                    "inferred_experience_summary": profile_data.get("inferred_experience_summary"),
                    "updated_at": "now()"
                }
                self.client.table("user_profiles").upsert(prof_record).execute()
                
                # 2. Insert matched skills (delete old ones first to allow replacement)
                self.client.table("user_matched_skills").delete().eq("profile_id", profile_id).execute()
                
                skills_records = []
                for s in profile_data.get("extracted_skills") or []:
                    skills_records.append({
                        "profile_id": profile_id,
                        "skill_uri": s["skill_id"],
                        "extracted_claim": s.get("extracted_claim") or "",
                        "source_citation": s.get("source_citation") or "",
                        "confidence_score": float(s.get("confidence_score") or 1.0),
                        "confidence_tier": s.get("confidence_tier") or "direct"
                    })
                if skills_records:
                    self.client.table("user_matched_skills").insert(skills_records).execute()
            except Exception as e:
                logger.error(f"Error saving profile to Supabase: {e}")
                
        return profile_id

    def get_profile(self, profile_id: str) -> Optional[Dict[str, Any]]:
        # 1. Try to fetch from Supabase
        if self._is_connected and self.client:
            try:
                prof_resp = self.client.table("user_profiles").select("*").eq("id", profile_id).execute()
                if prof_resp.data:
                    prof_data = prof_resp.data[0]
                    # Fetch matched skills with inner skills attributes
                    skills_resp = self.client.table("user_matched_skills").select(
                        "skill_uri, extracted_claim, source_citation, confidence_score, confidence_tier, "
                        "skills(preferred_label, skill_type, description)"
                    ).eq("profile_id", profile_id).execute()
                    
                    extracted_skills = []
                    for sk in (skills_resp.data or []):
                        sk_details = sk.get("skills") or {}
                        extracted_skills.append({
                            "skill_id": sk["skill_uri"],
                            "preferred_label": sk_details.get("preferred_label") or "",
                            "extracted_claim": sk["extracted_claim"],
                            "confidence_score": sk["confidence_score"],
                            "confidence_tier": sk["confidence_tier"],
                            "source_citation": sk["source_citation"],
                            "skill_type": sk_details.get("skill_type") or "skill/competence",
                            "description": sk_details.get("description") or ""
                        })
                    
                    return {
                        "id": prof_data["id"],
                        "full_name": prof_data["full_name"],
                        "cv_file_name": prof_data["cv_file_name"],
                        "raw_text": prof_data["raw_text"],
                        "linkedin_url": prof_data["linkedin_url"],
                        "inferred_experience_summary": prof_data["inferred_experience_summary"],
                        "extracted_skills": extracted_skills
                    }
            except Exception as e:
                logger.error(f"Error fetching profile from Supabase: {e}")

        if profile_id in self.in_memory_profiles:
            return self.in_memory_profiles[profile_id]
        
        # Fallback to load from mock_profiles.json if present
        import json
        from pathlib import Path
        mock_file = Path(__file__).parent / "mock_profiles.json"
        if mock_file.exists():
            try:
                with open(mock_file, "r", encoding="utf-8") as f:
                    mock_data = json.load(f)
                    if profile_id in mock_data:
                        return mock_data[profile_id]
            except Exception as e:
                logger.error(f"Error reading mock_profiles.json: {e}")
        return None

    def save_gap_run(self, run_data: Dict[str, Any]):
        run_id = run_data["run_id"]
        self.in_memory_runs[run_id] = run_data
        
        if self._is_connected and self.client:
            try:
                db_record = {
                    "run_id": run_id,
                    "profile_id": run_data["profile_id"],
                    "occupation_uri": run_data["target_occupation"]["id"] or run_data["target_occupation"]["concept_uri"],
                    "essential_match_percent": int(run_data["essential_match_percent"]),
                    "optional_match_percent": int(run_data["optional_match_percent"]),
                    "overall_match_percent": int(run_data["overall_match_percent"]),
                    "matched_essential": run_data.get("matched_essential") or [],
                    "missing_essential": run_data.get("missing_essential") or [],
                    "matched_optional": run_data.get("matched_optional") or [],
                    "missing_optional": run_data.get("missing_optional") or [],
                    "ai_guidance_summary": run_data.get("ai_guidance_summary") or ""
                }
                self.client.table("gap_analysis_runs").upsert(db_record, on_conflict="run_id").execute()
            except Exception as e:
                logger.error(f"Error saving gap analysis run to Supabase: {e}")

    def get_pathway_for_skill(self, skill_id: str) -> Optional[Dict[str, Any]]:
        return self.pathways_cache.get(skill_id)

    def update_skill_embedding(self, skill_uri: str, embedding: List[float]):
        """Saves a pre-computed vector embedding to the database for a skill."""
        if self._is_connected and self.client:
            try:
                self.client.table("skills").update({"vector_embedding": embedding}).eq("concept_uri", skill_uri).execute()
                # Also update our in-memory cache if we have it
                if hasattr(self, "_db_skills_cache") and self._db_skills_cache is not None:
                    for s in self._db_skills_cache:
                        if s["id"] == skill_uri:
                            s["vector_embedding"] = embedding
                            break
            except Exception as e:
                logger.error(f"Error updating skill embedding in DB for {skill_uri}: {e}")

db_manager = SupabaseManager()
