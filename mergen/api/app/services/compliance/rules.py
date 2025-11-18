from typing import Dict, List, Any
from dataclasses import dataclass

# Per-diem limits by location and month
PER_DIEM_LIMITS = {
    "orlando": {
        "april": 140.0,
        "may": 140.0,
        "june": 140.0,
        "july": 140.0,
        "august": 140.0,
        "september": 140.0,
        "october": 140.0,
        "november": 140.0,
        "december": 140.0,
        "january": 140.0,
        "february": 140.0,
        "march": 140.0
    },
    "miami": {
        "april": 150.0,
        "may": 150.0,
        "june": 150.0,
        "july": 150.0,
        "august": 150.0,
        "september": 150.0,
        "october": 150.0,
        "november": 150.0,
        "december": 150.0,
        "january": 150.0,
        "february": 150.0,
        "march": 150.0
    },
    "tampa": {
        "april": 130.0,
        "may": 130.0,
        "june": 130.0,
        "july": 130.0,
        "august": 130.0,
        "september": 130.0,
        "october": 130.0,
        "november": 130.0,
        "december": 130.0,
        "january": 130.0,
        "february": 130.0,
        "march": 130.0
    }
}

# Required facility features
REQUIRED_FACILITY_FEATURES = {
    "shuttle": {
        "description": "Airport shuttle service",
        "required": True,
        "alternatives": ["free_shuttle", "complimentary_shuttle"]
    },
    "wifi": {
        "description": "Wi-Fi internet access",
        "required": True,
        "alternatives": ["wireless_internet", "high_speed_internet"]
    },
    "parking": {
        "description": "Parking facilities",
        "required": True,
        "alternatives": ["valet_parking", "self_park"]
    },
    "breakout_rooms": {
        "description": "Breakout rooms for small group sessions",
        "required": True,
        "min_count": 2
    },
    "boardroom": {
        "description": "Boardroom for executive meetings",
        "required": True,
        "alternatives": ["executive_room"]
    }
}

# Distance requirements
DISTANCE_REQUIREMENTS = {
    "restaurant": {
        "max_distance": 0.2,  # miles
        "unit": "miles",
        "description": "Restaurant within 0.2 miles or free shuttle service"
    },
    "airport": {
        "max_distance": 10.0,  # miles
        "unit": "miles",
        "description": "Airport within 10 miles"
    }
}

# FAR clause requirements
FAR_CLAUSE_REQUIREMENTS = {
    "52.204-24": {
        "title": "Representation Regarding Certain Telecommunications and Video Surveillance Services or Equipment",
        "required": True,
        "description": "Contractor must represent whether it uses covered telecommunications equipment"
    },
    "52.204-25": {
        "title": "Prohibition on Contracting for Certain Telecommunications and Video Surveillance Services or Equipment",
        "required": True,
        "description": "Contractor must certify it does not use covered telecommunications equipment"
    },
    "52.204-26": {
        "title": "Covered Telecommunications Equipment or Services—Representation",
        "required": True,
        "description": "Contractor must represent regarding covered telecommunications equipment"
    }
}

# IPP billing requirements
IPP_BILLING_REQUIREMENTS = {
    "invoice_format": {
        "required": True,
        "description": "Invoices must be submitted through IPP system"
    },
    "required_fields": [
        "contract_number",
        "invoice_number",
        "invoice_date",
        "due_date",
        "amount",
        "description_of_services",
        "payment_terms"
    ],
    "supporting_documents": [
        "receipts",
        "timesheets",
        "expense_reports"
    ]
}

@dataclass
class ComplianceRule:
    """Represents a compliance rule"""
    rule_id: str
    category: str
    description: str
    required: bool
    severity: str  # low, medium, high, critical
    check_function: str  # Name of function to check this rule


def get_per_diem_limit(location: str, month: str) -> float:
    """Get per-diem limit for location and month"""
    location_lower = location.lower()
    month_lower = month.lower()
    
    if location_lower in PER_DIEM_LIMITS:
        if month_lower in PER_DIEM_LIMITS[location_lower]:
            return PER_DIEM_LIMITS[location_lower][month_lower]
    
    # Default to Orlando April rate if not found
    return PER_DIEM_LIMITS["orlando"]["april"]


