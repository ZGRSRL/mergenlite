"""
Test script for 3-pass RFQ pipeline.
Run this to test the complete pipeline.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mergen.api.app.agents.rfq_3pass_orchestrator import run_rfq_3pass_pipeline


if __name__ == "__main__":
    # Test with sample RFQ PDF
    # Update this path to point to an actual RFQ PDF file
    sample_rfq_path = "data/sample_rfq.pdf"
    
    if not Path(sample_rfq_path).exists():
        print(f"ERROR: Sample RFQ PDF not found: {sample_rfq_path}")
        print("Please update sample_rfq_path to point to an actual RFQ PDF file")
        sys.exit(1)
    
    print("=" * 60)
    print("3-PASS RFQ PIPELINE TEST")
    print("=" * 60)
    
    try:
        result = run_rfq_3pass_pipeline(
            rfq_pdf_path=sample_rfq_path,
            seating_chart_pdf_path=None,  # Optional
            use_template_engine=True,
            output_dir=None,  # Will use same directory as RFQ PDF
        )
        
        print("\n✅ Pipeline completed!")
        print(f"\nResults:")
        print(f"  - Analyzer JSON: {'✅' if result.get('analyzer_json') else '❌'}")
        print(f"  - Normalized JSON: {'✅' if result.get('normalized_json') else '❌'}")
        print(f"  - Data Model: {'✅' if result.get('data_model') else '❌'}")
        print(f"  - SOW HTML: {'✅' if result.get('sow_html') else '❌'}")
        print(f"  - SOW PDF: {result.get('sow_pdf_path', '❌ Not generated')}")
        
        if result.get("errors"):
            print(f"\n⚠️  Errors encountered:")
            for error in result["errors"]:
                print(f"  - {error}")
        
        if result.get("sow_pdf_path"):
            print(f"\n📄 SOW PDF generated: {result['sow_pdf_path']}")
        
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

