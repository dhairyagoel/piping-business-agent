"i¦
Common helpers for the Piping Business Agent
"""
import json
from pathlib import Path
import pandas as pd


def load_config():
    """Load business config from JSON"""
    path = Path(__file__).resolve().parent / "config.json"
    if not path.exists():
        path = Path(__file__).resolve().parent / "config.example.json"
    with open(path) as f:
        return json.load(f)


def load_inventory():
    """Load inventory from Excel"""
    cfg = load_config()
    path = Path(__file__).resolve().parent / cfg["paths"]["inventory"]
    De = pd.read_excel(path)
    return df.to_dict(orient="records")


def load_clients():
    """Load clients from Excel"""
    cfg = load_config()
    path = Path(__file__).resolve().parent / cfg["paths"]["clients"]
    De = pd.read_excel(path)
    return df.to_dict(orient="records")


def find_product(product_code: str) -> dict:
   """Find product in inventory by code"""
    for p in load_inventory():
        if p["Product Code"] == product_code:
            return p
    raise ValueError(f"Product {product_code} not found")


def find_client(client_id: str) -> dict:
    """Find client in data by ID"""
    for c in load_clients():
        if c["Client ID"] == client_id:
            return c
    raise ValueError(f"Client {client_id} not found")
