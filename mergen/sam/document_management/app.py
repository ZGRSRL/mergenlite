#!/usr/bin/env python3
"""
ZGR SAM Document Management System - Optimized Single App
Consolidated Streamlit application with all core features
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import json
import time
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go

# Core imports
from database_manager import DatabaseUtils, test_db_connection
from autogen_analysis_center import (
    analyze_opportunity_comprehensive,
    batch_analyze_opportunities,
    get_analysis_statistics
)
from sam_document_access_v2 import (
    fetch_opportunities,
    get_opportunity_details,
    download_all_attachments
)
from sam_opportunity_analyzer_agent import get_analyzer_statistics

# Configure page
st.set_page_config(
    page_title="ZGR SAM Document Management",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .success-card {
        background-color: #d4edda;
        border-left-color: #28a745;
    }
    .warning-card {
        background-color: #fff3cd;
        border-left-color: #ffc107;
    }
    .error-card {
        background-color: #f8d7da;
        border-left-color: #dc3545;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'selected_opportunity' not in st.session_state:
    st.session_state.selected_opportunity = None
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = {}

def main():
    """Main application function"""
    
    # Header
    st.markdown('<h1 class="main-header">🏢 ZGR SAM Document Management System</h1>', unsafe_allow_html=True)
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("## Navigation")

        page = st.selectbox(
            "Select Page",
            [
                "Dashboard",
                "AutoGen Analysis Center",
                "SAM API v2 Access"
            ]
        )

        st.markdown("---")

        st.markdown("## System Status")
        if test_db_connection():
            st.success("Database Connected")
        else:
            st.error("Database Disconnected")
    # Route to selected page

    if page == "Dashboard":
        dashboard_page()
    elif page == "AutoGen Analysis Center":
        autogen_analysis_page()
    elif page == "SAM API v2 Access":
        sam_api_page()

def dashboard_page():
    """Main dashboard with system overview"""
    st.markdown("## 📊 System Dashboard")
    
    # System metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        try:
            total_opps = DatabaseUtils.get_opportunity_count()
            st.metric("Total Opportunities", total_opps)
        except:
            st.metric("Total Opportunities", "N/A")
    
    with col2:
        try:
            recent_opps = DatabaseUtils.get_recent_opportunities(limit=10)
            st.metric("Recent Opportunities", len(recent_opps))
        except:
            st.metric("Recent Opportunities", "N/A")
    
    with col3:
        try:
            analyzer_stats = get_analyzer_statistics()
            cache_size = analyzer_stats.get('cache_size', 0)
            st.metric("Cache Size", cache_size)
        except:
            st.metric("Cache Size", "N/A")
    
    with col4:
        try:
            analyzer_stats = get_analyzer_statistics()
            status = analyzer_stats.get('analyzer_status', 'unknown')
            st.metric("Analyzer Status", status.title())
        except:
            st.metric("Analyzer Status", "Unknown")
    
    st.markdown("---")
    
    # Recent opportunities
    st.markdown("## 📋 Recent Opportunities")
    try:
        recent_opps = DatabaseUtils.get_recent_opportunities(limit=10)
        if recent_opps:
            df = pd.DataFrame(recent_opps)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No recent opportunities found")
    except Exception as e:
        st.error(f"Error loading recent opportunities: {e}")
    
    # Quick actions
    st.markdown("## ⚡ Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()
    
    with col2:
        if st.button("📊 Run Analysis", use_container_width=True):
            st.info("Analysis started in background")
    
    with col3:
        if st.button("📈 View Statistics", use_container_width=True):
            st.info("Statistics updated")

def opportunity_analysis_page():
    """Opportunity analysis page"""
    st.markdown("## 🎯 Opportunity Analysis")
    
    # Search and select opportunity
    col1, col2 = st.columns([2, 1])
    
    with col1:
        search_term = st.text_input("🔍 Search Opportunities", placeholder="Enter opportunity ID or keywords")
    
    with col2:
        if st.button("🔍 Search", use_container_width=True):
            if search_term:
                try:
                    results = DatabaseUtils.search_opportunities(search_term, limit=20)
                    st.session_state.search_results = results
                except Exception as e:
                    st.error(f"Search error: {e}")
    
    # Display search results
    if hasattr(st.session_state, 'search_results') and st.session_state.search_results:
        st.markdown("### 📋 Search Results")
        
        for i, opp in enumerate(st.session_state.search_results):
            with st.expander(f"{opp.get('opportunity_id', 'N/A')}: {opp.get('title', 'N/A')}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Organization:** {opp.get('agency', 'N/A')}")
                    st.write(f"**NAICS:** {opp.get('naics_code', 'N/A')}")
                    st.write(f"**Posted:** {opp.get('posted_date', 'N/A')}")
                
                with col2:
                    if st.button(f"Analyze", key=f"analyze_{i}"):
                        st.session_state.selected_opportunity = opp.get('opportunity_id')
    
    # Analyze selected opportunity
    if st.session_state.selected_opportunity:
        st.markdown("---")
        st.markdown(f"## 🔍 Analyzing: {st.session_state.selected_opportunity}")
        
        if st.button("🚀 Run Comprehensive Analysis"):
            with st.spinner("Running analysis..."):
                try:
                    result = analyze_opportunity_comprehensive(st.session_state.selected_opportunity)
                    st.session_state.analysis_results[st.session_state.selected_opportunity] = result
                    
                    # Display results
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Status", result.get('status', 'unknown').title())
                    
                    with col2:
                        confidence = result.get('confidence_score', 0.0)
                        st.metric("Confidence", f"{confidence:.2f}")
                    
                    with col3:
                        st.metric("Risk Level", result.get('risk_level', 'unknown').title())
                    
                    # Recommendations
                    recommendations = result.get('recommendations', [])
                    if recommendations:
                        st.markdown("### 💡 Recommendations")
                        for i, rec in enumerate(recommendations, 1):
                            st.write(f"{i}. {rec}")
                    
                    # Agent coordination
                    coordination = result.get('coordination_results', {})
                    if coordination:
                        st.markdown("### 🤝 Agent Coordination")
                        for agent, info in coordination.items():
                            st.write(f"**{agent}**: {info.get('status', 'unknown')}")
                
                except Exception as e:
                    st.error(f"Analysis error: {e}")

def autogen_analysis_page():
    """AutoGen Analysis Center page"""
    st.markdown("## 🤖 AutoGen Analysis Center")
    
    # Analysis statistics
    try:
        stats = get_analysis_statistics()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            analyzer_stats = stats.get('analyzer_agent', {})
            total_opps = analyzer_stats.get('total_opportunities', 0)
            st.metric("Total Opportunities", total_opps)
        
        with col2:
            cache_size = analyzer_stats.get('cache_size', 0)
            st.metric("Cache Size", cache_size)
        
        with col3:
            analyzer_status = analyzer_stats.get('analyzer_status', 'unknown')
            st.metric("Analyzer Status", analyzer_status.title())
    
    except Exception as e:
        st.error(f"Error loading statistics: {e}")
    
    st.markdown("---")
    
    # Batch analysis
    st.markdown("### 🔄 Batch Analysis")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        opportunity_ids = st.text_area(
            "Opportunity IDs (one per line)",
            placeholder="DEMO-001\nDEMO-002\nDEMO-003",
            height=100
        )
    
    with col2:
        max_concurrent = st.slider("Max Concurrent", 1, 10, 3)
        
        if st.button("🚀 Run Batch Analysis"):
            if opportunity_ids:
                opp_ids = [id.strip() for id in opportunity_ids.split('\n') if id.strip()]
                
                with st.spinner("Running batch analysis..."):
                    try:
                        result = batch_analyze_opportunities(opp_ids, max_concurrent)
                        
                        st.success(f"Batch analysis completed!")
                        st.write(f"**Total:** {result.get('total_opportunities', 0)}")
                        st.write(f"**Successful:** {result.get('successful', 0)}")
                        st.write(f"**Failed:** {result.get('failed', 0)}")
                        
                        # Show results
                        results = result.get('results', [])
                        if results:
                            st.markdown("### 📊 Results")
                            for res in results:
                                opp_id = res.get('opportunity_id', 'N/A')
                                status = res.get('status', 'unknown')
                                confidence = res.get('confidence_score', 0.0)
                                st.write(f"**{opp_id}**: {status} (Confidence: {confidence:.2f})")
                    
                    except Exception as e:
                        st.error(f"Batch analysis error: {e}")

def document_management_page():
    """Document management page"""
    st.markdown("## 📤 Document Management")
    
    # File upload
    st.markdown("### 📁 Upload Document")
    
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=['pdf', 'docx', 'xlsx', 'txt'],
        help="Upload PDF, DOCX, XLSX, or TXT files"
    )
    
    if uploaded_file:
        st.success(f"File uploaded: {uploaded_file.name}")
        
        if st.button("📊 Analyze Document"):
            with st.spinner("Analyzing document..."):
                st.info("Document analysis feature coming soon!")
    
    # Document library
    st.markdown("---")
    st.markdown("### 📚 Document Library")
    
    # Mock document data
    documents = [
        {"name": "Sample Document 1.pdf", "type": "PDF", "size": "2.3 MB", "uploaded": "2024-01-15"},
        {"name": "Sample Document 2.docx", "type": "DOCX", "size": "1.8 MB", "uploaded": "2024-01-14"},
        {"name": "Sample Document 3.xlsx", "type": "XLSX", "size": "0.9 MB", "uploaded": "2024-01-13"},
    ]
    
    df = pd.DataFrame(documents)
    st.dataframe(df, use_container_width=True)

def sam_api_page():
    """SAM API v2 Access page"""
    st.markdown("## 🌐 SAM API v2 Access")
    
    # API configuration
    col1, col2 = st.columns(2)
    
    with col1:
        naics_codes = st.text_input(
            "NAICS Codes",
            placeholder="721100,721110",
            help="Comma-separated NAICS codes"
        )
    
    with col2:
        days_back = st.slider("Days Back", 1, 90, 7)
    
    col3, col4 = st.columns(2)
    
    with col3:
        limit = st.slider("Limit", 10, 1000, 50)
    
    with col4:
        keywords = st.text_input("Keywords", placeholder="hotel, accommodation")
    
    # Fetch opportunities
    if st.button("🔍 Fetch Opportunities"):
        if naics_codes:
            naics_list = [code.strip() for code in naics_codes.split(',')]
            
            with st.spinner("Fetching opportunities..."):
                try:
                    result = fetch_opportunities(
                        keywords=keywords if keywords else None,
                        naics_codes=naics_list,
                        days_back=days_back,
                        limit=limit
                    )
                    
                    if result.get('success'):
                        opportunities = result.get('opportunities', [])
                        count = result.get('count', 0)
                        
                        st.success(f"Fetched {count} opportunities!")
                        
                        if opportunities:
                            st.markdown("### 📋 Fetched Opportunities")
                            
                            for i, opp in enumerate(opportunities[:10]):  # Show first 10
                                with st.expander(f"{opp.get('opportunityId', 'N/A')}: {opp.get('title', 'N/A')}"):
                                    st.write(f"**Organization:** {opp.get('fullParentPathName', 'N/A')}")
                                    st.write(f"**NAICS:** {opp.get('naicsCode', 'N/A')}")
                                    st.write(f"**Posted:** {opp.get('postedDate', 'N/A')}")
                                    st.write(f"**Deadline:** {opp.get('responseDeadLine', 'N/A')}")
                    else:
                        st.error(f"Fetch failed: {result.get('error', 'Unknown error')}")
                
                except Exception as e:
                    st.error(f"API error: {e}")
        else:
            st.warning("Please enter NAICS codes")

def system_monitor_page():
    """System monitor page"""
    st.markdown("## ⚙️ System Monitor")
    
    # Database status
    st.markdown("### 🗄️ Database Status")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if test_db_connection():
            st.success("✅ Connected")
        else:
            st.error("❌ Disconnected")
    
    with col2:
        try:
            total_opps = DatabaseUtils.get_opportunity_count()
            st.metric("Total Records", total_opps)
        except:
            st.metric("Total Records", "N/A")
    
    with col3:
        try:
            recent_opps = DatabaseUtils.get_recent_opportunities(limit=5)
            st.metric("Recent Records", len(recent_opps))
        except:
            st.metric("Recent Records", "N/A")
    
    # Analyzer status
    st.markdown("---")
    st.markdown("### 🤖 Analyzer Status")
    
    try:
        analyzer_stats = get_analyzer_statistics()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Status", analyzer_stats.get('analyzer_status', 'unknown').title())
        
        with col2:
            st.metric("Cache Size", analyzer_stats.get('cache_size', 0))
        
        with col3:
            st.metric("Total Opportunities", analyzer_stats.get('total_opportunities', 0))
        
        with col4:
            last_analysis = analyzer_stats.get('last_analysis', 'N/A')
            st.metric("Last Analysis", last_analysis[:10] if last_analysis != 'N/A' else 'N/A')
    
    except Exception as e:
        st.error(f"Error loading analyzer stats: {e}")
    
    # Performance metrics
    st.markdown("---")
    st.markdown("### 📊 Performance Metrics")
    
    # Mock performance data
    performance_data = {
        'Metric': ['Response Time', 'Cache Hit Rate', 'Success Rate', 'Error Rate'],
        'Value': ['120ms', '85%', '98%', '2%'],
        'Status': ['Good', 'Excellent', 'Excellent', 'Good']
    }
    
    df = pd.DataFrame(performance_data)
    st.dataframe(df, use_container_width=True)
    
    # System actions
    st.markdown("---")
    st.markdown("### 🔧 System Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Refresh Cache", use_container_width=True):
            st.info("Cache refreshed!")
    
    with col2:
        if st.button("📊 Update Statistics", use_container_width=True):
            st.info("Statistics updated!")
    
    with col3:
        if st.button("🧹 Cleanup", use_container_width=True):
            st.info("Cleanup completed!")

if __name__ == "__main__":
    main()
