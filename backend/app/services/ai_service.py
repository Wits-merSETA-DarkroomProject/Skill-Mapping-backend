import logging
import json
import re
from typing import List, Dict, Any, Optional
import httpx
import numpy as np

from app.core.config import settings

logger = logging.getLogger(__name__)

class AIService:
    """
    Handles AI-powered skill extraction, embedding generation, and career advisory synthesis.
    Supports Groq (Llama 3.3/3.1), OpenAI, Gemini, and local mock fallback.
    """

    def __init__(self):
        self._resolve_provider()

    def _resolve_provider(self):
        self.provider = settings.AI_PROVIDER.lower()
        if settings.GROQ_API_KEY and (self.provider == "groq" or self.provider == "mock"):
            self.provider = "groq"
        elif settings.OPENAI_API_KEY and (self.provider == "openai" or self.provider == "mock"):
            self.provider = "openai"
        elif settings.GEMINI_API_KEY and (self.provider == "gemini" or self.provider == "mock"):
            self.provider = "gemini"

    # -------------------------------------------------------------------------
    # 1. Competency Claims Extraction
    # -------------------------------------------------------------------------
    async def extract_competencies(self, full_text: str) -> Dict[str, Any]:
        """
        Parses raw text into structured competency claims with source evidence.
        """
        self._resolve_provider()
        
        if self.provider == "groq" and settings.GROQ_API_KEY:
            return await self._extract_groq(full_text)
        elif self.provider == "openai" and settings.OPENAI_API_KEY:
            return await self._extract_openai(full_text)
        elif self.provider == "gemini" and settings.GEMINI_API_KEY:
            return await self._extract_gemini(full_text)
        else:
            return self._extract_mock(full_text)

    async def _extract_groq(self, text: str) -> Dict[str, Any]:
        prompt = f"""
You are an expert occupational skill assessor. Analyze the following candidate profile / CV text and extract:
1. Candidate Full Name (or "Candidate")
2. Summary of estimated experience and background
3. Specific technical skills, tasks, and competencies with exact verbatim quotes as citations.

Candidate Text:
\"\"\"
{text[:4000]}
\"\"\"

Return ONLY valid JSON matching this schema:
{{
  "full_name": "string",
  "inferred_experience_summary": "string",
  "claims": [
    {{
      "claim": "string (e.g. PLC fault finding)",
      "source_citation": "string (exact sentence from text)"
    }}
  ]
}}
"""
        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
                resp = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
                    json={
                        "model": settings.LLM_MODEL or "llama-3.3-70b-versatile",
                        "messages": [
                            {"role": "system", "content": "You are a professional occupational assessor. Respond strictly in valid JSON."},
                            {"role": "user", "content": prompt}
                        ],
                        "response_format": {"type": "json_object"},
                        "temperature": 0.1
                    }
                )
                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                return json.loads(content)
        except Exception as e:
            logger.error(f"Groq extraction failed: {e}. Falling back to rule-based extractor.")
            return self._extract_mock(text)

    async def _extract_openai(self, text: str) -> Dict[str, Any]:
        prompt = f"""
You are an expert occupational skill assessor. Analyze the following candidate profile / CV text and extract:
1. Candidate Full Name (or "Candidate")
2. Summary of estimated experience and background
3. Specific technical skills, tasks, and competencies with exact verbatim quotes as citations.

Candidate Text:
\"\"\"
{text[:4000]}
\"\"\"

Return ONLY valid JSON matching this schema:
{{
  "full_name": "string",
  "inferred_experience_summary": "string",
  "claims": [
    {{
      "claim": "string (e.g. PLC fault finding)",
      "source_citation": "string (exact sentence from text)"
    }}
  ]
}}
"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                    json={
                        "model": settings.LLM_MODEL,
                        "messages": [{"role": "user", "content": prompt}],
                        "response_format": {"type": "json_object"},
                        "temperature": 0.1
                    }
                )
                resp.raise_for_status()
                data = resp.json()
                return json.loads(data["choices"][0]["message"]["content"])
        except Exception as e:
            logger.error(f"OpenAI extraction failed: {e}. Falling back to rule-based extractor.")
            return self._extract_mock(text)

    async def _extract_gemini(self, text: str) -> Dict[str, Any]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.LLM_MODEL}:generateContent?key={settings.GEMINI_API_KEY}"
        prompt = f"""Extract technical skills and quotes from this CV. Return JSON with full_name, inferred_experience_summary, and claims (array of {{claim, source_citation}}).\n\nText:\n{text[:4000]}"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    url,
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {"response_mime_type": "application/json"}
                    }
                )
                resp.raise_for_status()
                data = resp.json()
                content = data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(content)
        except Exception as e:
            logger.error(f"Gemini extraction failed: {e}. Falling back to rule-based extractor.")
            return self._extract_mock(text)

    def _extract_mock(self, text: str) -> Dict[str, Any]:
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        claims = []
        
        name = "Candidate"
        if lines:
            first_line = lines[0]
            if len(first_line.split()) <= 4 and not any(w in first_line.lower() for w in ["cv", "resume", "curriculum"]):
                name = first_line

        trade_patterns = [
            (r"\bplc\b|programmable logic|siemens\s*s7|allen bradley", "PLC troubleshooting and fault finding"),
            (r"hydraul", "Industrial hydraulic systems maintenance"),
            (r"pneumat", "Pneumatic systems and valve maintenance"),
            (r"preventative maintenance|preventive maintenance|\bpm\b|total productive", "Preventative maintenance execution"),
            (r"weld|arc weld|mig\b|tig\b|co2", "Metal welding and fabrication"),
            (r"electrical fault|circuit test|multimeter", "Electrical fault finding and diagnostics"),
            (r"drawing|blueprint|cad\b|solidworks", "Technical engineering drawing interpretation"),
            (r"align|bearing|laser shaft", "Machine shaft and coupling precision alignment"),
            (r"cnc\b|g-code|fanuc|milling|lathe", "CNC programming and machine tool operation"),
            (r"iso\s*9001|quality audit|qms", "ISO 9001 quality management auditing"),
            (r"spc\b|statistical process", "Statistical process control application"),
            (r"root cause|5-why|fishbone|8d\b", "Root cause failure analysis"),
            (r"solar\b|photovoltaic|\bpv\b", "Solar PV installation and mounting"),
            (r"battery storage|\bbms\b|lithium", "Battery energy storage systems maintenance"),
            (r"can\s*bus|wiring harness|ecu\b", "Automotive electrical and CAN bus diagnostics")
        ]

        sentences = re.split(r'(?<=[.!?\n]) +', text)
        matched_keys = set()

        for s in sentences:
            s_clean = s.strip()
            if not s_clean:
                continue
            for pattern, canonical_claim in trade_patterns:
                if re.search(pattern, s_clean, re.IGNORECASE) and canonical_claim not in matched_keys:
                    matched_keys.add(canonical_claim)
                    claims.append({
                        "claim": canonical_claim,
                        "source_citation": s_clean[:200]
                    })

        if not claims and text:
            claims.append({
                "claim": "General mechanical and electrical maintenance",
                "source_citation": text[:150]
            })

        return {
            "full_name": name,
            "inferred_experience_summary": f"Detected {len(claims)} core technical competencies from profile submission.",
            "claims": claims
        }

    # -------------------------------------------------------------------------
    # 2. Dense Embeddings & Vector Similarity
    # -------------------------------------------------------------------------
    async def get_embedding(self, text: str) -> List[float]:
        if settings.HF_API_KEY:
            try:
                model_id = settings.EMBEDDING_MODEL or "BAAI/bge-large-en-v1.5"
                url = f"https://router.huggingface.co/hf-inference/models/{model_id}"
                headers = {"Authorization": f"Bearer {settings.HF_API_KEY}"}
                async with httpx.AsyncClient(timeout=25.0) as client:
                    resp = await client.post(url, headers=headers, json={"inputs": text})
                    resp.raise_for_status()
                    result = resp.json()
                    if isinstance(result, list):
                        if len(result) > 0 and isinstance(result[0], list):
                            if len(result[0]) > 0 and isinstance(result[0][0], list):
                                return result[0][0]
                            return result[0]
                        return result
            except Exception as e:
                logger.error(f"Hugging Face embedding generation failed: {e}")

        if settings.OPENAI_API_KEY:
            try:
                async with httpx.AsyncClient(timeout=20.0) as client:
                    resp = await client.post(
                        "https://api.openai.com/v1/embeddings",
                        headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                        json={"model": settings.EMBEDDING_MODEL, "input": text}
                    )
                    resp.raise_for_status()
                    return resp.json()["data"][0]["embedding"]
            except Exception as e:
                logger.error(f"OpenAI embedding generation failed: {e}")
        
        return self._get_deterministic_mock_embedding(text)

    def _get_deterministic_mock_embedding(self, text: str) -> List[float]:
        dim = settings.EMBEDDING_DIMENSION or 1024
        vec = np.zeros(dim, dtype=np.float32)
        words = text.lower().split()
        for w in words:
            idx = abs(hash(w)) % dim
            vec[idx] += 1.0
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    # -------------------------------------------------------------------------
    # 3. Career Advisory Synthesis
    # -------------------------------------------------------------------------
    async def synthesize_guidance(
        self,
        candidate_name: str,
        occupation_title: str,
        match_percent: int,
        matched_skills: List[str],
        missing_essential: List[str]
    ) -> str:
        self._resolve_provider()

        prompt = f"""
Candidate: {candidate_name}
Target Role: {occupation_title}
Match Score: {match_percent}%
Matched Competencies: {', '.join(matched_skills) if matched_skills else 'None'}
Missing Essential Gaps: {', '.join(missing_essential) if missing_essential else 'None'}

Write a 2-3 sentence personalized, encouraging career advice summary. Mention the specific missing skills and recommend focus areas for practical hands-on practice, mentorship, or targeted on-the-job skill development.
"""
        if self.provider == "groq" and settings.GROQ_API_KEY:
            try:
                async with httpx.AsyncClient(timeout=20.0) as client:
                    resp = await client.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
                        json={
                            "model": settings.LLM_MODEL or "llama-3.3-70b-versatile",
                            "messages": [
                                {"role": "system", "content": "You are an encouraging occupational advisor."},
                                {"role": "user", "content": prompt}
                            ],
                            "temperature": 0.4
                        }
                    )
                    resp.raise_for_status()
                    return resp.json()["choices"][0]["message"]["content"].strip()
            except Exception as e:
                logger.error(f"Groq guidance synthesis failed: {e}")

        elif self.provider == "openai" and settings.OPENAI_API_KEY:
            try:
                async with httpx.AsyncClient(timeout=20.0) as client:
                    resp = await client.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                        json={
                            "model": settings.LLM_MODEL,
                            "messages": [{"role": "user", "content": prompt}],
                            "temperature": 0.4
                        }
                    )
                    resp.raise_for_status()
                    return resp.json()["choices"][0]["message"]["content"].strip()
            except Exception as e:
                logger.error(f"OpenAI guidance synthesis failed: {e}")

        # Deterministic structured summary fallback
        if match_percent >= 90:
            return f"{candidate_name}'s profile demonstrates outstanding alignment ({match_percent}%) with the {occupation_title} profile. All core trade competencies are accounted for, verifying high readiness for immediate placement or role qualification."
        elif match_percent >= 60:
            gaps_str = " and ".join(missing_essential[:2]) if missing_essential else "secondary skills"
            return f"{candidate_name} exhibits a strong foundation for the {occupation_title} role with a {match_percent}% match. The primary technical gaps include {gaps_str}. Seeking targeted mentorship or hands-on practice will rapidly close these gaps."
        else:
            gaps_str = ", ".join(missing_essential[:3]) if missing_essential else "core parameters"
            return f"{candidate_name}'s profile currently shows emerging alignment ({match_percent}%) with {occupation_title}. Key skill gaps exist in {gaps_str}. Focused hands-on training and peer mentorship are recommended to help build these capabilities."

ai_service = AIService()
