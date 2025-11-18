"""
AutoGen Configuration for ZgrBid System
Configuration files and agent definitions
"""

import autogen
from typing import Dict, List, Any, Optional
import json
import os

# AutoGen Agent Configurations
def get_agent_configs() -> Dict[str, Dict[str, Any]]:
    """Get configuration for all AutoGen agents"""
    
    return {
        "document_processor": {
            "name": "DocumentProcessor",
            "model": "gpt-4",
            "temperature": 0.1,
            "max_tokens": 4000,
            "system_message": """
            You are a document processing specialist for government contracting.
            Your expertise includes:
            - PDF and Excel document analysis
            - Structured data extraction
            - Metadata identification
            - Content categorization
            
            Always provide accurate, detailed analysis of documents.
            """
        },
        
        "requirements_extractor": {
            "name": "RequirementsExtractor", 
            "model": "gpt-4",
            "temperature": 0.1,
            "max_tokens": 4000,
            "system_message": """
            You are a requirements extraction specialist for government RFQs.
            Your expertise includes:
            - RFQ requirement identification
            - Requirement categorization (capacity, date, transport, av, invoice, clauses)
            - Priority assessment (low, medium, high, critical)
            - FAR clause recognition
            - Compliance requirement analysis
            
            Extract requirements with high accuracy and proper categorization.
            """
        },
        
        "compliance_analyst": {
            "name": "ComplianceAnalyst",
            "model": "gpt-4", 
            "temperature": 0.1,
            "max_tokens": 4000,
            "system_message": """
            You are a compliance analysis specialist for government proposals.
            Your expertise includes:
            - Requirement vs capability matching
            - Evidence identification and scoring
            - Risk assessment (low, medium, high, critical)
            - Gap analysis
            - Mitigation strategy development
            
            Provide thorough compliance analysis with actionable insights.
            """
        },
        
        "pricing_specialist": {
            "name": "PricingSpecialist",
            "model": "gpt-4",
            "temperature": 0.1,
            "max_tokens": 4000,
            "system_message": """
            You are a pricing specialist for government contracting.
            Your expertise includes:
            - Government pricing regulations
            - Per-diem compliance
            - Cost calculation and validation
            - Competitive pricing analysis
            - Budget optimization
            
            Ensure all pricing is compliant and competitive.
            """
        },
        
        "proposal_writer": {
            "name": "ProposalWriter",
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 4000,
            "system_message": """
            You are a proposal writing specialist for government contracts.
            Your expertise includes:
            - Government proposal writing standards
            - Technical approach development
            - Executive summary creation
            - Past performance integration
            - Professional communication
            
            Write compelling, compliant proposals that win contracts.
            """
        },
        
        "quality_assurance": {
            "name": "QualityAssurance",
            "model": "gpt-4",
            "temperature": 0.1,
            "max_tokens": 4000,
            "system_message": """
            You are a quality assurance specialist for government proposals.
            Your expertise includes:
            - Proposal completeness review
            - Technical accuracy validation
            - Compliance verification
            - Quality standards assessment
            - Risk identification
            
            Ensure all deliverables meet the highest quality standards.
            """
        }
    }

def create_autogen_agents() -> Dict[str, autogen.AssistantAgent]:
    """Create AutoGen agents with proper configuration"""
    
    configs = get_agent_configs()
    agents = {}
    
    # LLM configuration
    llm_config = {
        "model": "gpt-4",
        "api_key": os.getenv("OPENAI_API_KEY"),
        "temperature": 0.1,
        "max_tokens": 4000
    }
    
    for agent_name, config in configs.items():
        agent = autogen.AssistantAgent(
            name=config["name"],
            system_message=config["system_message"],
            llm_config=llm_config
        )
        agents[agent_name] = agent
    
    return agents

