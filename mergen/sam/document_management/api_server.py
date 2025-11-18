"""
API Endpoints - REST API for SAM Document Management
Provides endpoints for fetching, triggering analysis, and getting results
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
from io import BytesIO

# Import our modules
from sam_document_access_v2 import fetch_opportunities, get_opportunity_details, download_all_attachments
from attachment_pipeline import process_document
from job_manager import enqueue_analysis, get_job_status, get_job_results, start_job_worker
from autogen_orchestrator import run_full_analysis

logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

# Opportunity Management Endpoints

@app.route('/opportunities/fetch', methods=['POST'])
def fetch_opportunities_endpoint():
    """Fetch opportunities from SAM.gov"""
    try:
        data = request.get_json() or {}
        
        keywords = data.get('keywords', [])
        naics_codes = data.get('naics_codes', [])
        days_back = data.get('days_back', 7)
        limit = data.get('limit', 100)
        
        result = fetch_opportunities(
            keywords=keywords,
            naics_codes=naics_codes,
            days_back=days_back,
            limit=limit
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Fetch opportunities failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/opportunities/<notice_id>/details', methods=['GET'])
def get_opportunity_details_endpoint(notice_id: str):
    """Get detailed information for a specific opportunity"""
    try:
        result = get_opportunity_details(notice_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Get opportunity details failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/opportunities/<notice_id>/attachments', methods=['POST'])
def download_attachments_endpoint(notice_id: str):
    """Download all attachments for an opportunity"""
    try:
        result = download_all_attachments(notice_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Download attachments failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Analysis Endpoints

@app.route('/analysis/trigger', methods=['POST'])
def trigger_analysis_endpoint():
    """Trigger analysis for an opportunity"""
    try:
        data = request.get_json() or {}
        
        notice_id = data.get('notice_id')
        if not notice_id:
            return jsonify({'success': False, 'error': 'notice_id is required'}), 400
        
        job_id = enqueue_analysis(notice_id)
        
        if job_id:
            return jsonify({
                'success': True,
                'job_id': job_id,
                'notice_id': notice_id,
                'message': 'Analysis job enqueued successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to enqueue analysis'}), 500
            
    except Exception as e:
        logger.error(f"Trigger analysis failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/analysis/status', methods=['GET'])
def get_analysis_status_endpoint():
    """Get analysis job status"""
    try:
        job_id = request.args.get('job_id')
        if not job_id:
            return jsonify({'success': False, 'error': 'job_id is required'}), 400
        
        result = get_job_status(job_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Get analysis status failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/analysis/results', methods=['GET'])
def get_analysis_results_endpoint():
    """Get analysis results for a notice"""
    try:
        notice_id = request.args.get('notice_id')
        if not notice_id:
            return jsonify({'success': False, 'error': 'notice_id is required'}), 400
        
        result = get_job_results(notice_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Get analysis results failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Document Processing Endpoints

@app.route('/documents/process', methods=['POST'])
def process_document_endpoint():
    """Process a document and extract text chunks"""
    try:
        data = request.get_json() or {}
        
        file_path = data.get('file_path')
        if not file_path:
            return jsonify({'success': False, 'error': 'file_path is required'}), 400
        
        result = process_document(file_path)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Process document failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Export Endpoints

@app.route('/export/analysis.csv', methods=['GET'])
def export_analysis_csv():
    """Export analysis results as CSV"""
    try:
        # This would typically query the database for results
        # For now, return a sample CSV
        
        # Sample data
        data = {
            'Notice ID': ['TEST001', 'TEST002'],
            'Title': ['Test Opportunity 1', 'Test Opportunity 2'],
            'Go/No-Go Score': [85, 72],
            'Confidence': [0.8, 0.7],
            'Status': ['Completed', 'Completed'],
            'Analysis Date': [datetime.now().isoformat(), datetime.now().isoformat()]
        }
        
        df = pd.DataFrame(data)
        
        # Create CSV in memory
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'analysis_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
        
    except Exception as e:
        logger.error(f"Export CSV failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/export/analysis.json', methods=['GET'])
def export_analysis_json():
    """Export analysis results as JSON"""
    try:
        # This would typically query the database for results
        # For now, return sample data
        
        sample_data = {
            'export_timestamp': datetime.now().isoformat(),
            'total_records': 2,
            'results': [
                {
                    'notice_id': 'TEST001',
                    'title': 'Test Opportunity 1',
                    'go_no_go_score': 85,
                    'confidence': 0.8,
                    'summary': 'Favorable opportunity with good potential',
                    'risks': [
                        {'type': 'technical', 'level': 'medium', 'description': 'Complex requirements'}
                    ],
                    'requirements': [
                        {'type': 'mandatory', 'description': 'Valid certification required'}
                    ]
                },
                {
                    'notice_id': 'TEST002',
                    'title': 'Test Opportunity 2',
                    'go_no_go_score': 72,
                    'confidence': 0.7,
                    'summary': 'Moderate opportunity with some concerns',
                    'risks': [
                        {'type': 'timeline', 'level': 'high', 'description': 'Tight deadline'}
                    ],
                    'requirements': [
                        {'type': 'mandatory', 'description': 'Previous experience required'}
                    ]
                }
            ]
        }
        
        return jsonify(sample_data)
        
    except Exception as e:
        logger.error(f"Export JSON failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Bulk Operations

@app.route('/analysis/bulk-trigger', methods=['POST'])
def bulk_trigger_analysis():
    """Trigger analysis for multiple opportunities"""
    try:
        data = request.get_json() or {}
        
        notice_ids = data.get('notice_ids', [])
        if not notice_ids:
            return jsonify({'success': False, 'error': 'notice_ids is required'}), 400
        
        job_ids = []
        for notice_id in notice_ids:
            job_id = enqueue_analysis(notice_id)
            if job_id:
                job_ids.append(job_id)
        
        return jsonify({
            'success': True,
            'job_ids': job_ids,
            'total_jobs': len(job_ids),
            'message': f'Enqueued {len(job_ids)} analysis jobs'
        })
        
    except Exception as e:
        logger.error(f"Bulk trigger analysis failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Statistics Endpoints

@app.route('/stats/overview', methods=['GET'])
def get_stats_overview():
    """Get system statistics overview"""
    try:
        # This would typically query the database for real statistics
        # For now, return sample data
        
        stats = {
            'total_opportunities': 150,
            'total_analyses': 45,
            'completed_analyses': 42,
            'failed_analyses': 3,
            'average_score': 78.5,
            'average_confidence': 0.82,
            'last_analysis': datetime.now().isoformat(),
            'system_status': 'healthy'
        }
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Get stats overview failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Error handlers

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

# Startup function
def start_api_server(host='localhost', port=5000, debug=False):
    """Start the API server"""
    try:
        # Start job worker
        start_job_worker()
        
        logger.info(f"Starting API server on {host}:{port}")
        app.run(host=host, port=port, debug=debug)
        
    except Exception as e:
        logger.error(f"API server startup failed: {e}")

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Start the server
    start_api_server(debug=True)

