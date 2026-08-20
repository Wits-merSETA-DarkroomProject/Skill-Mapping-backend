import uuid
import logging
import asyncio
import json
from typing import List, Dict, Any, Tuple, Optional
import numpy as np

from app.db.supabase_client import db_manager
from app.services.ai_service import ai_service
from app.schemas.gap_analysis import (
    ExtractedSkillItem,
    AdjacentOccupation,
    SkillRequirement,
    OccupationSummary,
    SkillMatchResult,
    #LearningPathwayItem,
    EvaluationResponse
)

logger = logging.getLogger(__name__)

class GapAnalysisEngine:
    """
    Deterministic Skills Gap Analysis Engine using ESCO Taxonomies.
    Calculates exact Essential vs. Optional requirements, rankings, and pathway attachments.
    """

    def __init__(self):
        self.skill_embeddings_cache: Dict[str, List[float]] = {}

    async def resolve_skills_and_adjacency(
        self,
        profile_id: str,
        claims: List[Dict[str, Any]]
    ) -> Tuple[List[ExtractedSkillItem], List[AdjacentOccupation]]:
        """
        Resolves candidate claims into canonical ESCO skills and computes top adjacent occupations.
        """
        all_esco_skills = db_manager.get_all_skills_flat()
        matched_items: List[ExtractedSkillItem] = []
        matched_skill_ids = set()

        for claim_obj in claims:
            claim_text = claim_obj.get("claim", "")
            citation = claim_obj.get("source_citation", "")
            
            # Find best matching ESCO skill
            best_match, score = await self._find_best_esco_match(claim_text, all_esco_skills)
            
            if best_match and score >= 0.50 and best_match["id"] not in matched_skill_ids:
                matched_skill_ids.add(best_match["id"])
                
                tier = "direct" if score >= 0.85 else ("related" if score >= 0.65 else "inferred")
                
                matched_items.append(ExtractedSkillItem(
                    skill_id=best_match["id"],
                    preferred_label=best_match["label"],
                    extracted_claim=claim_text,
                    confidence_score=round(score, 2),
                    confidence_tier=tier,
                    source_citation=citation,
                    skill_type=best_match.get("skill_type", "skill/competence")
                ))

        # Calculate Adjacency across all ESCO occupations
        adjacent_occupations = self._calculate_adjacent_occupations(matched_items)

        return matched_items, adjacent_occupations

    async def _find_best_esco_match(
        self,
        claim_text: str,
        esco_skills: List[Dict[str, Any]]
    ) -> Tuple[Dict[str, Any], float]:
        """
        Computes semantic proximity using embeddings and cosine similarity between claim and ESCO skills.
        Uses token/keyword Jaccard overlap to pre-filter candidate pool when matching against the entire database.
        """
        claim_lower = claim_text.lower()
        if not esco_skills:
            return None, 0.0

        # 1. Pre-filter comparison pool to top 150 candidates using token/keyword overlap to prevent API timeout / rate limits
        if len(esco_skills) > 200:
            STOPWORDS = {"and", "of", "to", "in", "for", "with", "on", "or", "the", "a", "an", "by", "at", "from", "as", "about"}
            claim_words = set(w for w in claim_lower.split() if w not in STOPWORDS)
            candidates = []
            for s in esco_skills:
                label_words = set(s["label"].lower().split())
                for alt in s.get("alt_labels", []):
                    label_words.update(alt.lower().split())
                overlap = len(claim_words.intersection(label_words))
                candidates.append((s, overlap))
            
            candidates.sort(key=lambda x: x[1], reverse=True)
            comparison_pool = [c[0] for c in candidates[:150]]
        else:
            comparison_pool = esco_skills

        # 2. Extract embedding for the claim
        try:
            claim_emb = await ai_service.get_embedding(claim_text)
            if not claim_emb:
                raise ValueError("Empty embedding returned")
            claim_arr = np.array(claim_emb)
            claim_norm = np.linalg.norm(claim_arr)
        except Exception as e:
            logger.warning(f"Embedding extraction failed for '{claim_text}': {e}. Falling back to Jaccard match.")
            return self._find_best_esco_match_jaccard_fallback(claim_text, comparison_pool)

        # 3. Resolve skill embeddings (using cache, DB value, or fetching async)
        for s in comparison_pool:
            if s.get("vector_embedding") and s["id"] not in self.skill_embeddings_cache:
                emb_val = s["vector_embedding"]
                if isinstance(emb_val, str):
                    try:
                        emb_val = json.loads(emb_val)
                    except Exception:
                        try:
                            clean_str = emb_val.strip("[]{}")
                            emb_val = [float(val) for val in clean_str.split(",") if val.strip()]
                        except Exception as e:
                            logger.error(f"Failed parsing vector string: {e}")
                            emb_val = None
                
                if emb_val:
                    self.skill_embeddings_cache[s["id"]] = emb_val

        uncached_skills = [s for s in comparison_pool if s["id"] not in self.skill_embeddings_cache]
        if uncached_skills:
            if len(uncached_skills) > 50:
                logger.warning(f"Found {len(uncached_skills)} uncached skills. Using local mock embeddings to avoid hitting API limits.")
                for s in uncached_skills:
                    self.skill_embeddings_cache[s["id"]] = ai_service._get_deterministic_mock_embedding(s["label"])
            else:
                chunk_size = 100
                for i in range(0, len(uncached_skills), chunk_size):
                    chunk = uncached_skills[i:i + chunk_size]
                    # Combine label and alt_labels to capture all keywords/synonyms in the embedding
                    combined_texts = ["; ".join([s["label"]] + s.get("alt_labels", [])) for s in chunk]
                    tasks = [ai_service.get_embedding(text) for text in combined_texts]
                    embeddings = await asyncio.gather(*tasks, return_exceptions=True)
                    for s, emb in zip(chunk, embeddings):
                        if isinstance(emb, Exception) or not emb:
                            # Fallback mock embedding if API fails
                            emb_list = ai_service._get_deterministic_mock_embedding(s["label"])
                        else:
                            emb_list = emb
                        
                        self.skill_embeddings_cache[s["id"]] = emb_list
                        # Sync back to Supabase in the background
                        try:
                            db_manager.update_skill_embedding(s["id"], emb_list)
                        except Exception as sync_err:
                            logger.warning(f"Background embedding sync failed: {sync_err}")

        # 4. Compute cosine similarity against candidate skills
        best_skill = None
        best_score = 0.0

        for skill in comparison_pool:
            skill_emb = self.skill_embeddings_cache.get(skill["id"])
            if not skill_emb:
                continue
            
            skill_arr = np.array(skill_emb)
            skill_norm = np.linalg.norm(skill_arr)
            if claim_norm == 0 or skill_norm == 0:
                cosine_score = 0.0
            else:
                cosine_score = float(np.dot(claim_arr, skill_arr) / (claim_norm * skill_norm))

            # Hybrid Jaccard fallback for mock environments and keyword match safety
            jaccard_score = self._compute_jaccard_score(claim_text, skill)
            score = max(cosine_score, jaccard_score)

            if score > best_score:
                best_score = score
                best_skill = skill

        return best_skill, best_score

    def _compute_jaccard_score(
        self,
        claim_text: str,
        skill: Dict[str, Any]
    ) -> float:
        claim_lower = claim_text.lower()
        label = skill["label"].lower()
        alt_labels = [a.lower() for a in skill.get("alt_labels", [])]

        if any(alt in claim_lower or claim_lower in alt for alt in alt_labels):
            return 0.95
        if label in claim_lower or claim_lower in label:
            return 0.90

        claim_words = set(claim_lower.split())
        label_words = set(label.split())
        for alt in alt_labels:
            label_words.update(alt.split())
        
        overlap = len(claim_words.intersection(label_words))
        if overlap > 0:
            score = overlap / max(len(claim_words), len(label_words))
            if score > 0.3:
                return min(0.85, score + 0.35)
            return score
        return 0.0

    def _find_best_esco_match_jaccard_fallback(
        self,
        claim_text: str,
        esco_skills: List[Dict[str, Any]]
    ) -> Tuple[Dict[str, Any], float]:
        best_skill = None
        best_score = 0.0
        for skill in esco_skills:
            score = self._compute_jaccard_score(claim_text, skill)
            if score > best_score:
                best_score = score
                best_skill = skill
        return best_skill, best_score

    async def match_skill(
        self,
        claim: str,
        candidates: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Decoupled matcher interface. Receives a skill claim and a list of candidate skills.
        Performs semantic and hybrid ranking, returning the top match with confidence scoring.
        """
        if not candidates:
            return None

        # Clean/Format candidates list if they are in db format (preferred_label, concept_uri)
        formatted_candidates = []
        for c in candidates:
            formatted_candidates.append({
                "id": c.get("id") or c.get("concept_uri"),
                "label": c.get("label") or c.get("preferred_label"),
                "alt_labels": c.get("alt_labels") or ([c.get("alt_names")] if c.get("alt_names") else [])
            })

        best_match, score = await self._find_best_esco_match(claim, formatted_candidates)
        if not best_match or score < 0.50:
            return None

        # Define confidence tiers
        if score >= 0.85:
            confidence = "High"
        elif score >= 0.70:
            confidence = "Medium"
        else:
            confidence = "Low"

        return {
            "id": best_match["id"],
            "label": best_match["label"],
            "score": round(score, 2),
            "confidence": confidence
        }

    def _skills_match_semantically(self, skill_a: Dict[str, Any], skill_b: Dict[str, Any]) -> bool:
        """
        Determines if two skills match semantically via exact labels, synonyms (alt_labels),
        or shared high-value domain keywords.
        """
        # 1. Check ID/URI match
        id_a = skill_a.get("id") or skill_a.get("skill_id") or skill_a.get("concept_uri")
        id_b = skill_b.get("id") or skill_b.get("skill_id") or skill_b.get("concept_uri")
        if id_a and id_b and id_a == id_b:
            return True

        # 2. Check preferred labels
        label_a = (skill_a.get("label") or skill_a.get("preferred_label") or "").lower().strip()
        label_b = (skill_b.get("label") or skill_b.get("preferred_label") or "").lower().strip()
        if not label_a or not label_b:
            return False

        if label_a in label_b or label_b in label_a:
            return True

        # 3. Check alt labels
        alts_a = [a.lower().strip() for a in skill_a.get("alt_labels", []) if a.strip()]
        alts_b = [b.lower().strip() for b in skill_b.get("alt_labels", []) if b.strip()]

        all_a = {label_a} | set(alts_a)
        all_b = {label_b} | set(alts_b)

        if all_a.intersection(all_b):
            return True

        # 4. Check high-value domain keywords
        STOPWORDS = {"and", "of", "to", "in", "for", "with", "on", "or", "the", "a", "an", "by", "at", "from", "as", "about"}
        words_a = set(w for w in label_a.split() if w not in STOPWORDS)
        words_b = set(w for w in label_b.split() if w not in STOPWORDS)

        common = words_a.intersection(words_b)
        if common:
            keywords = {"plc", "hydraulic", "hydraulics", "pneumatic", "pneumatics", "weld", "welding", "audit", "maintenance", "electrical", "drawings", "cnc", "solar"}
            if common.intersection(keywords):
                return True

        return False

    def _calculate_adjacent_occupations(
        self,
        resolved_skills: List[ExtractedSkillItem]
    ) -> List[AdjacentOccupation]:
        """
        Ranks all ESCO occupations based on candidate's matched essential skills.
        Supports both direct ID matching and flexible label/synonym matching to bridge mock occupations and live database skills.
        """
        occupations = db_manager.get_all_occupations()
        results = []

        # Convert resolved skills to dicts and inject alt_labels from the master skills list cache
        all_skills_map = {s["id"]: s for s in db_manager.get_all_skills_flat()}
        resolved_dicts = []
        for s in resolved_skills:
            s_dict = s.model_dump() if hasattr(s, "model_dump") else s
            skill_id = s_dict.get("skill_id") or s_dict.get("id")
            master_skill = all_skills_map.get(skill_id)
            if master_skill:
                s_dict["alt_labels"] = master_skill.get("alt_labels", [])
            resolved_dicts.append(s_dict)

        for occ in occupations:
            essential_skills = [s for s in occ["skills"] if s.get("relation_type") == "essential"]
            total_essential = len(essential_skills)
            
            matched_count = 0
            for ess in essential_skills:
                # Check if this essential skill matches any of our resolved skills
                if any(self._skills_match_semantically(ess, res) for res in resolved_dicts):
                    matched_count += 1

            pct = round((matched_count / total_essential * 100)) if total_essential > 0 else 0

            results.append(AdjacentOccupation(
                occupation_id=occ["id"],
                title=occ["title"],
                isco_group=occ.get("isco_group", "General"),
                category=occ.get("category", "General"),
                match_percent=pct,
                matched_count=matched_count,
                total_essential=total_essential
            ))

        # Sort by match percentage descending
        results.sort(key=lambda x: x.match_percent, reverse=True)
        return results

    async def evaluate_gap(
        self,
        profile_data: Dict[str, Any],
        occupation_id: str
    ) -> EvaluationResponse:
        """
        Performs multi-level gap analysis against target occupation.
        """
        occ = db_manager.get_occupation_by_id(occupation_id)
        if not occ:
            raise ValueError(f"Occupation with ID {occupation_id} not found.")

        extracted_skills_list = profile_data.get("extracted_skills", [])
        user_skill_map = {s["skill_id"]: s for s in extracted_skills_list}
        user_skill_ids = set(user_skill_map.keys())

        # Map all_skills to resolved_dicts items to inject alt_labels
        all_skills_map = {s["id"]: s for s in db_manager.get_all_skills_flat()}
        resolved_dicts = []
        for s in extracted_skills_list:
            s_dict = s.copy() if isinstance(s, dict) else s.model_dump()
            skill_id = s_dict.get("skill_id") or s_dict.get("id")
            master_skill = all_skills_map.get(skill_id)
            if master_skill:
                s_dict["alt_labels"] = master_skill.get("alt_labels", [])
            resolved_dicts.append(s_dict)

        matched_essential: List[SkillMatchResult] = []
        missing_essential: List[SkillMatchResult] = []
        matched_optional: List[SkillMatchResult] = []
        missing_optional: List[SkillMatchResult] = []
        #recommended_pathways: List[LearningPathwayItem] = []

        essential_reqs = []
        optional_reqs = []

        for skill in occ["skills"]:
            is_essential = skill.get("relation_type", "essential") == "essential"
            skill_id = skill["id"]
            
            is_matched = False
            user_item = {}
            # Match by ID or semantically by label/synonyms
            if skill_id in user_skill_ids:
                is_matched = True
                user_item = user_skill_map.get(skill_id, {})
            else:
                for s in resolved_dicts:
                    if self._skills_match_semantically(skill, s):
                        is_matched = True
                        user_item = s
                        break

            match_res = SkillMatchResult(
                skill_id=skill_id,
                preferred_label=skill["label"],
                relation_type="essential" if is_essential else "optional",
                is_matched=is_matched,
                confidence_score=user_item.get("confidence_score") if isinstance(user_item, dict) else getattr(user_item, "confidence_score", None),
                source_citation=user_item.get("source_citation") if isinstance(user_item, dict) else getattr(user_item, "source_citation", None),
                confidence_tier=user_item.get("confidence_tier") if isinstance(user_item, dict) else getattr(user_item, "confidence_tier", None)
            )

            if is_essential:
                essential_reqs.append(SkillRequirement(
                    skill_id=skill["id"],
                    preferred_label=skill["label"],
                    relation_type="essential",
                    importance_score=skill.get("importance_score", 1.0),
                    description=skill.get("description"),
                    alt_labels=skill.get("alt_labels", [])
                ))
                if is_matched:
                    matched_essential.append(match_res)
                else:
                    missing_essential.append(match_res)
                    # # Lookup learning pathway for missing essential skill
                    # pathway = db_manager.get_pathway_for_skill(skill_id)
                    # if pathway:
                    #     #recommended_pathways.append(LearningPathwayItem(
                    #         skill_name=skill["label"],
                    #         course_title=pathway["course_title"],
                    #         provider_name=pathway["provider_name"],
                    #         nqf_level=pathway["nqf_level"],
                    #         funding_scheme=pathway["funding_scheme"],
                    #         duration_weeks=pathway.get("duration_weeks", 4),
                    #         description=pathway.get("description")
                    #     ))
            else:
                optional_reqs.append(SkillRequirement(
                    skill_id=skill["id"],
                    preferred_label=skill["label"],
                    relation_type="optional",
                    importance_score=skill.get("importance_score", 0.5),
                    description=skill.get("description"),
                    alt_labels=skill.get("alt_labels", [])
                ))
                if is_matched:
                    matched_optional.append(match_res)
                else:
                    missing_optional.append(match_res)

        # Calculate exact percentages
        total_ess = len(essential_reqs)
        total_opt = len(optional_reqs)

        ess_pct = round((len(matched_essential) / total_ess) * 100) if total_ess > 0 else 100
        opt_pct = round((len(matched_optional) / total_opt) * 100) if total_opt > 0 else 100
        overall_pct = round(0.8 * ess_pct + 0.2 * opt_pct)

        # AI Guidance Synthesis
        guidance = await ai_service.synthesize_guidance(
            candidate_name=profile_data.get("full_name", "Candidate"),
            occupation_title=occ["title"],
            match_percent=ess_pct,
            matched_skills=[s.preferred_label for s in matched_essential],
            missing_essential=[s.preferred_label for s in missing_essential]
        )

        run_id = f"run_{uuid.uuid4().hex[:12]}"
        
        target_occ_summary = OccupationSummary(
            id=occ["id"],
            title=occ["title"],
            isco_group=occ.get("isco_group", "3231"),
            category=occ.get("category", "General"),
            description=occ.get("description", ""),
            essential_skills=essential_reqs,
            optional_skills=optional_reqs
        )

        response = EvaluationResponse(
            run_id=run_id,
            profile_id=profile_data.get("id", ""),
            target_occupation=target_occ_summary,
            essential_match_percent=ess_pct,
            optional_match_percent=opt_pct,
            overall_match_percent=overall_pct,
            matched_essential=matched_essential,
            missing_essential=missing_essential,
            matched_optional=matched_optional,
            missing_optional=missing_optional,
            #recommended_pathways=recommended_pathways,
            ai_guidance_summary=guidance
        )

        # Save run in DB
        db_manager.save_gap_run({
            "run_id": run_id,
            "profile_id": profile_data.get("id", ""),
            "occupation_id": occ["id"],
            "essential_match_percent": ess_pct,
            "optional_match_percent": opt_pct,
            "overall_match_percent": overall_pct,
            "ai_guidance_summary": guidance
        })

        return response

gap_engine = GapAnalysisEngine()
