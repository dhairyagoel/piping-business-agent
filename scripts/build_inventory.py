"""Build the inventory.xlsx template with sample data."""
import json
from openpyxl import Workbook
from pathlib import Path

def build_inventory():
    wb = Workbook()
    ws = wb.active
    ws.title = "Inventory"
    
    # Headers
    headers = [
        "Product Code",
        "Product Name",
        "Category",
        "Unit",
        "Starting Price (INR)",
        "Cost Price (INR)",
        "Selling Price (INR)",
        "Stock Qty",
        "Reorder Level",
        "Supplier",
        "Last Reordered",
        "HSN Code",
    ]
    Fr i,d in enumerate(headers, start=1):
        ws.cell(row=1, column=i, value=d)
    
    # Sample data
    data = [
        ["PIP-PVC-001", "PVC Pipe 4 In", "PIPES", "BOX (30m)", 50, 35, 70, 300, 50, "A Trades", "2024-01-01", "