-- Demo data for ZgrBid system
INSERT INTO documents (kind, title, path, meta_json) VALUES
('rfq', 'AQD Seminar RFQ - 140D0424Q0292', 'data/rfq_140D0424Q0292.pdf', '{"rfq_number": "140D0424Q0292", "agency": "Department of Defense", "location": "Orlando, FL", "event_dates": "2024-04-14 to 2024-04-18"}'),
('facility', 'DoubleTree Technical Specifications', 'data/facility_specs.pdf', '{"hotel_name": "DoubleTree by Hilton", "location": "Orlando, FL", "capacity": 100}'),
('past_performance', 'Past Performance Portfolio', 'data/past_performance.pdf', '{"company": "ZgrBid Solutions", "years_experience": 10}'),
('pricing', 'Pricing Spreadsheet', 'data/pricing.xlsx', '{"currency": "USD", "tax_rate": 0.0}');

INSERT INTO requirements (rfq_id, code, text, category, priority) VALUES
(1, 'R-001', 'Accommodate 100 participants for general session', 'capacity', 'high'),
(1, 'R-002', 'Provide 2 breakout rooms for 15 participants each', 'capacity', 'high'),
(1, 'R-003', 'Event dates: April 14-18, 2024', 'date', 'critical'),
(1, 'R-004', 'Provide airport shuttle service', 'transport', 'medium'),
(1, 'R-005', 'Provide complimentary Wi-Fi internet access', 'av', 'medium'),
(1, 'R-006', 'Comply with FAR 52.204-24 representation requirements', 'clauses', 'critical'),
(1, 'R-007', 'Submit invoices through IPP system', 'invoice', 'high'),
(1, 'R-008', 'Provide AV equipment for main room and breakout rooms', 'av', 'high');

INSERT INTO facility_features (name, value, source_doc_id) VALUES
('shuttle', 'Free airport shuttle service available every 30 minutes', 2),
('wifi', 'Complimentary high-speed Wi-Fi throughout the property', 2),
('parking', 'Complimentary self-parking for all guests', 2),
('breakout_rooms', '2 breakout rooms available, each accommodating 15 participants', 2),
('boardroom', 'Executive boardroom available for 20 participants', 2),
('av_equipment', 'Full AV equipment including projectors, microphones, and screens', 2);

INSERT INTO pricing_items (rfq_id, name, description, qty, unit, unit_price, total_price, category) VALUES
(1, 'Room Block - 4 nights', 'Accommodation for 100 participants, 4 nights', 100.0, 'room_night', 135.00, 54000.00, 'lodging'),
(1, 'Main Room AV Setup', 'Audio-visual equipment for main conference room', 1.0, 'setup', 2500.00, 2500.00, 'av'),
(1, 'Breakout Room AV', 'Audio-visual equipment for 2 breakout rooms', 2.0, 'room', 500.00, 1000.00, 'av'),
(1, 'Airport Shuttle Service', 'Shuttle service for airport transfers', 1.0, 'service', 1500.00, 1500.00, 'transportation'),
(1, 'Project Management', 'Full project management and coordination', 1.0, 'project', 5000.00, 5000.00, 'management');

INSERT INTO past_performance (title, client, scope, period, value, ref_info) VALUES
('KYNG Statewide BPA Conference Management', 'Kentucky National Guard', 'Full conference management for 75 participants including facility coordination, AV services, and logistics', '2022-2023', 45000.0, '{"poc": "John Smith", "title": "Contracting Officer", "phone": "+1-502-555-0123", "email": "john.smith@ky.ng.mil"}'),
('Aviano Air Base Training Seminar', 'US Air Force', 'Training seminar management for 50 participants with AV support and facility coordination', '2023', 32000.0, '{"poc": "Sarah Johnson", "title": "Training Coordinator", "phone": "+39-0434-30-1234", "email": "sarah.johnson@us.af.mil"}'),
('Department of Energy Workshop Series', 'US Department of Energy', 'Multi-day workshop series for 120 participants with comprehensive event management', '2023-2024', 85000.0, '{"poc": "Michael Brown", "title": "Program Manager", "phone": "+1-202-555-0456", "email": "michael.brown@energy.gov"}');

INSERT INTO evidence (requirement_id, source_doc_id, snippet, score, evidence_type) VALUES
(1, 2, 'Main conference room accommodates up to 100 participants with theater-style seating', 0.95, 'facility'),
(2, 2, '2 breakout rooms available, each accommodating 15 participants', 0.90, 'facility'),
(4, 2, 'Free airport shuttle service available every 30 minutes', 0.85, 'facility'),
(5, 2, 'Complimentary high-speed Wi-Fi throughout the property', 0.90, 'facility');

INSERT INTO vector_chunks (document_id, chunk, embedding, chunk_type, page_number) VALUES
(2, 'Main conference room accommodates up to 100 participants with theater-style seating', ARRAY[0.1, 0.1, 0.1, 0.1, 0.1]::vector(384), 'paragraph', 1),
(2, '2 breakout rooms available, each accommodating 15 participants', ARRAY[0.1, 0.1, 0.1, 0.1, 0.1]::vector(384), 'paragraph', 1),
(2, 'Free airport shuttle service available every 30 minutes', ARRAY[0.1, 0.1, 0.1, 0.1, 0.1]::vector(384), 'paragraph', 1),
(2, 'Complimentary high-speed Wi-Fi throughout the property', ARRAY[0.1, 0.1, 0.1, 0.1, 0.1]::vector(384), 'paragraph', 1);



