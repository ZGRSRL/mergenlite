"""
Search for opportunities by awardee name in database
Awardee bilgisi raw_data JSON'unda saklanıyor olabilir
"""
import os
import sys
from typing import List, Dict, Any
import json

# Database connection
try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    import psycopg2
except ImportError:
    print("[ERROR] Required packages not installed. Install: pip install sqlalchemy psycopg2-binary")
    sys.exit(1)

# Database connection string
DB_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://postgres:postgres@localhost:5432/mergenlite'
)

def get_table_columns(session, table_name: str) -> List[str]:
    """Get column names for a table"""
    try:
        query = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = :table_name
            ORDER BY ordinal_position
        """)
        rows = session.execute(query, {'table_name': table_name}).fetchall()
        return [row[0] for row in rows]
    except:
        return []

def search_awardee_in_db(awardee_name: str, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Search for opportunities by awardee name
    Searches in raw_data JSON field and other text fields
    """
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    results = []
    
    try:
        # First, check what columns exist
        columns = get_table_columns(session, 'opportunities')
        print(f"[DEBUG] Available columns: {', '.join(columns)}")
        
        # Build SELECT clause based on available columns
        select_fields = []
        if 'opportunity_id' in columns:
            select_fields.append('opportunity_id')
        if 'id' in columns:
            select_fields.append('id')
        if 'notice_id' in columns:
            select_fields.append('notice_id')
        if 'title' in columns:
            select_fields.append('title')
        if 'agency' in columns:
            select_fields.append('agency')
        if 'notice_type' in columns:
            select_fields.append('notice_type')
        if 'posted_date' in columns:
            select_fields.append('posted_date')
        if 'raw_data' in columns:
            select_fields.append('raw_data')
        if 'sam_gov_link' in columns:
            select_fields.append('sam_gov_link')
        if 'description' in columns:
            select_fields.append('description')
        
        if not select_fields:
            print("[ERROR] No valid columns found in opportunities table")
            return []
        
        # PostgreSQL JSON search - awardee bilgisi raw_data içinde olabilir
        search_pattern = f"%{awardee_name}%"
        
        # Build WHERE clause
        where_conditions = []
        if 'title' in columns:
            where_conditions.append("LOWER(title) LIKE LOWER(:pattern)")
        if 'description' in columns:
            where_conditions.append("LOWER(description) LIKE LOWER(:pattern)")
        if 'raw_data' in columns:
            where_conditions.append("LOWER(raw_data::text) LIKE LOWER(:pattern)")
        
        if not where_conditions:
            print("[ERROR] No searchable columns found")
            return []
        
        # Build ORDER BY
        order_by = "ORDER BY "
        if 'posted_date' in columns:
            order_by += "posted_date DESC NULLS LAST"
        elif 'created_at' in columns:
            order_by += "created_at DESC NULLS LAST"
        else:
            order_by += "opportunity_id DESC"
        
        # SQL query
        query_text = f"""
            SELECT {', '.join(select_fields)}
            FROM opportunities
            WHERE {' OR '.join(where_conditions)}
            {order_by}
            LIMIT :limit
        """
        
        query = text(query_text)
        rows = session.execute(query, {
            'pattern': search_pattern,
            'limit': limit
        }).fetchall()
        
        for row in rows:
            # Convert row to dict
            row_dict = dict(row._mapping) if hasattr(row, '_mapping') else dict(zip(select_fields, row))
            
            raw_data = row_dict.get('raw_data') or {}
            
            # Awardee bilgisini bul
            awardee = None
            if isinstance(raw_data, dict):
                # Farklı alanlarda awardee bilgisi olabilir
                awardee = (
                    raw_data.get('awardee') or
                    raw_data.get('awardeeName') or
                    raw_data.get('contractorName') or
                    raw_data.get('vendorName') or
                    raw_data.get('awardeeNameText') or
                    raw_data.get('contractor') or
                    None
                )
            
            result = {
                'opportunity_id': row_dict.get('opportunity_id'),
                'id': row_dict.get('id'),
                'notice_id': row_dict.get('notice_id'),
                'title': row_dict.get('title'),
                'agency': row_dict.get('agency'),
                'notice_type': row_dict.get('notice_type'),
                'posted_date': str(row_dict.get('posted_date')) if row_dict.get('posted_date') else None,
                'awardee': awardee,
                'sam_gov_link': row_dict.get('sam_gov_link'),
                'raw_data_keys': list(raw_data.keys()) if isinstance(raw_data, dict) else []
            }
            results.append(result)
        
        return results
        
    except Exception as e:
        print(f"[ERROR] Database search error: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        session.close()
        engine.dispose()

def search_by_notice_id(notice_id: str) -> Dict[str, Any]:
    """Search for a specific notice by notice ID"""
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Check available columns
        columns = get_table_columns(session, 'opportunities')
        
        select_fields = []
        if 'opportunity_id' in columns:
            select_fields.append('opportunity_id')
        if 'id' in columns:
            select_fields.append('id')
        if 'notice_id' in columns:
            select_fields.append('notice_id')
        if 'title' in columns:
            select_fields.append('title')
        if 'agency' in columns:
            select_fields.append('agency')
        if 'notice_type' in columns:
            select_fields.append('notice_type')
        if 'posted_date' in columns:
            select_fields.append('posted_date')
        if 'raw_data' in columns:
            select_fields.append('raw_data')
        if 'sam_gov_link' in columns:
            select_fields.append('sam_gov_link')
        
        # Build WHERE clause - try notice_id first, then opportunity_id
        where_clause = "notice_id = :notice_id" if 'notice_id' in columns else "opportunity_id = :notice_id"
        
        query_text = f"""
            SELECT {', '.join(select_fields)}
            FROM opportunities
            WHERE {where_clause}
            LIMIT 1
        """
        
        query = text(query_text)
        row = session.execute(query, {'notice_id': notice_id}).fetchone()
        
        if row:
            row_dict = dict(row._mapping) if hasattr(row, '_mapping') else dict(zip(select_fields, row))
            
            raw_data = row_dict.get('raw_data') or {}
            awardee = None
            if isinstance(raw_data, dict):
                awardee = (
                    raw_data.get('awardee') or
                    raw_data.get('awardeeName') or
                    raw_data.get('contractorName') or
                    raw_data.get('vendorName') or
                    None
                )
            
            return {
                'id': row_dict.get('id'),
                'opportunity_id': row_dict.get('opportunity_id'),
                'notice_id': row_dict.get('notice_id'),
                'title': row_dict.get('title'),
                'agency': row_dict.get('agency'),
                'notice_type': row_dict.get('notice_type'),
                'posted_date': str(row_dict.get('posted_date')) if row_dict.get('posted_date') else None,
                'awardee': awardee,
                'sam_gov_link': row_dict.get('sam_gov_link'),
                'raw_data_sample': {k: v for k, v in (raw_data.items() if isinstance(raw_data, dict) else []) if k in ['awardee', 'awardeeName', 'contractorName', 'vendorName', 'title', 'noticeId']}
            }
        return None
        
    except Exception as e:
        print(f"[ERROR] Database search error: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        session.close()
        engine.dispose()

if __name__ == "__main__":
    import argparse
    import sys
    
    # Fix encoding for Windows console
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    parser = argparse.ArgumentParser(description='Search for opportunities by awardee name')
    parser.add_argument('search_term', nargs='?', default='nmaiol', help='Awardee name or search term (default: nmaiol)')
    parser.add_argument('--notice-id', help='Search by specific notice ID')
    parser.add_argument('--limit', type=int, default=50, help='Maximum results (default: 50)')
    
    args = parser.parse_args()
    
    if args.notice_id:
        print(f"[SEARCH] Searching for notice ID: {args.notice_id}\n")
        result = search_by_notice_id(args.notice_id)
        if result:
            print(f"[FOUND] Notice found:")
            print(f"   Notice ID: {result['notice_id']}")
            print(f"   Title: {result['title']}")
            print(f"   Agency: {result['agency']}")
            print(f"   Notice Type: {result['notice_type']}")
            print(f"   Awardee: {result['awardee']}")
            print(f"   Posted Date: {result['posted_date']}")
            print(f"   SAM.gov Link: {result['sam_gov_link']}")
            if result.get('raw_data_sample'):
                print(f"\n   Raw Data Sample:")
                for k, v in result['raw_data_sample'].items():
                    print(f"      {k}: {v}")
        else:
            print(f"[NOT FOUND] Notice ID {args.notice_id} not found in database")
    else:
        print(f"[SEARCH] Searching for awardee/company: '{args.search_term}'\n")
        results = search_awardee_in_db(args.search_term, limit=args.limit)
        
        if results:
            print(f"[FOUND] Found {len(results)} result(s):\n")
            for i, result in enumerate(results, 1):
                print(f"{i}. Notice ID: {result['notice_id']}")
                print(f"   Title: {result['title']}")
                print(f"   Agency: {result['agency']}")
                print(f"   Notice Type: {result['notice_type']}")
                print(f"   Awardee: {result['awardee'] or 'N/A'}")
                print(f"   Posted Date: {result['posted_date']}")
                print(f"   SAM.gov Link: {result['sam_gov_link']}")
                if result.get('raw_data_keys'):
                    print(f"   Raw Data Keys: {', '.join(result['raw_data_keys'][:10])}")
                print()
        else:
            print(f"[NOT FOUND] No results found for '{args.search_term}'")
            print("\n[TIPS]")
            print("   - Try different spellings or partial matches")
            print("   - Check if the notice is in the database")
            print("   - Search by notice ID: python search_awardee.py --notice-id W50S8R26Q0003B")

