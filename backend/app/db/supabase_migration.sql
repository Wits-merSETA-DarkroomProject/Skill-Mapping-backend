-- =============================================================================
-- ESCO OFFICIAL SKILLS SCHEMA (13,960 DATASET ALIGNED)
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Master ESCO Skills Table (1:1 with your DataFrame)
CREATE TABLE IF NOT EXISTS esco_skills (
    concept_uri TEXT PRIMARY KEY,                       -- e.g. "http://data.europa.eu/esco/skill/0005c151-5b5a..."
    concept_type TEXT DEFAULT 'KnowledgeSkillCompetence',-- "KnowledgeSkillCompetence"
    skill_type TEXT,                                   -- "skill/competence" or "knowledge"
    reuse_level TEXT,                                  -- "sector-specific", "occupation-specific", "cross-sector", "transversal"
    preferred_label TEXT NOT NULL,                     -- e.g. "manage musical staff"
    alt_labels TEXT,                                   -- Raw newline-separated synonyms (\n) or JSON
    in_scheme TEXT,                                    -- "http://data.europa.eu/esco/concept-scheme/skills"
    description TEXT,                                  -- Full description
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Search Indexes for ultra-fast matching
CREATE INDEX IF NOT EXISTS idx_esco_skills_label_trgm ON esco_skills USING gin (to_tsvector('english', preferred_label));
CREATE INDEX IF NOT EXISTS idx_esco_skills_alt_trgm ON esco_skills USING gin (to_tsvector('english', COALESCE(alt_labels, '')));
CREATE INDEX IF NOT EXISTS idx_esco_skills_type ON esco_skills(skill_type);
CREATE INDEX IF NOT EXISTS idx_esco_skills_reuse ON esco_skills(reuse_level);

-- 2. ESCO Occupations Table
CREATE TABLE IF NOT EXISTS esco_occupations (
    concept_uri TEXT PRIMARY KEY,                       -- e.g. "http://data.europa.eu/esco/occupation/..."
    isco_group TEXT NOT NULL,                          -- e.g. "3231", "3115"
    preferred_label TEXT NOT NULL,                     -- e.g. "industrial machinery mechanic"
    alt_labels TEXT,                                   -- Newline-separated synonyms
    description TEXT,
    category TEXT DEFAULT 'Trade / Maintenance',
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_esco_occ_isco ON esco_occupations(isco_group);
CREATE INDEX IF NOT EXISTS idx_esco_occ_label ON esco_occupations USING gin (to_tsvector('english', preferred_label));

-- 3. ESCO Occupation-to-Skill Requirements (Essential vs Optional)
CREATE TABLE IF NOT EXISTS esco_occupation_skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    occupation_uri TEXT NOT NULL REFERENCES esco_occupations(concept_uri) ON DELETE CASCADE,
    skill_uri TEXT NOT NULL REFERENCES esco_skills(concept_uri) ON DELETE CASCADE,
    relation_type TEXT NOT NULL DEFAULT 'essential',   -- 'essential' or 'optional'
    importance_score FLOAT DEFAULT 1.0,                -- 1.0 for essential, 0.5 for optional
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(occupation_uri, skill_uri)
);
CREATE INDEX IF NOT EXISTS idx_occ_skills_lookup ON esco_occupation_skills(occupation_uri, relation_type);

-- 4. Candidate Profiles & Extracted Skills
CREATE TABLE IF NOT EXISTS user_profiles (
    id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL DEFAULT 'Candidate',
    cv_file_name TEXT,
    raw_text TEXT,
    linkedin_url TEXT,
    inferred_experience_summary TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS user_matched_skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id TEXT NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    skill_uri TEXT NOT NULL REFERENCES esco_skills(concept_uri) ON DELETE CASCADE,
    extracted_claim TEXT NOT NULL,
    source_citation TEXT,
    confidence_score FLOAT DEFAULT 1.0,
    confidence_tier TEXT DEFAULT 'direct',             -- 'direct', 'related', 'inferred'
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 5. Gap Analysis Runs
CREATE TABLE IF NOT EXISTS gap_analysis_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id TEXT UNIQUE NOT NULL,
    profile_id TEXT NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    occupation_uri TEXT NOT NULL REFERENCES esco_occupations(concept_uri) ON DELETE CASCADE,
    essential_match_percent INT NOT NULL,
    optional_match_percent INT NOT NULL,
    overall_match_percent INT NOT NULL,
    matched_essential JSONB DEFAULT '[]'::jsonb,
    missing_essential JSONB DEFAULT '[]'::jsonb,
    matched_optional JSONB DEFAULT '[]'::jsonb,
    missing_optional JSONB DEFAULT '[]'::jsonb,
    ai_guidance_summary TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
