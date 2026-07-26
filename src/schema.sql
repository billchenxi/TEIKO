PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS projects (
    project_id   INTEGER PRIMARY KEY,
    project_code TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS conditions (
    condition_id   INTEGER PRIMARY KEY,
    condition_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS treatments (
    treatment_id   INTEGER PRIMARY KEY,
    treatment_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS sample_types (
    sample_type_id   INTEGER PRIMARY KEY,
    sample_type_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS cell_populations (
    population_id   INTEGER PRIMARY KEY,
    population_name TEXT NOT NULL UNIQUE,   -- original name, e.g. cd8_t_cell
    display_name    TEXT,                   -- readable label, e.g. CD8 T cell
    sort_order      INTEGER
);

CREATE TABLE IF NOT EXISTS subjects (
    subject_id   INTEGER PRIMARY KEY,
    subject_code TEXT NOT NULL UNIQUE,
    project_id   INTEGER NOT NULL REFERENCES projects(project_id),
    condition_id INTEGER REFERENCES conditions(condition_id),
    age          INTEGER CHECK (age IS NULL OR age BETWEEN 0 AND 120),
    sex          TEXT CHECK (sex IS NULL OR sex IN ('M', 'F'))
);

CREATE TABLE IF NOT EXISTS samples (
    sample_id                 INTEGER PRIMARY KEY,
    sample_code               TEXT NOT NULL UNIQUE,
    subject_id                INTEGER NOT NULL REFERENCES subjects(subject_id),
    treatment_id              INTEGER REFERENCES treatments(treatment_id),
    sample_type_id            INTEGER REFERENCES sample_types(sample_type_id),
    response                  TEXT,
    time_from_treatment_start INTEGER
);

-- Measurement table: raw counts
CREATE TABLE IF NOT EXISTS cell_counts (
    sample_id     INTEGER NOT NULL REFERENCES samples(sample_id) ON DELETE CASCADE,
    population_id INTEGER NOT NULL REFERENCES cell_populations(population_id),
    count         INTEGER NOT NULL CHECK (count >= 0),
    PRIMARY KEY (sample_id, population_id)
);

-- Create view for reuse
CREATE VIEW IF NOT EXISTS view_sample_total AS
    SELECT sample_id, SUM(count) AS total_count
    FROM cell_counts
    GROUP BY sample_id;
