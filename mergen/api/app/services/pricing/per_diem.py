from typing import Dict, Any, List, Optional
from ..compliance.rules import get_per_diem_limit, check_per_diem_compliance
import logging

logger = logging.getLogger(__name__)


def check_per_diem_compliance(rate: float, location: str, month: str) -> Dict[str, Any]:
    """Check if rate complies with per-diem limits"""
    return check_per_diem_compliance(rate, location, month)


def get_per_diem_warnings(pricing_items: List[Dict[str, Any]], location: str = "orlando", month: str = "april") -> List[str]:
    """Get per-diem warnings for pricing items"""
    warnings = []
    limit = get_per_diem_limit(location, month)
    
    for item in pricing_items:
        if item.get("category") == "lodging" and item.get("unit_price", 0) > 0:
            compliance = check_per_diem_compliance(item["unit_price"], location, month)
            if not compliance["compliant"]:
                warnings.append(compliance["warning"])
    
    return warnings


def suggest_per_diem_alternatives(rate: float, location: str, month: str) -> List[str]:
    """Suggest alternatives for per-diem compliance"""
    limit = get_per_diem_limit(location, month)
    
    if rate <= limit:
        return ["Rate is compliant with per-diem limits"]
    
    suggestions = []
    excess = rate - limit
    
    suggestions.append(f"Current rate: ${rate:.2f}")
    suggestions.append(f"Per-diem limit: ${limit:.2f}")
    suggestions.append(f"Excess: ${excess:.2f}")
    suggestions.append("")
    suggestions.append("Alternatives:")
    suggestions.append(f"1. Reduce rate to ${limit:.2f} to meet per-diem limit")
    suggestions.append(f"2. Request per-diem waiver for ${excess:.2f} excess")
    suggestions.append("3. Split costs between multiple line items")
    suggestions.append("4. Negotiate with hotel for government rate")
    
    return suggestions


def calculate_per_diem_savings(rate: float, location: str, month: str) -> Dict[str, Any]:
    """Calculate potential savings from per-diem compliance"""
    limit = get_per_diem_limit(location, month)
    
    if rate <= limit:
        return {
            "compliant": True,
            "current_rate": rate,
            "limit": limit,
            "savings": 0.0,
            "savings_percentage": 0.0
        }
    
    excess = rate - limit
    savings_percentage = (excess / rate) * 100
    
    return {
        "compliant": False,
        "current_rate": rate,
        "limit": limit,
        "excess": excess,
        "savings": excess,
        "savings_percentage": savings_percentage
    }
