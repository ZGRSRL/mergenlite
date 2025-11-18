#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MergenLite Opportunity Analysis CLI
AutoGen-based multi-agent system for comprehensive opportunity analysis

Usage:
    python mergenlite_opportunity.py <opportunity_folder> [output_dir]

Example:
    python mergenlite_opportunity.py opportunities/140D0424Q0292
    python mergenlite_opportunity.py samples/ output/
"""

import sys
import os
import codecs
from pathlib import Path

# Windows encoding fix
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from mergenlite_opportunity_pipeline import run_mergen_opportunity_analysis
import logging

def main():
    """Main CLI entry point"""
    
    if len(sys.argv) < 2:
        print("""
MergenLite Opportunity Analysis Pipeline
========================================

Usage (Local Folder):
    python mergenlite_opportunity.py <opportunity_folder> [output_dir]

Usage (SAM.gov):
    python mergenlite_opportunity.py --notice-id <notice_id> [--opportunity-id <opp_id>] [output_dir]
    python mergenlite_opportunity.py --opp-id <opportunity_id> [output_dir]

Arguments:
    opportunity_folder    Path to folder containing PDF documents (local mode)
    --notice-id          SAM.gov Notice ID (SAM.gov mode)
    --opportunity-id      SAM.gov Opportunity ID (optional, SAM.gov mode)
    --opp-id             Alias for --opportunity-id
    output_dir           Optional output directory

Examples:
    # Local folder
    python mergenlite_opportunity.py opportunities/140D0424Q0292
    python mergenlite_opportunity.py samples/ output/
    
    # SAM.gov download
    python mergenlite_opportunity.py --notice-id 57cd76db400c4e7ca895d40bf6454173
    python mergenlite_opportunity.py --opp-id 57cd76db400c4e7ca895d40bf6454173 output/
    
Output:
    - report.json         Full opportunity requirements report (JSON)
    - summary.md         Human-readable summary with go-no go assessment

Requirements:
    - AutoGen: pip install pyautogen
    - OpenAI API Key: Set OPENAI_API_KEY environment variable
    - SAM API Key: Set SAM_API_KEY environment variable (for SAM.gov mode)
    - PDF files in the opportunity folder (for local mode)
        """)
        sys.exit(1)
    
    # Parse arguments
    folder_path = None
    notice_id = None
    opportunity_id = None
    output_dir = None
    
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--notice-id' and i + 1 < len(sys.argv):
            notice_id = sys.argv[i + 1]
            i += 2
        elif (arg == '--opportunity-id' or arg == '--opp-id') and i + 1 < len(sys.argv):
            opportunity_id = sys.argv[i + 1]
            i += 2
        elif not arg.startswith('--'):
            if folder_path is None:
                folder_path = arg
            elif output_dir is None:
                output_dir = arg
            i += 1
        else:
            i += 1
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    logger = logging.getLogger(__name__)
    
    # Validate inputs
    if notice_id or opportunity_id:
        # SAM.gov mode
        logger.info(f"[SAM.gov] Notice ID: {notice_id or 'N/A'}")
        logger.info(f"[SAM.gov] Opportunity ID: {opportunity_id or 'N/A'}")
        if output_dir:
            logger.info(f"[Output] Output directory: {output_dir}")
    elif folder_path:
        # Local folder mode
        folder = Path(folder_path)
        if not folder.exists():
            logger.error(f"[ERROR] Folder not found: {folder_path}")
            sys.exit(1)
        
        if not folder.is_dir():
            logger.error(f"[ERROR] Not a directory: {folder_path}")
            sys.exit(1)
        
        # Check for PDF files
        pdf_files = list(folder.glob("*.pdf"))
        if not pdf_files:
            logger.warning(f"[WARNING] No PDF files found in {folder_path}")
            response = input("Continue anyway? (y/n): ")
            if response.lower() != 'y':
                sys.exit(1)
        
        logger.info(f"[Folder] Opportunity folder: {folder_path}")
        logger.info(f"[PDFs] Found {len(pdf_files)} PDF file(s)")
        if output_dir:
            logger.info(f"[Output] Output directory: {output_dir}")
    else:
        logger.error("[ERROR] Either folder_path or notice_id/opportunity_id must be provided")
        sys.exit(1)
    
    # Run analysis
    try:
        logger.info("\n[START] Starting MergenLite Opportunity Analysis...\n")
        result = run_mergen_opportunity_analysis(
            folder_path=folder_path,
            notice_id=notice_id,
            opportunity_id=opportunity_id,
            output_dir=output_dir
        )
        
        # Determine output paths
        if output_dir:
            output_path = Path(output_dir)
        elif folder_path:
            output_path = Path(folder_path)
        else:
            output_path = Path("downloads")
        
        report_path = output_path / "report.json"
        summary_path = output_path / "summary.md"
        
        print("\n" + "="*60)
        print("[OK] Analysis completed successfully!")
        print("="*60)
        print(f"\n[Report] {report_path}")
        print(f"[Summary] {summary_path}")
        
        # Print summary preview
        if result.get('summary_md'):
            print("\n" + "-"*60)
            print("Summary Preview:")
            print("-"*60)
            summary_text = result['summary_md'][:500] + "..." if len(result['summary_md']) > 500 else result['summary_md']
            print(summary_text)
        
        print("\n" + "="*60)
        
    except Exception as e:
        logger.error(f"\n❌ Analysis failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
