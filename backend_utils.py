#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backend Utilities - NiceGUI için streamlit bağımlılığı olmadan
app.py'deki backend fonksiyonlarının kopyası
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Load environment variables
try:
    from dotenv import load_dotenv
    env_paths = ['mergen/.env', '/app/mergen/.env', '.env', '/app/.env']
    for env_path in env_paths:
        if os.path.exists(env_path):
            load_dotenv(env_path, override=True, verbose=False)
            break
except ImportError:
    pass

# Database imports
try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    from mergenlite_models import Opportunity, Base
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

# SAM Integration
try:
    from sam_integration import SAMIntegration
except ImportError:
    SAMIntegration = None

def get_secret(key: str, default: str = '') -> str:
    """
    Secrets/Environment variable okuma helper'ı
    Öncelik sırası:
    1. Environment variable (os.getenv)
    2. os.environ direkt erişim
    3. Streamlit secrets (eğer varsa, guarded)
    
    Args:
        key: Secret key adı (örn: 'SAM_API_KEY')
        default: Varsayılan değer
    
    Returns:
        Secret değeri veya default
    """
    # 1. os.getenv ile dene
    value = os.getenv(key, '').strip()
    if value:
        return value
    
    # 2. os.environ ile direkt dene
    value = os.environ.get(key, '').strip()
    if value:
        return value
    
    # 3. Streamlit secrets'den dene (eğer varsa, guarded)
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and key in st.secrets:
            value = str(st.secrets[key]).strip()
            if value:
                logger.debug(f"Secret '{key}' loaded from Streamlit secrets")
                return value
    except (ImportError, AttributeError, KeyError):
        # Streamlit yoksa veya secrets yoksa, sessizce geç
        pass
    
    return default

def get_db_session():
    """Database session oluştur"""
    if not DB_AVAILABLE:
        return None
    
    try:
        db_host = os.getenv('DB_HOST', 'localhost')
        env_mode = os.getenv('ENV', 'dev').lower().strip()
        if db_host == 'db' and env_mode == 'dev':
            db_host = 'localhost'
        
        db_user = os.getenv('DB_USER', 'postgres')
        db_password = os.getenv('DB_PASSWORD', 'postgres')
        db_port = os.getenv('DB_PORT', '5432')
        db_name = os.getenv('DB_NAME', 'mergenlite')
        
        DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(bind=engine)
        return SessionLocal()
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

