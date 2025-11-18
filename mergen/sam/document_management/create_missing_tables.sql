-- Eksik tabloları oluştur
-- SAM Document Management için gerekli tablolar

-- Vector chunks tablosu
CREATE TABLE IF NOT EXISTS vector_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    embedding VECTOR(384), -- pgvector extension gerekli
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Requirements tablosu (eğer yoksa)
CREATE TABLE IF NOT EXISTS requirements (
    id SERIAL PRIMARY KEY,
    rfq_id INTEGER NOT NULL,
    code VARCHAR(20) NOT NULL,
    text TEXT NOT NULL,
    category VARCHAR(50),
    priority VARCHAR(20) DEFAULT 'medium',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Evidence tablosu (eğer yoksa)
CREATE TABLE IF NOT EXISTS evidence (
    id SERIAL PRIMARY KEY,
    requirement_id INTEGER NOT NULL,
    source_doc_id INTEGER NOT NULL,
    text TEXT NOT NULL,
    confidence FLOAT DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Facility features tablosu (eğer yoksa)
CREATE TABLE IF NOT EXISTS facility_features (
    id SERIAL PRIMARY KEY,
    source_doc_id INTEGER NOT NULL,
    feature_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    location VARCHAR(100),
    capacity INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Pricing items tablosu (eğer yoksa)
CREATE TABLE IF NOT EXISTS pricing_items (
    id SERIAL PRIMARY KEY,
    rfq_id INTEGER NOT NULL,
    item_code VARCHAR(20) NOT NULL,
    description TEXT NOT NULL,
    unit VARCHAR(20),
    quantity INTEGER DEFAULT 1,
    unit_price DECIMAL(10,2),
    total_price DECIMAL(10,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Past performance tablosu (eğer yoksa)
CREATE TABLE IF NOT EXISTS past_performance (
    id SERIAL PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    project_title VARCHAR(255) NOT NULL,
    contract_value DECIMAL(15,2),
    completion_date DATE,
    performance_rating VARCHAR(20),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index'ler oluştur
CREATE INDEX IF NOT EXISTS idx_vector_chunks_document_id ON vector_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_vector_chunks_embedding ON vector_chunks USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_requirements_rfq_id ON requirements(rfq_id);
CREATE INDEX IF NOT EXISTS idx_evidence_requirement_id ON evidence(requirement_id);
CREATE INDEX IF NOT EXISTS idx_evidence_source_doc_id ON evidence(source_doc_id);
CREATE INDEX IF NOT EXISTS idx_facility_features_source_doc_id ON facility_features(source_doc_id);
CREATE INDEX IF NOT EXISTS idx_pricing_items_rfq_id ON pricing_items(rfq_id);
CREATE INDEX IF NOT EXISTS idx_past_performance_company ON past_performance(company_name);

-- Örnek veriler ekle
INSERT INTO requirements (rfq_id, code, text, category, priority) VALUES
(1, 'REQ-001', 'Hotel must have conference facilities', 'Facilities', 'high'),
(1, 'REQ-002', 'Minimum 100 guest rooms', 'Capacity', 'high'),
(1, 'REQ-003', '24/7 room service', 'Services', 'medium')
ON CONFLICT DO NOTHING;

INSERT INTO facility_features (source_doc_id, feature_type, description, location, capacity) VALUES
(1, 'Conference Room', 'Main conference hall with AV equipment', 'Ground Floor', 200),
(1, 'Meeting Room', 'Small meeting rooms for breakout sessions', 'First Floor', 20),
(1, 'Restaurant', 'Full-service restaurant with bar', 'Ground Floor', 150)
ON CONFLICT DO NOTHING;

INSERT INTO pricing_items (rfq_id, item_code, description, unit, quantity, unit_price, total_price) VALUES
(1, 'ROOM-001', 'Standard guest room', 'night', 100, 150.00, 15000.00),
(1, 'MEAL-001', 'Breakfast buffet', 'person', 200, 25.00, 5000.00),
(1, 'AV-001', 'Audio-visual equipment rental', 'day', 3, 500.00, 1500.00)
ON CONFLICT DO NOTHING;

INSERT INTO past_performance (company_name, project_title, contract_value, completion_date, performance_rating, description) VALUES
('ZGR Hotels', 'Government Conference Center', 2500000.00, '2023-12-15', 'Excellent', 'Successfully completed major government conference facility'),
('ZGR Hotels', 'Military Lodging Contract', 1800000.00, '2023-08-30', 'Good', 'Provided lodging services for military personnel'),
('ZGR Hotels', 'Federal Training Center', 3200000.00, '2024-02-28', 'Excellent', 'Operated federal training facility with high satisfaction ratings')
ON CONFLICT DO NOTHING;

-- Başarı mesajı
SELECT 'Missing tables created successfully!' as status;
