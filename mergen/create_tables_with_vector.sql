-- Create tables with pgvector support
-- This assumes pgvector extension is already installed

-- Drop existing tables if they exist
DROP TABLE IF EXISTS vector_chunks CASCADE;
DROP TABLE IF EXISTS evidence CASCADE; 
DROP TABLE IF EXISTS requirements CASCADE;
DROP TABLE IF EXISTS facility_features CASCADE;
DROP TABLE IF EXISTS pricing_items CASCADE;
DROP TABLE IF EXISTS past_performance CASCADE;
DROP TABLE IF EXISTS clauses CASCADE;
DROP TABLE IF EXISTS documents CASCADE;

-- Create documents table
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    kind VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    path VARCHAR(500) NOT NULL,
    meta_json JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create clauses table
CREATE TABLE clauses (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    section VARCHAR(100),
    text TEXT NOT NULL,
    tags JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create requirements table
CREATE TABLE requirements (
    id SERIAL PRIMARY KEY,
    rfq_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    code VARCHAR(20) NOT NULL,
    text TEXT NOT NULL,
    category VARCHAR(50),
    priority VARCHAR(20) DEFAULT 'medium',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create evidence table
CREATE TABLE evidence (
    id SERIAL PRIMARY KEY,
    requirement_id INTEGER NOT NULL REFERENCES requirements(id) ON DELETE CASCADE,
    source_doc_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    snippet TEXT NOT NULL,
    score FLOAT DEFAULT 0.0,
    evidence_type VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create facility_features table
CREATE TABLE facility_features (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    value TEXT,
    source_doc_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create pricing_items table
CREATE TABLE pricing_items (
    id SERIAL PRIMARY KEY,
    rfq_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    qty FLOAT DEFAULT 1.0,
    unit VARCHAR(50),
    unit_price FLOAT NOT NULL,
    total_price FLOAT,
    category VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create past_performance table
CREATE TABLE past_performance (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    client VARCHAR(200),
    scope TEXT,
    period VARCHAR(100),
    value FLOAT,
    ref_info JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create vector_chunks table with VECTOR type
CREATE TABLE vector_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk TEXT NOT NULL,
    embedding VECTOR(384), -- Using 384 dimensions for sentence-transformers
    chunk_type VARCHAR(50),
    page_number INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_documents_kind ON documents(kind);
CREATE INDEX idx_documents_created_at ON documents(created_at);
CREATE INDEX idx_requirements_rfq_id ON requirements(rfq_id);
CREATE INDEX idx_requirements_category ON requirements(category);
CREATE INDEX idx_evidence_requirement_id ON evidence(requirement_id);
CREATE INDEX idx_evidence_source_doc_id ON evidence(source_doc_id);
CREATE INDEX idx_facility_features_name ON facility_features(name);
CREATE INDEX idx_pricing_items_rfq_id ON pricing_items(rfq_id);
CREATE INDEX idx_pricing_items_category ON pricing_items(category);
CREATE INDEX idx_vector_chunks_document_id ON vector_chunks(document_id);

-- Create vector similarity index
CREATE INDEX ON vector_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Create compliance matrix view
CREATE VIEW compliance_matrix_view AS
SELECT 
    r.id as requirement_id,
    r.code,
    r.text as requirement_text,
    r.category,
    r.priority,
    COUNT(e.id) as evidence_count,
    COALESCE(AVG(e.score), 0) as avg_score,
    CASE 
        WHEN COUNT(e.id) = 0 THEN 'critical'
        WHEN AVG(e.score) >= 0.8 THEN 'low'
        WHEN AVG(e.score) >= 0.6 THEN 'medium'
        WHEN AVG(e.score) >= 0.4 THEN 'high'
        ELSE 'critical'
    END as risk_level
FROM requirements r
LEFT JOIN evidence e ON r.id = e.requirement_id
GROUP BY r.id, r.code, r.text, r.category, r.priority;