def load_opportunities_from_db(limit: int = 100) -> List[Dict[str, Any]]:
    """Database'den fırsatları yükle - app.py'deki versiyonla uyumlu"""
    if not DB_AVAILABLE:
        logger.warning("⚠️ DB_AVAILABLE = False, boş liste döndürülüyor")
        return []
    
    db = get_db_session()
    if not db:
        logger.warning("⚠️ Database session oluşturulamadı, boş liste döndürülüyor")
        return []
    
    try:
        opportunities = db.query(Opportunity).order_by(Opportunity.created_at.desc()).limit(limit).all()
        logger.info(f"✅ Database'den {len(opportunities)} kayıt yüklendi")
        
        # SQLAlchemy objelerini dict'e dönüştür
        result = []
        for opp in opportunities:
            try:
                # Analiz durumunu kontrol et (relationship hatası olabilir, try-except ile koru)
                analyzed = False
                analysis_status = None
                try:
                    if hasattr(opp, 'analyses') and opp.analyses:
                        latest_analysis = sorted(opp.analyses, key=lambda x: getattr(x, 'start_time', datetime.now()), reverse=True)[0] if opp.analyses else None
                        if latest_analysis:
                            analyzed = getattr(latest_analysis, 'analysis_status', None) == 'COMPLETED'
                            analysis_status = getattr(latest_analysis, 'analysis_status', None)
                except Exception as analysis_error:
                    # Relationship hatası (tablo yapısı uyumsuz olabilir)
                    logger.debug(f"⚠️ Analysis relationship hatası: {analysis_error}")
                    analyzed = False
                    analysis_status = None
                
                # raw_data'dan opportunityId ve noticeId çek
                raw_data = opp.raw_data or {}
                opportunity_id = opp.opportunity_id or ''
                notice_id = getattr(opp, 'notice_id', None) or raw_data.get('noticeId', '') or ''
                
                # Eğer opportunityId yoksa, raw_data'dan çek
                if not opportunity_id and raw_data:
                    opportunity_id = raw_data.get('opportunityId', '') or raw_data.get('noticeId', '')
                
                # Eğer hala yoksa, notice_id'yi kullan
                if not opportunity_id and notice_id:
                    opportunity_id = notice_id
                
                # SAM.gov view link oluştur
                sam_gov_link = getattr(opp, 'sam_gov_link', None)
                if not sam_gov_link:
                    if opportunity_id and len(str(opportunity_id)) == 32:
                        sam_gov_link = f"https://sam.gov/opp/{opportunity_id}/view"
                    elif notice_id:
                        sam_gov_link = f"https://sam.gov/opportunities/search?noticeId={notice_id}"
                
                opp_dict = {
                    'opportunity_id': opportunity_id,
                    'opportunityId': opportunity_id,
                    'notice_id': notice_id,
                    'noticeId': notice_id,
                    'title': getattr(opp, 'title', None) or 'Başlık Yok',
                    'notice_type': getattr(opp, 'notice_type', None),
                    'naics_code': getattr(opp, 'naics_code', None),
                    'response_deadline': getattr(opp, 'response_deadline', None),
                    'estimated_value': float(getattr(opp, 'estimated_value', 0)) if getattr(opp, 'estimated_value', None) else None,
                    'place_of_performance': getattr(opp, 'place_of_performance', None),
                    'sam_gov_link': sam_gov_link,
                    'samGovLink': sam_gov_link,
                    'created_at': getattr(opp, 'created_at', None),
                    'updated_at': getattr(opp, 'updated_at', None),
                    'raw_data': raw_data,
                    'analyzed': analyzed,
                    'analysis_status': analysis_status
                }
                result.append(opp_dict)
            except Exception as opp_error:
                logger.warning(f"⚠️ Kayıt parse hatası: {opp_error}")
                continue
        
        logger.info(f"✅ {len(result)} kayıt başarıyla parse edildi")
        return result
    except Exception as e:
        logger.error(f"❌ Fırsat yükleme hatası: {e}", exc_info=True)
        return []
    finally:
        if db:
            db.close()

def sync_opportunities_from_sam(naics_code: str = "721110", days_back: int = 30, limit: int = 100, show_progress: bool = True):
    """SAM.gov'dan fırsatları senkronize et"""
    try:
        if not SAMIntegration:
            logger.error("SAMIntegration not available")
            return
        
        sam = SAMIntegration()
        if not sam.api_key:
            logger.error("SAM_API_KEY not found")
            return
        
        opportunities = sam.fetch_opportunities(
            naics_codes=[naics_code],
            days_back=days_back,
            limit=limit
        )
        
        if not opportunities:
            logger.warning(f"No opportunities found for NAICS {naics_code}")
            return
        
        # Database'e kaydet
        if not DB_AVAILABLE:
            logger.warning("Database not available, skipping save")
            return
        
        db = get_db_session()
        if not db:
            return
        
        try:
            count_new = 0
            count_updated = 0
            
            for opp_data in opportunities:
                opportunity_id = opp_data.get('opportunityId', '').strip()
                notice_id = opp_data.get('noticeId', '').strip() or opp_data.get('solicitationNumber', '').strip()
                
                if not opportunity_id:
                    raw_data = opp_data.get('raw_data', {})
                    if isinstance(raw_data, dict):
                        opportunity_id = raw_data.get('opportunityId', '').strip()
                
                if not opportunity_id:
                    continue
                
                existing = db.query(Opportunity).filter(Opportunity.opportunity_id == opportunity_id).first()
                
                if existing:
                    existing.raw_data = opp_data.get('raw_data', opp_data)
                    existing.updated_at = datetime.now()
                    count_updated += 1
                else:
                    new_opp = Opportunity(
                        opportunity_id=opportunity_id,
                        notice_id=notice_id,
                        title=opp_data.get('title', 'Başlık Yok'),
                        raw_data=opp_data.get('raw_data', opp_data)
                    )
                    db.add(new_opp)
                    count_new += 1
            
            db.commit()
            logger.info(f"Synced: {count_new} new, {count_updated} updated")
        except Exception as e:
            db.rollback()
            logger.error(f"Database save error: {e}", exc_info=True)
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Sync error: {e}", exc_info=True)

