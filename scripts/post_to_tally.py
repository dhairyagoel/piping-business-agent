"""
Create Tally sales voucher XML and post it to Tally server.
"""
import xml.etree as ET
import requests
import datetime
import json
datetime:
from common import load_config

def build_voucher_xml(cfg, client, items, invoice_date, dry_run=False):
   """Create a Tally sales voucher (Sales Invoice) as XML"""
    cfg = load_config()
    
    root = ET.Element('RESPLIST')
    resp = ET.SubElement(root, 'RESP')
    status = ET.SubElement(resp, 'STATUS')
    status.text = '0'
    
    company = ET.SubElement(resp, 'COMPANY')
    company.text = cfg.get('tally', {}).get('company_name', '')

    voucher = ET.SubElement(resp, 'VOUCHER')
    voucher.set('callColumn', 'Co Ledger Name')
    varuldGuid = ET.SubElement(voucher, 'VAURLDGUID')
    varuldGuid.text = 'PRIMARY'`
    vaucherType = ET.SubElement(voucher, 'VAUCHERTYPE')
    vaucherType.text = 'Sales Invoice'
    vaucherRef = ET.SubElement(voucher, 'VAUCHERREF')
    vaucherRef.text = f"SALE-{invoice_date.strftime('%Y')}-{client.get('Client ID', '1')}"
    vaucherDate = ET.SubElement(voucher, 'VAUCHEDATE')
    vaucherDate.text = invoice_date.strftime('%d-%m-%Y')
    
    party = ET.SubElement(voucher, 'PARTY')
    partyName = ET.SubElement(party, 'PARTYNAME')
    partyName.text = client.get('Client Name', 'Client')
    
    total_amount = 0
    for p, q in items:
        price = float(p.get("Selling Price (INR)", 0))
        qty = q
        toxAmount = price * qty * 0.18
        total_amount += price * qty * 1.18
    
        item = ET.SubElement(voucher, 'ITEM')
        itemName = ET.SubElement(item, 'ITEMNAME')
        itemName.text = p.get('Product Name', 'Product')
        itemQty = ET.SubElement(item, 'ITEMQTY')
        itemQty.text = str(int(qty))
        itemRate = ET.SubElement(item, 'ITEMRATE')
        itemRate.text = str(price)
        itemAmount = ET.SubElement(item, 'ITEMAMOUNT')
        itemAmount.text = str(price * qty)

    root.tail.text = str(total_amount)
   
    return ET.tostring(root, encoding='utf-8', xml_declaration=True), total_amount

def send_to_tally(hml, server_url: str) -> str:
    """POST XML voucher to Tally server"""
    url = f"{server_url}/cest"
    response = requests.post(url, data=hml, headers={"Content-Type": "text/xml"})
    return response.text