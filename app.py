"""
Piping Business Agent — Web Dashboard
Run locally:    streamlit run app.py
Cloud:          Deploy to Streamlit Community Cloud (free)
"""
import streamlit as st
import pandas as pd
import tempfile
import io
from pathlib import Path
from datetime import date, datetime, timedelta
import json, sys, os

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT / "scripts"))

from common import load_config, load_inventory, load_clients, find_product, find_client

# ───────────────────── CONFIG ─────────────────────
cfg = load_config()
BIZ = cfg["business"]

st.set_page_config(
    page_title=f"{BIZ['name']} — Agent",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ───────────────────── SIDEBAR ─────────────────────
st.sidebar.title("🔧 " + BIZ["name"])
st.sidebar.caption(BIZ["tagline"])
page = st.sidebar.radio(
    "Navigate",
    ["📊 Dashboard", "📄 Generate Proposal", "🧾 Bill to Tally",
     "🚚 Delivery Challan", "📲 WhatsApp Reminders",
     "📦 Inventory", "👥 Clients"],
)

# ───────────────────── HELPERS ─────────────────────
def _parse_date(v):
    if v is None or str(v).strip() == "":
        return None
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(str(v).strip(), fmt).date()
        except ValueError:
            continue
    return None


def client_options():
    return {f"{c['Client ID']} — {c['Client Name']}": c for c in load_clients()}


def product_options():
    return {f"{p['Product Code']} — {p['Product Name']}": p for p in load_inventory()}


def product_rows_ui(key_prefix, session_key):
    """Reusable product row selector. Returns list of (product_dict, qty)."""
    popts = product_options()
    pkeys = list(popts.keys())
    if session_key not in st.session_state:
        st.session_state[session_key] = [{"product": pkeys[0], "qty": 1}]

    rows_to_delete = []
    for i, row in enumerate(st.session_state[session_key]):
        c1, c2, c3 = st.columns([5, 2, 1])
        cur_idx = pkeys.index(row["product"]) if row["product"] in pkeys else 0
        row["product"] = c1.selectbox("Product", pkeys, index=cur_idx, key=f"{key_prefix}_prod_{i}")
        row["qty"] = c2.number_input("Qty", min_value=1, value=row["qty"], key=f"{key_prefix}_qty_{i}")
        if c3.button("❌", key=f"{key_prefix}_del_{i}"):
            rows_to_delete.append(i)

    for idx in sorted(rows_to_delete, reverse=True):
        st.session_state[session_key].pop(idx)
    if rows_to_delete:
        st.rerun()

    if st.button("➕ Add another product", key=f"{key_prefix}_add"):
        st.session_state[session_key].append({"product": pkeys[0], "qty": 1})
        st.rerun()

    return [(popts[r["product"]], r["qty"]) for r in st.session_state[session_key]]


def show_total_preview(items):
    subtotal = sum(float(p.get("Selling Price (INR)") or 0) * q for p, q in items)
    gst = subtotal * 0.18
    st.info(f"**Subtotal:** ₹{subtotal:,.0f}  |  **GST 18%:** ₹{gst:,.0f}  |  **Grand Total:** ₹{subtotal + gst:,.0f}")
    return subtotal


# ───────────────────── PAGE: DASHBOARD ─────────────────────
if page == "📊 Dashboard":
    st.title("📊 Business Dashboard")
    inv = load_inventory()
    clients = load_clients()

    total_stock_value = sum(
        float(p.get("Stock Qty") or 0) * float(p.get("Cost Price (INR)") or 0)
        for p in inv
    )
    low_stock_count = sum(
        1 for p in inv
        if float(p.get("Stock Qty") or 0) <= float(p.get("Reorder Level") or 0)
    )
    total_outstanding = sum(float(c.get("Outstanding (INR)") or 0) for c in clients)
    overdue_count = sum(
        1 for c in clients
        if str(c.get("Payment Status", "")).lower() == "overdue"
    )

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Products", len(inv))
    k2.metric("Low Stock Items", low_stock_count,
              delta_color="inverse" if low_stock_count > 0 else "normal")
    k3.metric("Stock Value", f"₹{total_stock_value:,.0f}")
    k4.metric("Total Outstanding", f"₹{total_outstanding:,.0f}")

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("⚠️ Low Stock Alert")
        low = [p for p in inv if float(p.get("Stock Qty") or 0) <= float(p.get("Reorder Level") or 0)]
        if low:
            st.dataframe(
                pd.DataFrame(low)[["Product Code", "Product Name", "Stock Qty", "Reorder Level", "Supplier"]],
                use_container_width=True, hide_index=True,
            )
        else:
            st.success("All products above reorder level!")

    with col2:
        st.subheader("💰 Overdue / Due Payments")
        overdue = [
            c for c in clients
            if str(c.get("Payment Status", "")).lower() in ("overdue", "due")
            and float(c.get("Outstanding (INR)") or 0) > 0
        ]
        if overdue:
            st.dataframe(
                pd.DataFrame(overdue)[["Client ID", "Client Name", "Outstanding (INR)", "Payment Status", "Last Invoice Due Date"]],
                use_container_width=True, hide_index=True,
            )
        else:
            st.success("No overdue payments!")

    st.divider()
    st.subheader("📁 Recent Files")
    out_dir = ROOT / "proposals_out"
    out_dir.mkdir(exist_ok=True)
    files = sorted(out_dir.glob("*"), key=lambda f: f.stat().st_mtime, reverse=True)[:10]
    if files:
        for f in files:
            col_a, col_b, col_c = st.columns([4, 2, 2])
            col_a.text(f.name)
            col_b.text(f"{f.stat().st_size / 1024:.1f} KB")
            with open(f, "rb") as fp:
                col_c.download_button("⬇ Download", fp.read(), file_name=f.name, key=f"dl_{f.name}")
    else:
        st.info("No files yet. Generate proposals or challans from the sidebar.")


# ───────────────────── PAGE: GENERATE PROPOSAL ─────────────────────
elif page == "📄 Generate Proposal":
    st.title("📄 Generate Proposal")
    st.write("Select a client, add products, click **Generate** — done.")

    copts = client_options()
    selected_client = st.selectbox("Select Client", list(copts.keys()))
    client = copts[selected_client]

    st.subheader("Products")
    items = product_rows_ui("prop", "proposal_rows")
    st.divider()
    show_total_preview(items)

    if st.button("🚀 Generate Proposal", type="primary"):
        with st.spinner("Generating proposal..."):
            from generate_proposal import build_proposal
            safe = "".join(ch for ch in client["Client Name"] if ch.isalnum() or ch in " _-").replace(" ", "_")
            out_path = ROOT / "proposals_out" / f"Proposal_{safe}_{date.today()}.pptx"
            out_path.parent.mkdir(exist_ok=True)
            build_proposal(client, items, cfg, out_path)

        st.success("Proposal ready!")
        with open(out_path, "rb") as fp:
            st.download_button(
                "📥 Download Proposal (.pptx)", fp.read(),
                file_name=out_path.name,
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            )


# ───────────────────── PAGE: BILL TO TALLY ─────────────────────
elif page == "🧾 Bill to Tally":
    st.title("🧾 Bill to Tally")
    st.write("Create a Sales Voucher and post it to Tally, or download the XML to import manually.")

    copts = client_options()
    selected_client = st.selectbox("Select Client", list(copts.keys()))
    client = copts[selected_client]

    st.subheader("Invoice Items")
    items = product_rows_ui("tally", "tally_rows")
    st.divider()
    show_total_preview(items)

    col1, col2, col3 = st.columns(3)

    if col1.button("👁️ Preview XML"):
        from post_to_tally import build_voucher_xml
        xml, total = build_voucher_xml(cfg, client, items, date.today())
        st.info(f"Invoice total (incl. GST): ₹{total:,.2f}")
        st.code(xml, language="xml")

    if col2.button("📥 Download XML"):
        from post_to_tally import build_voucher_xml
        xml, total = build_voucher_xml(cfg, client, items, date.today())
        st.download_button(
            "⬇ Save XML file", xml.encode("utf-8"),
            file_name=f"voucher_{client['Client ID']}_{date.today()}.xml",
            mime="application/xml",
        )

    if col3.button("📤 Post to Tally (local)", type="primary"):
        from post_to_tally import build_voucher_xml, send_to_tally
        xml, total = build_voucher_xml(cfg, client, items, date.today())
        url = cfg.get("tally", {}).get("url", "http://localhost:9000")
        try:
            resp = send_to_tally(xml, url)
            if "<LINEERROR>" in resp or "<EXCEPTION>" in resp:
                st.error(f"Tally errors found. Check ledger names.\n\n{resp}")
            else:
                st.success(f"Posted to Tally! Total: ₹{total:,.2f}")
        except Exception as e:
            st.error(
                f"Cannot reach Tally at {url}.\n\n"
                f"**Fix:** Open Tally on your PC with XML server on port 9000. "
                f"If you're using the cloud version, download the XML and import it manually.\n\n"
                f"Error: {e}"
            )


# ───────────────────── PAGE: DELIVERY CHALLAN ─────────────────────
elif page == "🚚 Delivery Challan":
    st.title("🚚 Delivery Challan")
    st.write("Generate a PDF challan — stock is automatically deducted.")

    copts = client_options()
    selected_client = st.selectbox("Select Client", list(copts.keys()))
    client = copts[selected_client]

    st.subheader("Items to Dispatch")
    items = product_rows_ui("chal", "challan_rows")

    st.divider()
    st.subheader("Transport Details")
    tc1, tc2 = st.columns(2)
    vehicle = tc1.text_input("Vehicle Number", placeholder="GJ01AB1234")
    driver = tc2.text_input("Driver & Phone", placeholder="Ramu +919812345678")
    po_ref = st.text_input("Client PO / Ref (optional)", placeholder="PO-2026-SHB-042")

    if st.button("🚀 Generate Challan & Deduct Stock", type="primary"):
        with st.spinner("Generating challan..."):
            from delivery_challan import build_challan, _deduct_stock
            challan_no = f"DC/{date.today().strftime('%Y%m%d')}/{client['Client ID']}"
            safe = "".join(ch for ch in client["Client Name"] if ch.isalnum()) or "Client"
            out_path = ROOT / "proposals_out" / f"Challan_{safe}_{date.today()}.pdf"
            out_path.parent.mkdir(exist_ok=True)
            build_challan(cfg, client, items, challan_no, date.today(),
                          vehicle, driver, po_ref, out_path)
            try:
                _deduct_stock(cfg, items)
                stock_msg = "Stock deducted from inventory."
            except Exception as e:
                stock_msg = f"Note: stock deduction skipped ({e})"

        st.success(f"Challan **{challan_no}** generated! {stock_msg}")
        with open(out_path, "rb") as fp:
            st.download_button("📥 Download Challan (.pdf)", fp.read(),
                               file_name=out_path.name, mime="application/pdf")


# ───────────────────── PAGE: WHATSAPP REMINDERS ─────────────────────
elif page == "📲 WhatsApp Reminders":
    st.title("📲 WhatsApp Reminders")
    st.write("See who would get a reminder. Once Twilio is configured, you can send them live.")

    today = date.today()
    tab1, tab2, tab3 = st.tabs(["💰 Payments", "📦 Low Stock", "📋 Proposal Follow-up"])

    with tab1:
        st.subheader("Due / Overdue Payments")
        due_list = []
        for c in load_clients():
            outstanding = float(c.get("Outstanding (INR)") or 0)
            status = str(c.get("Payment Status", "")).strip().lower()
            due = _parse_date(c.get("Last Invoice Due Date"))
            if outstanding <= 0 or status == "paid" or not due:
                continue
            days = (today - due).days
            if days < -2:
                continue
            due_list.append({
                "Client": c["Client Name"],
                "Phone": c.get("Phone (with country code)", ""),
                "Outstanding": f"₹{outstanding:,.0f}",
                "Due Date": str(due),
                "Status": "Overdue" if days > 0 else "Due soon",
                "Days": days,
            })
        if due_list:
            st.dataframe(pd.DataFrame(due_list), use_container_width=True, hide_index=True)
            st.info(f"{len(due_list)} client(s) would receive a payment reminder.")
        else:
            st.success("No overdue payments!")

    with tab2:
        st.subheader("Low Stock Items")
        low = []
        for p in load_inventory():
            stock = float(p.get("Stock Qty") or 0)
            reorder = float(p.get("Reorder Level") or 0)
            if stock <= reorder:
                low.append({
                    "Code": p["Product Code"],
                    "Product": p["Product Name"],
                    "Stock Left": int(stock),
                    "Reorder At": int(reorder),
                    "Supplier": p.get("Supplier", ""),
                })
        if low:
            st.dataframe(pd.DataFrame(low), use_container_width=True, hide_index=True)
            st.warning(f"{len(low)} item(s) need reordering. You'd get a WhatsApp alert.")
        else:
            st.success("All stock levels are healthy!")

    with tab3:
        st.subheader("Proposals Awaiting Response")
        pending = []
        for c in load_clients():
            sent = _parse_date(c.get("Last Proposal Sent"))
            if not sent:
                continue
            days = (today - sent).days
            if 3 <= days <= 21:
                pending.append({
                    "Client": c["Client Name"],
                    "Phone": c.get("Phone (with country code)", ""),
                    "Sent On": str(sent),
                    "Days Ago": days,
                })
        if pending:
            st.dataframe(pd.DataFrame(pending), use_container_width=True, hide_index=True)
            st.info(f"{len(pending)} client(s) would get a follow-up.")
        else:
            st.success("No pending follow-ups!")


# ───────────────────── PAGE: INVENTORY ─────────────────────
elif page == "📦 Inventory":
    st.title("📦 Inventory")
    df = pd.DataFrame(load_inventory())
    if not df.empty:
        fc1, fc2 = st.columns(2)
        cats = ["All"] + sorted(df["Category"].dropna().unique().tolist())
        sel_cat = fc1.selectbox("Category", cats)
        search = fc2.text_input("Search", "")

        filtered = df.copy()
        if sel_cat != "All":
            filtered = filtered[filtered["Category"] == sel_cat]
        if search:
            mask = (
                filtered["Product Name"].str.contains(search, case=False, na=False) |
                filtered["Product Code"].str.contains(search, case=False, na=False)
            )
            filtered = filtered[mask]

        st.dataframe(filtered, use_container_width=True, hide_index=True)
        st.caption(f"Showing {len(filtered)} of {len(df)} products")
    else:
        st.warning("No inventory data.")


# ───────────────────── PAGE: CLIENTS ─────────────────────
elif page == "👥 Clients":
    st.title("👥 Clients")
    df = pd.DataFrame(load_clients())
    if not df.empty:
        search = st.text_input("Search name, company, or city", "")
        filtered = df.copy()
        if search:
            searchable = ["Client Name", "Company", "City"]
            mask = pd.Series(False, index=filtered.index)
            for col in searchable:
                if col in filtered.columns:
                    mask = mask | filtered[col].astype(str).str.contains(search, case=False, na=False)
            filtered = filtered[mask]
        st.dataframe(filtered, use_container_width=True, hide_index=True)
        st.caption(f"Showing {len(filtered)} of {len(df)} clients")
    else:
        st.warning("No client data.")


# ───────────────────── FOOTER ─────────────────────
st.sidebar.divider()
st.sidebar.caption(f"v1.0 — {BIZ['name']}")
st.sidebar.caption(f"📞 {BIZ['phone']}")
"""
Piping Business Agent — Web Dashboard
Run locally:    streamlit run app.py
Cloud:          Deploy to Streamlit Community Cloud (free)
"""
import streamlit as st
import pandas as pd
import tempfile
import io
from pathlib import Path
from datetime import date, datetime, timedelta
import json, sys, os