def create_workflow_config() -> Dict[str, Any]:
    """Create workflow configuration for the AutoGen system"""
    
    return {
        "workflow_name": "ZgrBid_RFQ_Processing",
        "description": "Multi-agent RFQ analysis and proposal generation workflow",
        "steps": [
            {
                "step": 1,
                "agent": "document_processor",
                "task": "Process uploaded documents and extract content",
                "input": "raw_documents",
                "output": "processed_content"
            },
            {
                "step": 2,
                "agent": "requirements_extractor", 
                "task": "Extract requirements from RFQ documents",
                "input": "processed_content",
                "output": "structured_requirements"
            },
            {
                "step": 3,
                "agent": "compliance_analyst",
                "task": "Analyze compliance between requirements and capabilities",
                "input": "structured_requirements",
                "output": "compliance_matrix"
            },
            {
                "step": 4,
                "agent": "pricing_specialist",
                "task": "Calculate pricing and ensure compliance",
                "input": "compliance_matrix",
                "output": "pricing_analysis"
            },
            {
                "step": 5,
                "agent": "proposal_writer",
                "task": "Write proposal sections",
                "input": "pricing_analysis",
                "output": "proposal_draft"
            },
            {
                "step": 6,
                "agent": "quality_assurance",
                "task": "Review and validate final proposal",
                "input": "proposal_draft",
                "output": "final_proposal"
            }
        ],
        "error_handling": {
            "retry_attempts": 3,
            "fallback_agent": "quality_assurance",
            "escalation_threshold": 0.8
        },
        "output_format": {
            "type": "json",
            "schema": "zgrbid_proposal_schema"
        }
    }

def create_group_chat_config() -> Dict[str, Any]:
    """Create group chat configuration for collaborative work"""
    
    return {
        "group_chat_name": "ZgrBid_Proposal_Team",
        "description": "Collaborative proposal development team",
        "participants": [
            "DocumentProcessor",
            "RequirementsExtractor", 
            "ComplianceAnalyst",
            "PricingSpecialist",
            "ProposalWriter",
            "QualityAssurance"
        ],
        "workflow": {
            "mode": "collaborative",
            "max_rounds": 10,
            "termination_condition": "consensus_reached",
            "collaboration_rules": [
                "Each agent contributes their expertise",
                "Consensus required for major decisions",
                "QualityAssurance has final approval authority",
                "Escalate conflicts to QualityAssurance"
            ]
        },
        "communication": {
            "message_format": "structured",
            "include_context": True,
            "max_context_length": 8000
        }
    }

def create_autogen_config() -> Dict[str, Any]:
    """Create complete AutoGen configuration"""
    
    return {
        "version": "1.0.0",
        "project": "ZgrBid AutoGen System",
        "agents": get_agent_configs(),
        "workflow": create_workflow_config(),
        "group_chat": create_group_chat_config(),
        "llm_config": {
            "default_model": "gpt-4",
            "fallback_model": "gpt-3.5-turbo",
            "max_tokens": 4000,
            "temperature": 0.1
        },
        "logging": {
            "level": "INFO",
            "format": "detailed",
            "include_agent_communications": True
        },
        "monitoring": {
            "track_performance": True,
            "alert_thresholds": {
                "error_rate": 0.1,
                "response_time": 30.0,
                "quality_score": 0.8
            }
        }
    }

# Save configuration to file
def save_config(config: Dict[str, Any], filename: str = "autogen_config.json"):
    """Save AutoGen configuration to file"""
    
    with open(filename, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"Configuration saved to {filename}")

# Load configuration from file
def load_config(filename: str = "autogen_config.json") -> Dict[str, Any]:
    """Load AutoGen configuration from file"""
    
    with open(filename, 'r') as f:
        config = json.load(f)
    
    return config

if __name__ == "__main__":
    # Create and save configuration
    config = create_autogen_config()
    save_config(config)
    
    print("AutoGen configuration created successfully!")
    print(f"Agents configured: {len(config['agents'])}")
    print(f"Workflow steps: {len(config['workflow']['steps'])}")
    print(f"Group chat participants: {len(config['group_chat']['participants'])}")


