-- ZgrBid Database Creation Script
-- PostgreSQL 16+

-- Create database
CREATE DATABASE ZGRSAM
    WITH 
    OWNER = postgres
    ENCODING = 'UTF8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
-- Note: pgvector extension needs to be installed first
-- CREATE EXTENSION IF NOT EXISTS vector;

-- Create tables
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    kind VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    path VARCHAR(500) NOT NULL,
    meta_json JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE clauses (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    section VARCHAR(100),
    text TEXT NOT NULL,
    tags JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE requirements (
    id SERIAL PRIMARY KEY,
    rfq_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    code VARCHAR(20) NOT NULL,
    text TEXT NOT NULL,
    category VARCHAR(50),
    priority VARCHAR(20) DEFAULT 'medium',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE evidence (
    id SERIAL PRIMARY KEY,
    requirement_id INTEGER NOT NULL REFERENCES requirements(id) ON DELETE CASCADE,
    source_doc_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    snippet TEXT NOT NULL,
    score FLOAT DEFAULT 0.0,
    evidence_type VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE facility_features (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    value TEXT,
    source_doc_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

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

CREATE TABLE vector_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk TEXT NOT NULL,
    embedding REAL[], -- Array of floats instead of vector type
    chunk_type VARCHAR(50),
    page_number INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
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

-- Create vector similarity index for RAG (commented out - requires pgvector)
-- CREATE INDEX ON vector_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Insert sample data
INSERT INTO documents (kind, title, path, meta_json) VALUES
('rfq', 'AQD Seminar RFQ - 140D0424Q0292', 'samples/rfq.pdf', '{"rfq_number": "140D0424Q0292", "agency": "Department of Defense", "location": "Orlando, FL", "event_dates": "2024-04-14 to 2024-04-18"}'),
('facility', 'DoubleTree Technical Specifications', 'samples/facility.pdf', '{"hotel_name": "DoubleTree by Hilton", "location": "Orlando, FL", "capacity": 100}'),
('past_performance', 'Past Performance Portfolio', 'samples/past_performance.pdf', '{"company": "ZgrBid Solutions", "years_experience": 10}'),
('pricing', 'Pricing Spreadsheet', 'samples/pricing.xlsx', '{"currency": "USD", "tax_rate": 0.0}');

-- Insert sample requirements
INSERT INTO requirements (rfq_id, code, text, category, priority) VALUES
(1, 'R-001', 'Accommodate 100 participants for general session', 'capacity', 'high'),
(1, 'R-002', 'Provide 2 breakout rooms for 15 participants each', 'capacity', 'high'),
(1, 'R-003', 'Event dates: April 14-18, 2024', 'date', 'critical'),
(1, 'R-004', 'Provide airport shuttle service', 'transport', 'medium'),
(1, 'R-005', 'Provide complimentary Wi-Fi internet access', 'av', 'medium'),
(1, 'R-006', 'Comply with FAR 52.204-24 representation requirements', 'clauses', 'critical'),
(1, 'R-007', 'Submit invoices through IPP system', 'invoice', 'high'),
(1, 'R-008', 'Provide AV equipment for main room and breakout rooms', 'av', 'high');

-- Insert sample facility features
INSERT INTO facility_features (name, value, source_doc_id) VALUES
('shuttle', 'Free airport shuttle service available every 30 minutes', 2),
('wifi', 'Complimentary high-speed Wi-Fi throughout the property', 2),
('parking', 'Complimentary self-parking for all guests', 2),
('breakout_rooms', '2 breakout rooms available, each accommodating 15 participants', 2),
('boardroom', 'Executive boardroom available for 20 participants', 2),
('av_equipment', 'Full AV equipment including projectors, microphones, and screens', 2);

-- Insert sample pricing items
INSERT INTO pricing_items (rfq_id, name, description, qty, unit, unit_price, total_price, category) VALUES
(1, 'Room Block - 4 nights', 'Accommodation for 100 participants, 4 nights', 100.0, 'room_night', 135.00, 54000.00, 'lodging'),
(1, 'Main Room AV Setup', 'Audio-visual equipment for main conference room', 1.0, 'setup', 2500.00, 2500.00, 'av'),
(1, 'Breakout Room AV', 'Audio-visual equipment for 2 breakout rooms', 2.0, 'room', 500.00, 1000.00, 'av'),
(1, 'Airport Shuttle Service', 'Shuttle service for airport transfers', 1.0, 'service', 1500.00, 1500.00, 'transportation'),
(1, 'Project Management', 'Full project management and coordination', 1.0, 'project', 5000.00, 5000.00, 'management');

-- Insert sample past performance
INSERT INTO past_performance (title, client, scope, period, value, ref_info) VALUES
('KYNG Statewide BPA Conference Management', 'Kentucky National Guard', 'Full conference management for 75 participants including facility coordination, AV services, and logistics', '2022-2023', 45000.0, '{"poc": "John Smith", "title": "Contracting Officer", "phone": "+1-502-555-0123", "email": "john.smith@ky.ng.mil"}'),
('Aviano Air Base Training Seminar', 'US Air Force', 'Training seminar management for 50 participants with AV support and facility coordination', '2023', 32000.0, '{"poc": "Sarah Johnson", "title": "Training Coordinator", "phone": "+39-0434-30-1234", "email": "sarah.johnson@us.af.mil"}'),
('Department of Energy Workshop Series', 'US Department of Energy', 'Multi-day workshop series for 120 participants with comprehensive event management', '2023-2024', 85000.0, '{"poc": "Michael Brown", "title": "Program Manager", "phone": "+1-202-555-0456", "email": "michael.brown@energy.gov"}');

-- Insert sample evidence
INSERT INTO evidence (requirement_id, source_doc_id, snippet, score, evidence_type) VALUES
(1, 2, 'Main conference room accommodates up to 100 participants with theater-style seating', 0.95, 'facility'),
(2, 2, '2 breakout rooms available, each accommodating 15 participants', 0.90, 'facility'),
(4, 2, 'Free airport shuttle service available every 30 minutes', 0.85, 'facility'),
(5, 2, 'Complimentary high-speed Wi-Fi throughout the property', 0.90, 'facility');

-- Insert sample vector chunks (with placeholder embeddings)
INSERT INTO vector_chunks (document_id, chunk, embedding, chunk_type, page_number) VALUES
(2, 'Main conference room accommodates up to 100 participants with theater-style seating', ARRAY[0.1, 0.1, 0.1, 0.1, 0.1], 'paragraph', 1),
(2, '2 breakout rooms available, each accommodating 15 participants', ARRAY[0.1, 0.1, 0.1, 0.1, 0.1], 'paragraph', 1),
(2, 'Free airport shuttle service available every 30 minutes', ARRAY[0.1, 0.1, 0.1, 0.1, 0.1], 'paragraph', 1),
(2, 'Complimentary high-speed Wi-Fi throughout the property', ARRAY[0.1, 0.1, 0.1, 0.1, 0.1], 'paragraph', 1);

-- Create a view for compliance matrix
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

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE ZGRSAM TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;

-- Display success message
SELECT 'ZGRSAM database and tables created successfully!' as status;
