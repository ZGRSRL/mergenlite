"""
SOW Template Engine
Renders SOW HTML from SOWDataModel using Jinja2 templates.
"""
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader, Template

logger = logging.getLogger(__name__)

try:
    from jinja2 import Environment, FileSystemLoader
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
    logger.warning("jinja2 not available, template engine will be limited")


def get_sow_html_template() -> str:
    """Get default SOW HTML template."""
    return """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Statement of Work - {{ data_model.event_name }}</title>
    <style>
        @page {
            margin: 1in;
            @bottom-center {
                content: "Page " counter(page) " of " counter(pages);
                font-size: 11px;
                color: #003366;
            }
        }
        body {
            font-family: Helvetica, Arial, sans-serif;
            font-size: 12px;
            color: #333333;
            line-height: 1.45;
            margin: 0;
            padding: 0;
        }
        .header {
            display: flex;
            justify-content: space-between;
            border-bottom: 1px solid #d7dce2;
            padding-bottom: 8px;
            margin-bottom: 24px;
        }
        .header-left {
            font-size: 14px;
            font-weight: bold;
            color: #003366;
        }
        .header-right {
            font-size: 14px;
            font-weight: bold;
            color: #003366;
            text-align: right;
        }
        .section-box {
            border-left: 4px solid #003366;
            background: #f9fbfd;
            padding: 12px 18px;
            margin: 24px 0 12px;
        }
        .section-box h2 {
            margin: 0;
            color: #003366;
            font-size: 16px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 24px;
            font-size: 12px;
        }
        th {
            background: #003366;
            color: white;
            padding: 8px 10px;
            font-weight: 600;
            text-align: left;
        }
        td {
            padding: 8px 10px;
            border: 1px solid #d7dce2;
        }
        tr:nth-child(even) {
            background: #eef3f8;
        }
        .layout-box {
            border: 1px solid #d7dce2;
            background: #f5f9fd;
            padding: 16px;
            margin-bottom: 20px;
            box-shadow: 0px 2px 4px rgba(0,0,0,0.05);
        }
        .layout-box h3 {
            margin-top: 0;
            color: #003366;
        }
        p {
            font-size: 12px;
            line-height: 1.45;
            color: #333333;
            margin: 8px 0;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-left">{{ data_model.event_name }}</div>
        <div class="header-right">{{ data_model.solicitation_number }}</div>
    </div>

    <h1 style="text-align: center; color: #003366; font-size: 20px;">Statement of Work (SOW)</h1>

    <!-- APPENDIX A - Event Summary -->
    <div class="section-box">
        <h2>APPENDIX A - EVENT SUMMARY</h2>
    </div>
    <table>
        <tr>
            <th style="width: 30%;">Field</th>
            <th>Value</th>
        </tr>
        <tr>
            <td><strong>Event Name</strong></td>
            <td>{{ data_model.event_name }}</td>
        </tr>
        <tr>
            <td><strong>Agency</strong></td>
            <td>{{ data_model.agency }}</td>
        </tr>
        <tr>
            <td><strong>Solicitation Number</strong></td>
            <td>{{ data_model.solicitation_number }}</td>
        </tr>
        <tr>
            <td><strong>Start Date</strong></td>
            <td>{{ data_model.dates.get('start', 'TBD') }}</td>
        </tr>
        <tr>
            <td><strong>End Date</strong></td>
            <td>{{ data_model.dates.get('end', 'TBD') }}</td>
        </tr>
        <tr>
            <td><strong>Location</strong></td>
            <td>{{ data_model.location }}</td>
        </tr>
    </table>

    <!-- Sleeping Room Requirements -->
    {% if data_model.sleeping_rooms %}
    <div class="section-box">
        <h2>Sleeping Room Requirements</h2>
    </div>
    <table>
        <thead>
            <tr>
                <th>Day</th>
                <th>Date</th>
                <th>Rooms Per Night</th>
            </tr>
        </thead>
        <tbody>
            {% for room in data_model.sleeping_rooms %}
            <tr>
                <td>{{ room.get('day', 'TBD') }}</td>
                <td>{{ room.get('date', 'TBD') }}</td>
                <td>{{ room.get('rooms_per_night', 'TBD') }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% endif %}

    <!-- Function Space Requirements -->
    {% if data_model.function_space_calendar %}
    <div class="section-box">
        <h2>Function Space Requirements</h2>
    </div>
    <table>
        <thead>
            <tr>
                <th>Day</th>
                <th>Date</th>
                <th>Room Type</th>
                <th>Capacity</th>
                <th>Setup</th>
            </tr>
        </thead>
        <tbody>
            {% for day in data_model.function_space_calendar %}
                {% for room in day.rooms %}
                <tr>
                    <td>{{ day.day }}</td>
                    <td>{{ day.date }}</td>
                    <td>{{ room.get('room_type', 'TBD') }}</td>
                    <td>{{ room.get('capacity', 'TBD') }}</td>
                    <td>{{ room.get('setup', 'TBD') }}</td>
                </tr>
                {% endfor %}
            {% endfor %}
        </tbody>
    </table>
    {% endif %}

    <!-- Meeting Room Setup -->
    {% if data_model.meeting_rooms %}
    <div class="section-box">
        <h2>Meeting Room Setup</h2>
    </div>
    <table>
        <thead>
            <tr>
                <th>Room</th>
                <th>Setup</th>
                <th>Capacity</th>
                <th>24-Hour Hold</th>
                <th>Notes</th>
            </tr>
        </thead>
        <tbody>
            {% for room in data_model.meeting_rooms %}
            <tr>
                <td>{{ room.get('name', room.get('room_name', 'TBD')) }}</td>
                <td>{{ room.get('setup', 'TBD') }}</td>
                <td>{{ room.get('capacity', 'TBD') }}</td>
                <td>{{ 'Yes' if room.get('hold_24h') else 'No' }}</td>
                <td>{{ room.get('notes', '-') }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% endif %}

    <!-- General Session Seating Layout -->
    {% if data_model.seating_layout %}
    <div class="layout-box">
        <h3>General Session Seating & Layout</h3>
        <ul>
            {% if data_model.seating_layout.hollow_square %}
            <li>Hollow Square — {{ data_model.seating_layout.hollow_square.capacity_min }}-{{ data_model.seating_layout.hollow_square.capacity_max }} participants</li>
            {% endif %}
            {% if data_model.seating_layout.classroom %}
                {% for classroom in data_model.seating_layout.classroom %}
                <li>Classroom — {{ classroom.location }}, {{ classroom.capacity }} participants</li>
                {% endfor %}
            {% endif %}
            {% if data_model.seating_layout.theater %}
            <li>Theater — Approx. {{ data_model.seating_layout.theater.capacity }} participants</li>
            {% endif %}
            {% if data_model.seating_layout.special_areas %}
                {% for area in data_model.seating_layout.special_areas %}
                <li>{{ area.name }} — {{ area.location }}</li>
                {% endfor %}
            {% endif %}
        </ul>
    </div>
    {% endif %}

    <!-- Daily AV Requirements -->
    {% if data_model.av_requirements %}
    <div class="section-box">
        <h2>Daily AV Requirements</h2>
    </div>
    <table>
        <thead>
            <tr>
                <th>Day</th>
                <th>Date</th>
                <th>Room</th>
                <th>AV Equipment</th>
                <th>Special Notes</th>
            </tr>
        </thead>
        <tbody>
            {% for av in data_model.av_requirements %}
            <tr>
                <td>{{ av.get('day', 'TBD') }}</td>
                <td>{{ av.get('date', 'TBD') }}</td>
                <td>{{ av.get('room_name', 'TBD') }}</td>
                <td>{{ av.get('av_needs', av.get('equipment', 'TBD')) }}</td>
                <td>{{ av.get('special_notes', '-') }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% endif %}

    <!-- Food & Beverage Requirements -->
    {% if data_model.food_beverage %}
    <div class="section-box">
        <h2>Food & Beverage and Refreshments</h2>
    </div>
    <table>
        <thead>
            <tr>
                <th>Day</th>
                <th>Date</th>
                <th>Time</th>
                <th>Headcount</th>
                <th>Menu/Items</th>
            </tr>
        </thead>
        <tbody>
            {% for fb in data_model.food_beverage %}
            <tr>
                <td>{{ fb.get('day', 'TBD') }}</td>
                <td>{{ fb.get('date', 'TBD') }}</td>
                <td>{{ fb.get('time', 'TBD') }}</td>
                <td>{{ fb.get('headcount', 'TBD') }}</td>
                <td>{{ fb.get('menu', fb.get('items', 'TBD')) }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% endif %}

    <!-- Commercial Terms -->
    {% if data_model.commercial_terms %}
    <div class="section-box">
        <h2>Commercial Terms & Special Conditions</h2>
    </div>
    <table>
        <tr>
            <th style="width: 30%;">Term</th>
            <th>Value</th>
        </tr>
        {% for key, value in data_model.commercial_terms.items() %}
        <tr>
            <td><strong>{{ key.replace('_', ' ').title() }}</strong></td>
            <td>{{ value if value is not none else 'TBD' }}</td>
        </tr>
        {% endfor %}
    </table>
    {% endif %}

    <!-- Compliance Requirements -->
    {% if data_model.compliance_clauses %}
    <div class="section-box">
        <h2>Compliance Requirements</h2>
    </div>
    {% if data_model.compliance_clauses.get('far_clauses') %}
    <p><strong>FAR Clauses:</strong></p>
    <ul>
        {% for clause in data_model.compliance_clauses.far_clauses %}
        <li>{{ clause.get('number', '') }}: {{ clause.get('title', '') }}</li>
        {% endfor %}
    </ul>
    {% endif %}
    {% if data_model.compliance_clauses.get('edar_clauses') %}
    <p><strong>EDAR Clauses:</strong></p>
    <ul>
        {% for clause in data_model.compliance_clauses.edar_clauses %}
        <li>{{ clause.get('number', '') }}: {{ clause.get('title', '') }}</li>
        {% endfor %}
    </ul>
    {% endif %}
    {% endif %}
</body>
</html>"""


