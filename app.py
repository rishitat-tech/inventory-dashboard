import os
import shutil
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

DATA_PATH = Path(os.getenv("INVENTORY_PATH", "data/inventory.xlsx"))
SEED_PATH = Path("data/inventory.xlsx")

if not DATA_PATH.exists() and SEED_PATH.exists():
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(SEED_PATH, DATA_PATH)

st.set_page_config(
    page_title="V2D Inventory & Orders",
    page_icon="📦",
    layout="wide"
)

ORDER_COLUMNS = [
    "Country",
    "Category",
    "Item Name",
    "Qty",
    "Status",
    "Source Link",
    "Priority",
    "Requested By",
    "Date Requested",
    "Notes"
]


def load_sheets():
    if not DATA_PATH.exists():
        st.error("Missing data/inventory.xlsx")
        st.stop()

    sheets = pd.read_excel(DATA_PATH, sheet_name=None)

    # Ensure To Order exists
    if "To Order" not in sheets:
        sheets["To Order"] = pd.DataFrame(columns=ORDER_COLUMNS)

    # Ensure To Order has expected columns
    to_order = sheets["To Order"].copy()
    for col in ORDER_COLUMNS:
        if col not in to_order.columns:
            to_order[col] = ""
    sheets["To Order"] = to_order[ORDER_COLUMNS]

    return sheets


def save_sheets(sheets):
    with pd.ExcelWriter(DATA_PATH, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)


def clean_name(col):
    return str(col).strip().lower()


def find_col(df, possible_names):
    possible = [p.lower() for p in possible_names]
    for col in df.columns:
        if clean_name(col) in possible:
            return col
    return None


def normalize_inventory_view(sheets):
    rows = []

    # US Inventory
    if "US Inventory" in sheets:
        df = sheets["US Inventory"].copy()
        category_col = find_col(df, ["category"])
        item_col = find_col(df, ["iteam", "item", "items", "item name"])
        model_col = find_col(df, ["model"])
        qty_col = find_col(df, ["qty", "quantity"])
        location_col = find_col(df, ["location"])
        notes_col = find_col(df, ["notes"])
        status_col = find_col(df, ["status"])

        for _, r in df.iterrows():
            rows.append({
                "Source Sheet": "US Inventory",
                "Country": "USA",
                "Category": r.get(category_col, "") if category_col else "",
                "Item Name": r.get(item_col, "") if item_col else "",
                "Model": r.get(model_col, "") if model_col else "",
                "Qty": r.get(qty_col, 1) if qty_col else 1,
                "Status": r.get(status_col, "On Hand") if status_col else "On Hand",
                "Location": r.get(location_col, "") if location_col else "",
                "Notes": r.get(notes_col, "") if notes_col else "",
            })

    # US Props
    if "US Props" in sheets:
        df = sheets["US Props"].copy()
        item_col = find_col(df, ["items", "item", "item name"])
        qty_col = find_col(df, ["quantity", "qty"])
        status_col = find_col(df, ["status"])

        for _, r in df.iterrows():
            rows.append({
                "Source Sheet": "US Props",
                "Country": "USA",
                "Category": "Prop",
                "Item Name": r.get(item_col, "") if item_col else "",
                "Model": "",
                "Qty": r.get(qty_col, 1) if qty_col else 1,
                "Status": r.get(status_col, "Arrived") if status_col else "Arrived",
                "Location": "Building K",
                "Notes": "",
            })

    # US Hardware
    if "US Hardware" in sheets:
        df = sheets["US Hardware"].copy()
        item_col = find_col(df, ["items", "item", "item name"])
        qty_col = find_col(df, ["quantity", "qty"])
        status_col = find_col(df, ["status"])

        for _, r in df.iterrows():
            rows.append({
                "Source Sheet": "US Hardware",
                "Country": "USA",
                "Category": "Hardware",
                "Item Name": r.get(item_col, "") if item_col else "",
                "Model": "",
                "Qty": r.get(qty_col, 1) if qty_col else 1,
                "Status": r.get(status_col, "Arrived") if status_col else "Arrived",
                "Location": "Building K",
                "Notes": "",
            })

    view = pd.DataFrame(rows)

    if not view.empty:
        view["Qty"] = pd.to_numeric(view["Qty"], errors="coerce").fillna(0)

    return view


def normalize_to_order_view(sheets):
    if "To Order" not in sheets:
        return pd.DataFrame(columns=ORDER_COLUMNS)

    df = sheets["To Order"].copy()

    if "Qty" in df.columns:
        df["Qty"] = pd.to_numeric(df["Qty"], errors="coerce").fillna(0)

    return df


