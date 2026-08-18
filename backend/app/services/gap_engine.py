import uuid
import logging
from typing import List, Dict, Any, Tuple
import numpy as np

from app.db.supabase_client import db_manager
from app.services.ai_service import ai_service
from app.schemas.gap_analysis import (
    ExtractedSkillItem,
    AdjacentOccupation,
    SkillRequirement,
    OccupationSummary,
    SkillMatchResult,
    LearningPathwayItem,
    EvaluationResponse
)

logger = logging.getLogger(__name__)

class GapAnalysisEngine:
    """
    Deterministic Skills Gap Analysis Engine using ESCO Taxonomies.
    Calculates exact Essential vs. Optional requirements, rankings, and pathway attachments.
    """

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
            best_match, score = self._find_best_esco_match(claim_text, all_esco_skills)
            
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
        adjacent_occupations = self._calculate_adjacent_occupations(matched_skill_ids)

        return matched_items, adjacent_occupations

    def _find_best_esco_match(
        self,
        claim_text: str,
        esco_skills: List[Dict[str, Any]]
    ) -> Tuple[Dict[str, Any], float]:
        """
        Computes semantic and keyword proximity between claim and ESCO skills.
        """
        claim_lower = claim_text.lower()
        best_skill = None
        best_score = 0.0

        for skill in esco_skills:
            score = 0.0
            label = skill["label"].lower()
            alt_labels = [a.lower() for a in skill.get("alt_labels", [])]

            # Exact alias hit
            if any(alt in claim_lower or claim_lower in alt for alt in alt_labels):
                score = 0.95
            elif label in claim_lower or claim_lower in label:
                score = 0.90
            else:
                # Word overlap Jaccard
                claim_words = set(claim_lower.split())
                label_words = set(label.split())
                for alt in alt_labels:
                    label_words.update(alt.split())
                
                overlap = len(claim_words.intersection(label_words))
                if overlap > 0:
                    score = overlap / max(len(claim_words), len(label_words))
                    # Boost for important keywords
                    if score > 0.3:
                        score = min(0.85, score + 0.35)

            if score > best_score:
                best_score = score
                best_skill = skill

        return best_skill, best_score

    def _calculate_adjacent_occupations(
        self,
        user_skill_ids: set
    ) -> List[AdjacentOccupation]:
        """
        Ranks all ESCO occupations based on candidate's matched essential skills.
        """
        occupations = db_manager.get_all_occupations()
        results = []

        for occ in occupations:
            essential_skills = [s for s in occ["skills"] if s.get("relation_type") == "essential"]
            total_essential = len(essential_skills)
            
            matched_count = sum(1 for s in essential_skills if s["id"] in user_skill_ids)
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

        matched_essential: List[SkillMatchResult] = []
        missing_essential: List[SkillMatchResult] = []
        matched_optional: List[SkillMatchResult] = []
        missing_optional: List[SkillMatchResult] = []
        recommended_pathways: List[LearningPathwayItem] = []

        essential_reqs = []
        optional_reqs = []

        for skill in occ["skills"]:
            is_essential = skill.get("relation_type", "essential") == "essential"
            skill_id = skill["id"]
            is_matched = skill_id in user_skill_ids

            user_item = user_skill_map.get(skill_id, {})
            match_res = SkillMatchResult(
                skill_id=skill_id,
                preferred_label=skill["label"],
                relation_type="essential" if is_essential else "optional",
                is_matched=is_matched,
                confidence_score=user_item.get("confidence_score"),
                source_citation=user_item.get("source_citation"),
                confidence_tier=user_item.get("confidence_tier")
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
                    # Lookup learning pathway for missing essential skill
                    pathway = db_manager.get_pathway_for_skill(skill_id)
                    if pathway:
                        recommended_pathways.append(LearningPathwayItem(
                            skill_name=skill["label"],
                            course_title=pathway["course_title"],
                            provider_name=pathway["provider_name"],
                            nqf_level=pathway["nqf_level"],
                            funding_scheme=pathway["funding_scheme"],
                            duration_weeks=pathway.get("duration_weeks", 4),
                            description=pathway.get("description")
                        ))
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
            recommended_pathways=recommended_pathways,
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
