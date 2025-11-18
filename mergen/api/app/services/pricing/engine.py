from typing import List, Dict, Any
from ...models import PricingItem
from .per_diem import check_per_diem_compliance
import logging

logger = logging.getLogger(__name__)


def calculate_quote(pricing_items: List[PricingItem]) -> Dict[str, Any]:
    """Calculate pricing quote from pricing items"""
    logger.info(f"Calculating quote for {len(pricing_items)} items")
    
    # Calculate totals by category
    category_totals = {}
    total_cost = 0.0
    
    for item in pricing_items:
        # Calculate total price if not already calculated
        if item.total_price is None:
            item.total_price = item.qty * item.unit_price
        
        # Add to category total
        category = item.category or "other"
        if category not in category_totals:
            category_totals[category] = 0.0
        category_totals[category] += item.total_price
        
        # Add to total cost
        total_cost += item.total_price
    
    # Calculate taxes and fees (placeholder)
    tax_rate = 0.0  # TODO: Extract from RFQ or configuration
    tax_amount = total_cost * tax_rate
    
    # Calculate grand total
    grand_total = total_cost + tax_amount
    
    return {
        "items": [
            {
                "id": item.id,
                "name": item.name,
                "description": item.description,
                "qty": item.qty,
                "unit": item.unit,
                "unit_price": item.unit_price,
                "total_price": item.total_price,
                "category": item.category
            }
            for item in pricing_items
        ],
        "category_totals": category_totals,
        "subtotal": total_cost,
        "tax_rate": tax_rate,
        "tax_amount": tax_amount,
        "grand_total": grand_total,
        "item_count": len(pricing_items)
    }


def calculate_room_block_pricing(
    room_rate: float,
    check_in_date: str,
    check_out_date: str,
    room_count: int
) -> Dict[str, Any]:
    """Calculate pricing for room block"""
    # TODO: Implement date parsing and calculation
    # For now, assume 4 nights (14-18 April)
    nights = 4
    
    total_rooms = room_count * nights
    total_cost = total_rooms * room_rate
    
    return {
        "room_rate": room_rate,
        "nights": nights,
        "room_count": room_count,
        "total_rooms": total_rooms,
        "total_cost": total_cost,
        "per_diem_compliance": check_per_diem_compliance(room_rate, "orlando", "april")
    }


def calculate_av_pricing(
    av_packages: List[Dict[str, Any]],
    setup_days: int = 1
) -> Dict[str, Any]:
    """Calculate AV equipment pricing"""
    total_cost = 0.0
    package_details = []
    
    for package in av_packages:
        package_cost = package.get("rate", 0.0) * setup_days
        total_cost += package_cost
        
        package_details.append({
            "name": package.get("name", "Unknown Package"),
            "rate": package.get("rate", 0.0),
            "days": setup_days,
            "total": package_cost
        })
    
    return {
        "packages": package_details,
        "setup_days": setup_days,
        "total_cost": total_cost
    }


def calculate_food_beverage_pricing(
    meal_rates: Dict[str, float],
    participant_count: int,
    event_days: int
) -> Dict[str, Any]:
    """Calculate food and beverage pricing"""
    total_cost = 0.0
    meal_details = []
    
    # Common meal types
    meal_types = ["breakfast", "lunch", "dinner", "coffee_break"]
    
    for meal_type in meal_types:
        if meal_type in meal_rates:
            meal_cost = meal_rates[meal_type] * participant_count * event_days
            total_cost += meal_cost
            
            meal_details.append({
                "type": meal_type,
                "rate": meal_rates[meal_type],
                "participants": participant_count,
                "days": event_days,
                "total": meal_cost
            })
    
    return {
        "meals": meal_details,
        "participant_count": participant_count,
        "event_days": event_days,
        "total_cost": total_cost
    }


def generate_pricing_summary(quote: Dict[str, Any]) -> str:
    """Generate human-readable pricing summary"""
    summary_parts = []
    
    # Add category breakdown
    summary_parts.append("Pricing Summary:")
    summary_parts.append("=" * 50)
    
    for category, total in quote["category_totals"].items():
        summary_parts.append(f"{category.title()}: ${total:.2f}")
    
    summary_parts.append("-" * 50)
    summary_parts.append(f"Subtotal: ${quote['subtotal']:.2f}")
    
    if quote["tax_amount"] > 0:
        summary_parts.append(f"Tax ({quote['tax_rate']:.1%}): ${quote['tax_amount']:.2f}")
    
    summary_parts.append(f"Grand Total: ${quote['grand_total']:.2f}")
    
    return "\n".join(summary_parts)


def validate_pricing_quote(quote: Dict[str, Any]) -> List[str]:
    """Validate pricing quote for common issues"""
    warnings = []
    
    # Check for zero-cost items
    for item in quote["items"]:
        if item["total_price"] == 0:
            warnings.append(f"Item '{item['name']}' has zero cost")
    
    # Check for very high costs
    for item in quote["items"]:
        if item["total_price"] > 10000:  # Arbitrary threshold
            warnings.append(f"Item '{item['name']}' has unusually high cost: ${item['total_price']:.2f}")
    
    # Check for missing categories
    for item in quote["items"]:
        if not item["category"] or item["category"] == "other":
            warnings.append(f"Item '{item['name']}' has no category assigned")
    
    return warnings
