-- Migration: Create job_logs table for structured success/failure tracking
-- Run: psql -U postgres -d gungil -f 001_create_job_logs.sql

CREATE TABLE IF NOT EXISTS job_logs (
    id              VARCHAR(36) PRIMARY KEY,
    celery_task_id  VARCHAR(255) NOT NULL,
    site_id         VARCHAR(255) NOT NULL,
    target_name     VARCHAR(255),
    status          VARCHAR(50)  NOT NULL DEFAULT 'pending',
    started_at      TIMESTAMP,
    completed_at    TIMESTAMP,
    urls_crawled    INTEGER      DEFAULT 0,
    urls_failed     INTEGER      DEFAULT 0,
    items_parsed    INTEGER      DEFAULT 0,
    error_message   TEXT,
    result_summary  TEXT,
    created_at      TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_job_logs_celery_task_id ON job_logs (celery_task_id);
CREATE INDEX IF NOT EXISTS idx_job_logs_site_id ON job_logs (site_id);
CREATE INDEX IF NOT EXISTS idx_job_logs_status ON job_logs (status);
CREATE INDEX IF NOT EXISTS idx_job_logs_created_at ON job_logs (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_job_logs_site_status ON job_logs (site_id, status);
