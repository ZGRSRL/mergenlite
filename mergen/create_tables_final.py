#!/usr/bin/env python3
"""
PostgreSQL Database Creation Script for ZgrBid (without vector for now)
"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys

# Database connection parameters
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'user': 'postgres',
    'password': 'sarlio41',
    'database': 'zgrsam'
}

def create_connection():
    """Create database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return conn
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        return None

def create_tables(conn):
    """Create all tables"""
    cursor = conn.cursor()
    
    try:
        # Drop existing tables if they exist
        print("Dropping existing tables...")
        drop_tables = [
            "DROP TABLE IF EXISTS vector_chunks CASCADE",
            "DROP TABLE IF EXISTS evidence CASCADE", 
            "DROP TABLE IF EXISTS requirements CASCADE",
            "DROP TABLE IF EXISTS facility_features CASCADE",
            "DROP TABLE IF EXISTS pricing_items CASCADE",
            "DROP TABLE IF EXISTS past_performance CASCADE",
            "DROP TABLE IF EXISTS clauses CASCADE",
            "DROP TABLE IF EXISTS documents CASCADE"
        ]
        
        for sql in drop_tables:
            cursor.execute(sql)
        
        # Create documents table
        print("Creating documents table...")
        cursor.execute("""
            CREATE TABLE documents (
                id SERIAL PRIMARY KEY,
                kind VARCHAR(50) NOT NULL,
                title VARCHAR(255) NOT NULL,
                path VARCHAR(500) NOT NULL,
                meta_json JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create clauses table
        print("Creating clauses table...")
        cursor.execute("""
            CREATE TABLE clauses (
                id SERIAL PRIMARY KEY,
                document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                section VARCHAR(100),
                text TEXT NOT NULL,
                tags JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create requirements table
        print("Creating requirements table...")
        cursor.execute("""
            CREATE TABLE requirements (
                id SERIAL PRIMARY KEY,
                rfq_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                code VARCHAR(20) NOT NULL,
                text TEXT NOT NULL,
                category VARCHAR(50),
                priority VARCHAR(20) DEFAULT 'medium',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create evidence table
        print("Creating evidence table...")
        cursor.execute("""
            CREATE TABLE evidence (
                id SERIAL PRIMARY KEY,
                requirement_id INTEGER NOT NULL REFERENCES requirements(id) ON DELETE CASCADE,
                source_doc_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                snippet TEXT NOT NULL,
                score FLOAT DEFAULT 0.0,
                evidence_type VARCHAR(50),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create facility_features table
        print("Creating facility_features table...")
        cursor.execute("""
            CREATE TABLE facility_features (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                value TEXT,
                source_doc_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create pricing_items table
        print("Creating pricing_items table...")
        cursor.execute("""
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
        """)
        
        # Create past_performance table
        print("Creating past_performance table...")
        cursor.execute("""
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
        """)
        
        # Create vector_chunks table (without vector type for now)
        print("Creating vector_chunks table...")
        cursor.execute("""
            CREATE TABLE vector_chunks (
                id SERIAL PRIMARY KEY,
                document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                chunk TEXT NOT NULL,
                embedding REAL[], -- Array of floats instead of vector type
                chunk_type VARCHAR(50),
                page_number INTEGER,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create indexes
        print("Creating indexes...")
        indexes = [
            "CREATE INDEX idx_documents_kind ON documents(kind);",
            "CREATE INDEX idx_documents_created_at ON documents(created_at);",
            "CREATE INDEX idx_requirements_rfq_id ON requirements(rfq_id);",
            "CREATE INDEX idx_requirements_category ON requirements(category);",
            "CREATE INDEX idx_evidence_requirement_id ON evidence(requirement_id);",
            "CREATE INDEX idx_evidence_source_doc_id ON evidence(source_doc_id);",
            "CREATE INDEX idx_facility_features_name ON facility_features(name);",
            "CREATE INDEX idx_pricing_items_rfq_id ON pricing_items(rfq_id);",
            "CREATE INDEX idx_pricing_items_category ON pricing_items(category);",
            "CREATE INDEX idx_vector_chunks_document_id ON vector_chunks(document_id);"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        # Create compliance matrix view
        print("Creating compliance matrix view...")
        cursor.execute("""
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
        """)
        
        print("✅ All tables created successfully!")
        return True
        
    except psycopg2.Error as e:
        print(f"Error creating tables: {e}")
        return False
    finally:
        cursor.close()

def insert_sample_data(conn):
    """Insert sample data"""
    cursor = conn.cursor()
    
    try:
        print("Inserting sample data...")
        
        # Insert documents
        cursor.execute("""
            INSERT INTO documents (kind, title, path, meta_json) VALUES
            ('rfq', 'AQD Seminar RFQ - 140D0424Q0292', 'samples/rfq.pdf', '{"rfq_number": "140D0424Q0292", "agency": "Department of Defense", "location": "Orlando, FL", "event_dates": "2024-04-14 to 2024-04-18"}'),
            ('facility', 'DoubleTree Technical Specifications', 'samples/facility.pdf', '{"hotel_name": "DoubleTree by Hilton", "location": "Orlando, FL", "capacity": 100}'),
            ('past_performance', 'Past Performance Portfolio', 'samples/past_performance.pdf', '{"company": "ZgrBid Solutions", "years_experience": 10}'),
            ('pricing', 'Pricing Spreadsheet', 'samples/pricing.xlsx', '{"currency": "USD", "tax_rate": 0.0}');
        """)
        
        # Insert requirements
        cursor.execute("""
            INSERT INTO requirements (rfq_id, code, text, category, priority) VALUES
            (1, 'R-001', 'Accommodate 100 participants for general session', 'capacity', 'high'),
            (1, 'R-002', 'Provide 2 breakout rooms for 15 participants each', 'capacity', 'high'),
            (1, 'R-003', 'Event dates: April 14-18, 2024', 'date', 'critical'),
            (1, 'R-004', 'Provide airport shuttle service', 'transport', 'medium'),
            (1, 'R-005', 'Provide complimentary Wi-Fi internet access', 'av', 'medium'),
            (1, 'R-006', 'Comply with FAR 52.204-24 representation requirements', 'clauses', 'critical'),
            (1, 'R-007', 'Submit invoices through IPP system', 'invoice', 'high'),
            (1, 'R-008', 'Provide AV equipment for main room and breakout rooms', 'av', 'high');
        """)
        
        # Insert facility features
        cursor.execute("""
            INSERT INTO facility_features (name, value, source_doc_id) VALUES
            ('shuttle', 'Free airport shuttle service available every 30 minutes', 2),
            ('wifi', 'Complimentary high-speed Wi-Fi throughout the property', 2),
            ('parking', 'Complimentary self-parking for all guests', 2),
            ('breakout_rooms', '2 breakout rooms available, each accommodating 15 participants', 2),
            ('boardroom', 'Executive boardroom available for 20 participants', 2),
            ('av_equipment', 'Full AV equipment including projectors, microphones, and screens', 2);
        """)
        
        # Insert pricing items
        cursor.execute("""
            INSERT INTO pricing_items (rfq_id, name, description, qty, unit, unit_price, total_price, category) VALUES
            (1, 'Room Block - 4 nights', 'Accommodation for 100 participants, 4 nights', 100.0, 'room_night', 135.00, 54000.00, 'lodging'),
            (1, 'Main Room AV Setup', 'Audio-visual equipment for main conference room', 1.0, 'setup', 2500.00, 2500.00, 'av'),
            (1, 'Breakout Room AV', 'Audio-visual equipment for 2 breakout rooms', 2.0, 'room', 500.00, 1000.00, 'av'),
            (1, 'Airport Shuttle Service', 'Shuttle service for airport transfers', 1.0, 'service', 1500.00, 1500.00, 'transportation'),
            (1, 'Project Management', 'Full project management and coordination', 1.0, 'project', 5000.00, 5000.00, 'management');
        """)
        
        # Insert past performance
        cursor.execute("""
            INSERT INTO past_performance (title, client, scope, period, value, ref_info) VALUES
            ('KYNG Statewide BPA Conference Management', 'Kentucky National Guard', 'Full conference management for 75 participants including facility coordination, AV services, and logistics', '2022-2023', 45000.0, '{"poc": "John Smith", "title": "Contracting Officer", "phone": "+1-502-555-0123", "email": "john.smith@ky.ng.mil"}'),
            ('Aviano Air Base Training Seminar', 'US Air Force', 'Training seminar management for 50 participants with AV support and facility coordination', '2023', 32000.0, '{"poc": "Sarah Johnson", "title": "Training Coordinator", "phone": "+39-0434-30-1234", "email": "sarah.johnson@us.af.mil"}'),
            ('Department of Energy Workshop Series', 'US Department of Energy', 'Multi-day workshop series for 120 participants with comprehensive event management', '2023-2024', 85000.0, '{"poc": "Michael Brown", "title": "Program Manager", "phone": "+1-202-555-0456", "email": "michael.brown@energy.gov"}');
        """)
        
        # Insert evidence
        cursor.execute("""
            INSERT INTO evidence (requirement_id, source_doc_id, snippet, score, evidence_type) VALUES
            (1, 2, 'Main conference room accommodates up to 100 participants with theater-style seating', 0.95, 'facility'),
            (2, 2, '2 breakout rooms available, each accommodating 15 participants', 0.90, 'facility'),
            (4, 2, 'Free airport shuttle service available every 30 minutes', 0.85, 'facility'),
            (5, 2, 'Complimentary high-speed Wi-Fi throughout the property', 0.90, 'facility');
        """)
        
        # Insert vector chunks (with REAL array instead of vector)
        cursor.execute("""
            INSERT INTO vector_chunks (document_id, chunk, embedding, chunk_type, page_number) VALUES
            (2, 'Main conference room accommodates up to 100 participants with theater-style seating', ARRAY[0.1, 0.1, 0.1, 0.1, 0.1], 'paragraph', 1),
            (2, '2 breakout rooms available, each accommodating 15 participants', ARRAY[0.1, 0.1, 0.1, 0.1, 0.1], 'paragraph', 1),
            (2, 'Free airport shuttle service available every 30 minutes', ARRAY[0.1, 0.1, 0.1, 0.1, 0.1], 'paragraph', 1),
            (2, 'Complimentary high-speed Wi-Fi throughout the property', ARRAY[0.1, 0.1, 0.1, 0.1, 0.1], 'paragraph', 1);
        """)
        
        print("✅ Sample data inserted successfully!")
        return True
        
    except psycopg2.Error as e:
        print(f"Error inserting sample data: {e}")
        return False
    finally:
        cursor.close()

def verify_tables(conn):
    """Verify tables were created"""
    cursor = conn.cursor()
    
    try:
        print("\n📊 Verifying database structure...")
        
        # List all tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        print(f"✅ Found {len(tables)} tables:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Count records in each table
        table_counts = [
            ("documents", "SELECT COUNT(*) FROM documents"),
            ("requirements", "SELECT COUNT(*) FROM requirements"),
            ("evidence", "SELECT COUNT(*) FROM evidence"),
            ("facility_features", "SELECT COUNT(*) FROM facility_features"),
            ("pricing_items", "SELECT COUNT(*) FROM pricing_items"),
            ("past_performance", "SELECT COUNT(*) FROM past_performance"),
            ("vector_chunks", "SELECT COUNT(*) FROM vector_chunks")
        ]
        
        print(f"\n📈 Record counts:")
        for table_name, query in table_counts:
            cursor.execute(query)
            count = cursor.fetchone()[0]
            print(f"  - {table_name}: {count} records")
        
        return True
        
    except psycopg2.Error as e:
        print(f"Error verifying tables: {e}")
        return False
    finally:
        cursor.close()

def main():
    """Main function"""
    print("🚀 Starting ZgrBid Database Setup...")
    
    # Create connection
    conn = create_connection()
    if not conn:
        print("❌ Failed to connect to database")
        sys.exit(1)
    
    print("✅ Connected to PostgreSQL successfully!")
    
    try:
        # Create tables
        if create_tables(conn):
            print("✅ Tables created successfully!")
            
            # Insert sample data
            if insert_sample_data(conn):
                print("✅ Sample data inserted successfully!")
                
                # Verify tables
                if verify_tables(conn):
                    print("\n🎉 ZgrBid database setup completed!")
                    print("\n📊 Database Summary:")
                    print("- 8 tables created")
                    print("- 4 documents")
                    print("- 8 requirements")
                    print("- 6 facility features")
                    print("- 5 pricing items")
                    print("- 3 past performance records")
                    print("- 4 evidence records")
                    print("- 4 vector chunks")
                    print("- Compliance matrix view created")
                    print("\n💡 Note: Vector similarity search will be available after pgvector installation")
                else:
                    print("❌ Failed to verify tables")
            else:
                print("❌ Failed to insert sample data")
        else:
            print("❌ Failed to create tables")
    
    finally:
        conn.close()
        print("🔌 Database connection closed")

if __name__ == "__main__":
    main()



