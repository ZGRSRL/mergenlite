-- MergenLite Sadeleştirilmiş Veritabanı Şeması
-- Database: mergenlite
-- Bu şema, MergenAI'nin 10+ tablosunu 4 temel tabloya indirger

-- UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. opportunities: SAM.gov Fırsatları
CREATE TABLE IF NOT EXISTS opportunities (
    opportunity_id VARCHAR(50) PRIMARY KEY,
    title VARCHAR(512) NOT NULL,
    notice_type VARCHAR(100),
    naics_code VARCHAR(10),
    response_deadline TIMESTAMP,
    estimated_value NUMERIC(15, 2),
    place_of_performance VARCHAR(255),
    sam_gov_link VARCHAR(512),
    raw_data JSONB, -- SAM.gov API'den gelen ham verinin tamamı
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for opportunities
CREATE INDEX IF NOT EXISTS idx_opportunities_naics ON opportunities(naics_code);
CREATE INDEX IF NOT EXISTS idx_opportunities_deadline ON opportunities(response_deadline);
CREATE INDEX IF NOT EXISTS idx_opportunities_created ON opportunities(created_at);

-- 2. manual_documents: Manuel Yüklenen Dokümanlar
CREATE TABLE IF NOT EXISTS manual_documents (
    document_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    opportunity_id VARCHAR(50) REFERENCES opportunities(opportunity_id) ON DELETE SET NULL,
    file_name VARCHAR(255) NOT NULL,
    file_mime_type VARCHAR(100),
    storage_path VARCHAR(512) NOT NULL,
    document_metadata JSONB, -- Kullanıcı tarafından girilen başlık, etiketler vb.
    upload_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for manual_documents
CREATE INDEX IF NOT EXISTS idx_manual_docs_opportunity ON manual_documents(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_manual_docs_upload_date ON manual_documents(upload_date);

-- 3. ai_analysis_results: Konsolide AI Analiz Sonuçları
-- Tüm ajan çıktıları bu tabloya, fırsat ID'si ile bağlanarak JSONB olarak kaydedilecektir.
CREATE TABLE IF NOT EXISTS ai_analysis_results (
    analysis_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    opportunity_id VARCHAR(50) REFERENCES opportunities(opportunity_id) ON DELETE CASCADE,
    analysis_status VARCHAR(50) NOT NULL DEFAULT 'IN_PROGRESS', -- Örn: 'IN_PROGRESS', 'COMPLETED', 'FAILED'
    analysis_version VARCHAR(20) DEFAULT '1.0',
    -- Tüm alt ajan çıktıları (Gereksinimler, Compliance, Teklif Taslağı) burada birleştirilir.
    consolidated_output JSONB,
    start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP WITH TIME ZONE,
    analysis_duration_seconds NUMERIC,
    UNIQUE (opportunity_id, analysis_version) -- Bir fırsatın aynı versiyonda iki analizi olamaz.
);

-- Indexes for ai_analysis_results
CREATE INDEX IF NOT EXISTS idx_ai_results_opportunity ON ai_analysis_results(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_ai_results_status ON ai_analysis_results(analysis_status);
CREATE INDEX IF NOT EXISTS idx_ai_results_start_time ON ai_analysis_results(start_time);

-- 4. system_sessions: Hafif Kullanıcı ve Sistem İzleme
-- MergenAI'daki 'user_sessions' ve 'system_metrics' tablolarının basitleştirilmiş birleşimi
CREATE TABLE IF NOT EXISTS system_sessions (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_start TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    user_identifier VARCHAR(100), -- Gerçek bir kullanıcı sistemi entegre edildiğinde kullanılmak üzere.
    analysis_count INTEGER DEFAULT 0,
    metric_data JSONB -- Hafif sistem metrikleri (CPU/Bellek kullanımı, hız vb.)
);

-- Indexes for system_sessions
CREATE INDEX IF NOT EXISTS idx_sessions_start ON system_sessions(session_start);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON system_sessions(user_identifier);

-- Updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for opportunities table
DROP TRIGGER IF EXISTS update_opportunities_updated_at ON opportunities;
CREATE TRIGGER update_opportunities_updated_at
    BEFORE UPDATE ON opportunities
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE opportunities IS 'SAM.gov fırsatları - temel ilan bilgileri';
COMMENT ON TABLE manual_documents IS 'Manuel yüklenen dokümanlar (PDF, DOCX, vb.)';
COMMENT ON TABLE ai_analysis_results IS 'Konsolide AI analiz sonuçları - tüm ajan çıktıları JSONB formatında';
COMMENT ON TABLE system_sessions IS 'Hafif kullanıcı ve sistem izleme metrikleri';

COMMENT ON COLUMN ai_analysis_results.consolidated_output IS 'Tüm ajan çıktıları: requirements, compliance, proposal_draft, vb. JSONB formatında';
COMMENT ON COLUMN opportunities.raw_data IS 'SAM.gov API''den gelen ham verinin tamamı (JSONB)';

