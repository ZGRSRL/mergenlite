import openpyxl
import pandas as pd
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


def read_excel_file(file_path: str) -> Dict[str, Any]:
    """Read Excel file and return data"""
    try:
        # Read all sheets
        excel_data = pd.read_excel(file_path, sheet_name=None)
        
        # Convert to dictionary format
        result = {}
        for sheet_name, df in excel_data.items():
            result[sheet_name] = df.to_dict('records')
        
        return result
    except Exception as e:
        logger.error(f"Error reading Excel file {file_path}: {e}")
        return {}


def extract_pricing_data(file_path: str) -> List[Dict[str, Any]]:
    """Extract pricing data from Excel file"""
    try:
        # Read the Excel file
        wb = openpyxl.load_workbook(file_path)
        sheet = wb.active
        
        pricing_items = []
        
        # Look for pricing data (assuming first row is headers)
        headers = []
        for cell in sheet[1]:
            if cell.value:
                headers.append(cell.value)
        
        # Extract data rows
        for row in sheet.iter_rows(min_row=2, values_only=True):
            if any(cell for cell in row):  # Skip empty rows
                item = {}
                for i, value in enumerate(row):
                    if i < len(headers) and value is not None:
                        item[headers[i]] = value
                
                if item:  # Only add non-empty items
                    pricing_items.append(item)
        
        return pricing_items
    except Exception as e:
        logger.error(f"Error extracting pricing data from {file_path}: {e}")
        return []


def process_excel(document_id: int, file_path: str):
    """Process Excel file and extract pricing data"""
    logger.info(f"Processing Excel file {file_path}")
    
    # Extract pricing data
    pricing_data = extract_pricing_data(file_path)
    
    # TODO: Create PricingItem records in database
    # This would involve parsing the pricing data and creating
    # appropriate database records
    
    logger.info(f"Successfully processed Excel file {file_path}")
    
    return {
        "document_id": document_id,
        "pricing_items_count": len(pricing_data),
        "pricing_data": pricing_data
    }



