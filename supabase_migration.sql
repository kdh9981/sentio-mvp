-- Sentio MVP - Supabase Migration
-- Run this in Supabase Dashboard > SQL Editor

-- Table 1: staging_records (replaces staging_log.csv)
CREATE TABLE staging_records (
    id              BIGSERIAL PRIMARY KEY,
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    original_file   TEXT NOT NULL,
    original_path   TEXT,
    staged_file     TEXT NOT NULL UNIQUE,
    storage_path    TEXT,
    modality        TEXT NOT NULL CHECK (modality IN ('vision', 'audio')),
    ai_classification TEXT NOT NULL,
    confidence      REAL NOT NULL,
    features        JSONB NOT NULL DEFAULT '{}',
    human_validated BOOLEAN NOT NULL DEFAULT FALSE,
    human_agrees    BOOLEAN,
    final_classification TEXT,
    validated_at    TIMESTAMPTZ
);
CREATE INDEX idx_staging_pending ON staging_records (human_validated) WHERE human_validated = FALSE;

-- Table 2: reference_samples (replaces reference_features.json)
CREATE TABLE reference_samples (
    id              BIGSERIAL PRIMARY KEY,
    filename        TEXT NOT NULL,
    classification  TEXT NOT NULL CHECK (classification IN ('healthy', 'sick')),
    features        JSONB NOT NULL,
    added_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (filename, classification)
);

-- Table 3: threshold_feedback (replaces threshold_history.json)
CREATE TABLE threshold_feedback (
    id                  BIGSERIAL PRIMARY KEY,
    modality            TEXT NOT NULL CHECK (modality IN ('vision', 'audio')),
    timestamp           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    score               REAL NOT NULL,
    ai_prediction       TEXT NOT NULL,
    human_agrees        BOOLEAN NOT NULL,
    current_threshold   REAL NOT NULL
);

-- Table 4: threshold_config (replaces config.yaml mutations)
CREATE TABLE threshold_config (
    id                      BIGSERIAL PRIMARY KEY,
    modality                TEXT NOT NULL UNIQUE,
    current_threshold       REAL NOT NULL,
    suggested_threshold     REAL,
    last_updated            TIMESTAMPTZ
);
INSERT INTO threshold_config (modality, current_threshold) VALUES ('vision', 0.676), ('audio', 0.5);

-- Storage bucket: create via Supabase Dashboard > Storage > New Bucket
-- Name: sentio-files (private)
-- Prefixes: staging/, verified/healthy_images/, verified/sick_images/,
--           verified/healthy_audio/, verified/sick_audio/
