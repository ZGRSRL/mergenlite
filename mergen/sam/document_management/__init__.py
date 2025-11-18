"""
SAM Document Management Module
Comprehensive document management system for SAM.gov opportunities
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path for imports
current_dir = Path(__file__).parent
parent_dir = current_dir.parent.parent
sys.path.append(str(parent_dir))

# Import all document management components
from autogen_document_manager import (
    upload_manual_document,
    analyze_manual_document,
    get_manual_documents,
    get_document_analysis_results,
    DocumentMetadata,
    AnalysisResult,
    AutoGenDocumentManager
)

from sam_document_access_v2 import (
    get_opportunity_description_v2,
    get_opportunity_resource_links_v2,
    get_opportunity_documents_complete_v2,
    SAMDocumentAccessManager
)

from ultra_optimized_sam_manager import (
    ultra_bulk_fetch_and_store,
    get_notice_documents_optimized,
    update_data_strategy,
    UltraOptimizedSAMManager
)

from optimized_sam_manager import (
    get_notice_documents,
    bulk_fetch_and_store,
    OptimizedSAMDataManager
)

from smart_document_manager import (
    document_manager,
    download_opportunity_documents,
    get_opportunity_documents,
    get_downloaded_documents,
    SmartDocumentManager
)

from autogen_analysis_center import (
    analyze_opportunity_comprehensive,
    batch_analyze_opportunities,
    generate_analysis_report,
    get_analysis_statistics,
    AutoGenAnalysisCenter
)

# Module version
__version__ = "1.0.0"

# Module info
__author__ = "SAM Document Management Team"
__description__ = "Comprehensive document management system for SAM.gov opportunities"

# Export main classes and functions
__all__ = [
    # AutoGen Document Manager
    'upload_manual_document',
    'analyze_manual_document', 
    'get_manual_documents',
    'get_document_analysis_results',
    'DocumentMetadata',
    'AnalysisResult',
    'AutoGenDocumentManager',
    
    # SAM Document Access v2
    'get_opportunity_description_v2',
    'get_opportunity_resource_links_v2',
    'get_opportunity_documents_complete_v2',
    'SAMDocumentAccessManager',
    
    # Ultra Optimized SAM Manager
    'ultra_bulk_fetch_and_store',
    'get_notice_documents_optimized',
    'update_data_strategy',
    'UltraOptimizedSAMManager',
    
    # Optimized SAM Manager
    'get_notice_documents',
    'bulk_fetch_and_store',
    'OptimizedSAMDataManager',
    
    # Smart Document Manager
    'document_manager',
    'download_opportunity_documents',
    'get_opportunity_documents',
    'get_downloaded_documents',
    'SmartDocumentManager',
    
    # AutoGen Analysis Center
    'analyze_opportunity_comprehensive',
    'batch_analyze_opportunities',
    'generate_analysis_report',
    'get_analysis_statistics',
    'AutoGenAnalysisCenter'
]

def get_module_info():
    """Get module information"""
    return {
        'name': 'SAM Document Management',
        'version': __version__,
        'author': __author__,
        'description': __description__,
        'components': [
            'AutoGen Document Manager',
            'SAM Document Access v2',
            'Ultra Optimized SAM Manager',
            'Optimized SAM Manager',
            'Smart Document Manager',
            'AutoGen Analysis Center'
        ]
    }

def initialize_module():
    """Initialize the document management module"""
    print(f"🚀 SAM Document Management Module v{__version__} initialized")
    print(f"📁 Module path: {current_dir}")
    print(f"🔧 Available components: {len(__all__)}")
    
    return True

if __name__ == "__main__":
    # Test module initialization
    info = get_module_info()
    print("📋 Module Information:")
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    initialize_module()
