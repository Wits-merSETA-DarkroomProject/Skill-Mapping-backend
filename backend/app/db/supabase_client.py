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
        return self.occupations_cache

    def get_occupation_by_id(self, occupation_id: str) -> Optional[Dict[str, Any]]:
        for occ in self.occupations_cache:
            if occ["id"] == occupation_id:
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
                            "concept_uri, preferred_label, alt_labels, skill_type, reuse_level, description"
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
                            "description": item.get("description")
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
        return profile_id

    def get_profile(self, profile_id: str) -> Optional[Dict[str, Any]]:
        return self.in_memory_profiles.get(profile_id)

    def save_gap_run(self, run_data: Dict[str, Any]):
        run_id = run_data["run_id"]
        self.in_memory_runs[run_id] = run_data

    def get_pathway_for_skill(self, skill_id: str) -> Optional[Dict[str, Any]]:
        return self.pathways_cache.get(skill_id)

db_manager = SupabaseManager()