def check_per_diem_compliance(rate: float, location: str, month: str) -> Dict[str, Any]:
    """Check if rate complies with per-diem limits"""
    limit = get_per_diem_limit(location, month)
    
    if rate <= limit:
        return {
            "compliant": True,
            "rate": rate,
            "limit": limit,
            "excess": 0.0,
            "warning": None
        }
    else:
        excess = rate - limit
        return {
            "compliant": False,
            "rate": rate,
            "limit": limit,
            "excess": excess,
            "warning": f"Rate ${rate:.2f} exceeds per-diem limit of ${limit:.2f} by ${excess:.2f}"
        }


def check_facility_compliance(features: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Check facility compliance against requirements"""
    compliance_results = {}
    
    for feature_name, requirements in REQUIRED_FACILITY_FEATURES.items():
        found = False
        matching_feature = None
        
        # Check if feature exists
        for feature in features:
            if feature["name"] == feature_name or feature["name"] in requirements.get("alternatives", []):
                found = True
                matching_feature = feature
                break
        
        compliance_results[feature_name] = {
            "required": requirements["required"],
            "found": found,
            "feature": matching_feature,
            "compliant": found if requirements["required"] else True
        }
    
    return compliance_results


def check_distance_compliance(distance_info: Dict[str, Any]) -> Dict[str, Any]:
    """Check distance compliance against requirements"""
    compliance_results = {}
    
    for distance_type, requirements in DISTANCE_REQUIREMENTS.items():
        distance_key = f"{distance_type}_distance"
        actual_distance = distance_info.get(distance_key)
        
        if actual_distance is not None:
            compliant = actual_distance <= requirements["max_distance"]
            compliance_results[distance_type] = {
                "required": True,
                "actual_distance": actual_distance,
                "max_distance": requirements["max_distance"],
                "unit": requirements["unit"],
                "compliant": compliant,
                "description": requirements["description"]
            }
        else:
            compliance_results[distance_type] = {
                "required": True,
                "actual_distance": None,
                "max_distance": requirements["max_distance"],
                "unit": requirements["unit"],
                "compliant": False,
                "description": requirements["description"],
                "warning": f"No distance information found for {distance_type}"
            }
    
    return compliance_results


def check_far_clause_compliance(clauses: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Check FAR clause compliance"""
    compliance_results = {}
    
    for clause_id, requirements in FAR_CLAUSE_REQUIREMENTS.items():
        found = False
        matching_clause = None
        
        # Check if clause exists
        for clause in clauses:
            if clause_id in clause.get("text", "") or clause_id in clause.get("tags", []):
                found = True
                matching_clause = clause
                break
        
        compliance_results[clause_id] = {
            "required": requirements["required"],
            "found": found,
            "clause": matching_clause,
            "compliant": found if requirements["required"] else True,
            "title": requirements["title"],
            "description": requirements["description"]
        }
    
    return compliance_results


def check_ipp_billing_compliance(billing_info: Dict[str, Any]) -> Dict[str, Any]:
    """Check IPP billing compliance"""
    compliance_results = {
        "invoice_format": {
            "required": IPP_BILLING_REQUIREMENTS["invoice_format"]["required"],
            "compliant": billing_info.get("uses_ipp", False),
            "description": IPP_BILLING_REQUIREMENTS["invoice_format"]["description"]
        },
        "required_fields": {
            "required": True,
            "missing_fields": [],
            "compliant": True
        },
        "supporting_documents": {
            "required": True,
            "missing_documents": [],
            "compliant": True
        }
    }
    
    # Check required fields
    required_fields = IPP_BILLING_REQUIREMENTS["required_fields"]
    provided_fields = billing_info.get("fields", [])
    missing_fields = [field for field in required_fields if field not in provided_fields]
    
    compliance_results["required_fields"]["missing_fields"] = missing_fields
    compliance_results["required_fields"]["compliant"] = len(missing_fields) == 0
    
    # Check supporting documents
    required_docs = IPP_BILLING_REQUIREMENTS["supporting_documents"]
    provided_docs = billing_info.get("documents", [])
    missing_docs = [doc for doc in required_docs if doc not in provided_docs]
    
    compliance_results["supporting_documents"]["missing_documents"] = missing_docs
    compliance_results["supporting_documents"]["compliant"] = len(missing_docs) == 0
    
    return compliance_results