def render_sow_from_model(data_model: Any) -> str:
    """
    Render SOW HTML from SOWDataModel.
    
    Args:
        data_model: SOWDataModel instance or dict
        
    Returns:
        HTML string
    """
    try:
        template_str = get_sow_html_template()
        
        if JINJA2_AVAILABLE:
            template = Template(template_str)
        else:
            # Fallback: simple string replacement
            logger.warning("jinja2 not available, using simple string template")
            if hasattr(data_model, 'event_name'):
                return template_str.replace("{{ data_model.event_name }}", data_model.event_name)
            elif isinstance(data_model, dict):
                return template_str.replace("{{ data_model.event_name }}", data_model.get("event_name", "TBD"))
            else:
                return template_str
        
        # Convert data_model to dict if needed
        if hasattr(data_model, 'to_dict'):
            data_dict = data_model.to_dict()
        elif isinstance(data_model, dict):
            data_dict = data_model
        else:
            # Try to convert to dict
            data_dict = {
                "event_name": getattr(data_model, 'event_name', 'TBD'),
                "agency": getattr(data_model, 'agency', 'TBD'),
                "solicitation_number": getattr(data_model, 'solicitation_number', 'TBD'),
                "dates": getattr(data_model, 'dates', {}),
                "location": getattr(data_model, 'location', 'TBD'),
                "sleeping_rooms": getattr(data_model, 'sleeping_rooms', []),
                "function_space_calendar": getattr(data_model, 'function_space_calendar', []),
                "meeting_rooms": getattr(data_model, 'meeting_rooms', []),
                "av_requirements": getattr(data_model, 'av_requirements', []),
                "food_beverage": getattr(data_model, 'food_beverage', []),
                "commercial_terms": getattr(data_model, 'commercial_terms', {}),
                "compliance_clauses": getattr(data_model, 'compliance_clauses', {}),
                "seating_layout": getattr(data_model, 'seating_layout', None),
            }
        
        html = template.render(data_model=data_dict)
        logger.info("SOW HTML rendered successfully")
        return html
        
    except Exception as e:
        logger.error(f"Error rendering SOW HTML: {e}", exc_info=True)
        raise