def normalize_in_ph_view(sheets):
    if "IN & PH" not in sheets:
        return pd.DataFrame()

    df = sheets["IN & PH"].copy()

    for col in df.columns:
        if str(col).strip() in ["Total PH", "Total IN", "Total to Order"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df


if "sheets" not in st.session_state:
    st.session_state.sheets = load_sheets()

st.title("📦 V2D Inventory & Orders")

st.sidebar.header("Controls")

if st.sidebar.button("Reload"):
    st.session_state.sheets = load_sheets()
    st.sidebar.success("Reloaded from Excel")

if st.sidebar.button("Save Changes"):
    save_sheets(st.session_state.sheets)
    st.sidebar.success("Saved to data/inventory.xlsx")

st.sidebar.info("All table tabs are editable. Click Save Changes after updates.")

sheets = st.session_state.sheets

inventory_view = normalize_inventory_view(sheets)
to_order_view = normalize_to_order_view(sheets)
in_ph_view = normalize_in_ph_view(sheets)

tab_names = ["Dashboard"]

for name in ["US Inventory", "US Props", "US Hardware", "IN & PH", "To Order"]:
    if name in sheets:
        tab_names.append(name)

tabs = st.tabs(tab_names)

with tabs[0]:
    st.subheader("Dashboard")

    total_inventory_lines = len(inventory_view)
    total_inventory_qty = int(inventory_view["Qty"].sum()) if not inventory_view.empty else 0
    total_to_order_lines = len(to_order_view)
    total_to_order_qty = int(to_order_view["Qty"].sum()) if not to_order_view.empty and "Qty" in to_order_view.columns else 0
    in_ph_lines = len(in_ph_view)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Inventory Lines", total_inventory_lines)
    c2.metric("Inventory Qty", total_inventory_qty)
    c3.metric("To Order Lines", total_to_order_lines)
    c4.metric("To Order Qty", total_to_order_qty)
    c5.metric("IN & PH Lines", in_ph_lines)

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Inventory by Category")
        if not inventory_view.empty:
            chart = (
                inventory_view.groupby("Category", dropna=False)["Qty"]
                .sum()
                .reset_index()
                .sort_values("Qty", ascending=True)
            )
            fig = px.bar(chart, x="Qty", y="Category", orientation="h")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No inventory data found.")

    with col2:
        st.subheader("Inventory by Status")
        if not inventory_view.empty and "Status" in inventory_view.columns:
            chart = (
                inventory_view.groupby("Status", dropna=False)
                .size()
                .reset_index(name="Count")
            )
            fig = px.pie(chart, names="Status", values="Count")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No status data found.")

    col3, col4 = st.columns(2)

    with col3:
        st.subheader("To Order by Country")
        if not to_order_view.empty and "Country" in to_order_view.columns and "Qty" in to_order_view.columns:
            chart = (
                to_order_view.groupby("Country", dropna=False)["Qty"]
                .sum()
                .reset_index()
            )
            fig = px.pie(chart, names="Country", values="Qty")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No To Order rows yet.")

    with col4:
        st.subheader("IN & PH Status")
        if not in_ph_view.empty:
            status_col = find_col(in_ph_view, ["item status", "status"])
            if status_col:
                chart = (
                    in_ph_view.groupby(status_col, dropna=False)
                    .size()
                    .reset_index(name="Count")
                )
                fig = px.pie(chart, names=status_col, values="Count")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No status column found.")
        else:
            st.info("No IN & PH data found.")

    st.divider()

    st.subheader("Action Items")

    action_parts = []

    if not to_order_view.empty:
        action_parts.append(to_order_view)

    if not in_ph_view.empty:
        status_col = find_col(in_ph_view, ["item status", "status"])
        if status_col:
            hw_action = in_ph_view[
                ~in_ph_view[status_col].astype(str).str.lower().isin(
                    ["arrived", "received", "available", "on hand"]
                )
            ].copy()
            if not hw_action.empty:
                hw_action["Source"] = "IN & PH"
                action_parts.append(hw_action)

    if action_parts:
        action_df = pd.concat(action_parts, ignore_index=True, sort=False)
        st.dataframe(action_df, use_container_width=True)
    else:
        st.success("No action items.")

# Editable sheet tabs
for i, sheet_name in enumerate(tab_names[1:], start=1):
    with tabs[i]:
        st.subheader(sheet_name)

        st.session_state.sheets[sheet_name] = st.data_editor(
            st.session_state.sheets[sheet_name],
            use_container_width=True,
            num_rows="dynamic",
            key=f"editor_{sheet_name}"
        )

        st.info("Click Save Changes in the sidebar after updating.")
