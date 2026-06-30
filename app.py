import os
from dotenv import load_dotenv
import pandas as pd
import streamlit as st
import plotly.express as px
from supabase import create_client

load_dotenv()

st.set_page_config(
    page_title="V2D Inventory & Orders",
    page_icon="📦",
    layout="wide"
)

def get_secret(name):
    value = os.getenv(name)
    if value:
        return value
    try:
        return st.secrets.get(name)
    except Exception:
        return None

SUPABASE_URL = get_secret("SUPABASE_URL")
SUPABASE_SERVICE_KEY = get_secret("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    st.error("Missing Supabase credentials.")
    st.stop()

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

INVENTORY_COLUMNS = [
    "id",
    "country",
    "location",
    "item_group",
    "category",
    "item_name",
    "model",
    "qty",
    "status",
    "owner",
    "asset_id",
    "serial_number",
    "condition",
    "storage_bin",
    "last_seen",
    "notes",
    "source_sheet"
]

ORDER_COLUMNS = [
    "id",
    "country",
    "category",
    "item_name",
    "qty",
    "status",
    "source_link",
    "vendor",
    "po_number",
    "priority",
    "requested_by",
    "date_requested",
    "ordered_date",
    "eta",
    "received_date",
    "owner",
    "notes"
]

HARDWARE_COLUMNS = [
    "id",
    "item",
    "total_ph",
    "total_in",
    "total_to_order",
    "item_status",
    "hardware_eta_ph",
    "hardware_eta_in",
    "owner",
    "blocker",
    "notes"
]

FIELD_REQUEST_COLUMNS = [
    "id",
    "section",
    "requested_field",
    "field_type",
    "reason",
    "requested_by",
    "status",
    "notes"
]


def fetch_table(table):
    res = supabase.table(table).select("*").order("id").execute()
    return pd.DataFrame(res.data)


def ensure_columns(df, columns):
    df = df.copy()
    for col in columns:
        if col not in df.columns:
            df[col] = None
    return df[columns]


def to_num(df, cols):
    df = df.copy()
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


def load_all():
    inventory = ensure_columns(fetch_table("inventory"), INVENTORY_COLUMNS)
    orders = ensure_columns(fetch_table("to_order"), ORDER_COLUMNS)
    hardware = ensure_columns(fetch_table("hardware_rollout"), HARDWARE_COLUMNS)
    field_requests = ensure_columns(fetch_table("field_requests"), FIELD_REQUEST_COLUMNS)

    inventory = to_num(inventory, ["qty"])
    orders = to_num(orders, ["qty"])
    hardware = to_num(hardware, ["total_ph", "total_in", "total_to_order"])

    return inventory, orders, hardware, field_requests


def clean_record(record):
    cleaned = {}

    for k, v in record.items():
        if k == "_delete":
            continue
        if pd.isna(v):
            cleaned[k] = None
        else:
            cleaned[k] = v

    return cleaned


def sync_table(table, df):
    df = df.copy()

    if "_delete" not in df.columns:
        df["_delete"] = False

    # Delete selected rows
    delete_df = df[df["_delete"] == True]
    for _, row in delete_df.iterrows():
        row_id = row.get("id")
        if pd.notna(row_id) and str(row_id).strip() != "":
            supabase.table(table).delete().eq("id", int(row_id)).execute()

    # Save non-deleted rows
    save_df = df[df["_delete"] != True].copy()

    for _, row in save_df.iterrows():
        record = clean_record(row.to_dict())
        row_id = record.get("id")

        if row_id is None or str(row_id).strip() == "":
            record.pop("id", None)
            supabase.table(table).insert(record).execute()
        else:
            record_id = int(row_id)
            record.pop("id", None)
            supabase.table(table).update(record).eq("id", record_id).execute()


def add_delete_column(df):
    df = df.copy()
    if "_delete" not in df.columns:
        df["_delete"] = False
    return df


def remove_delete_column(df):
    df = df.copy()
    if "_delete" in df.columns:
        df = df.drop(columns=["_delete"])
    return df


def get_country_options(*dfs):
    countries = set()

    for df in dfs:
        if not df.empty and "country" in df.columns:
            for c in df["country"].dropna().astype(str).str.strip():
                if c:
                    countries.add(c)

    preferred = ["USA", "India", "Philippines"]
    ordered = [c for c in preferred if c in countries]
    ordered += sorted([c for c in countries if c not in ordered])

    return ["All"] + ordered


def filter_by_country(df, country):
    if country == "All" or df.empty or "country" not in df.columns:
        return df.copy()
    return df[df["country"].astype(str) == country].copy()


def merge_filtered_back(full_df, edited_df, country):
    full_df = full_df.copy()
    edited_df = edited_df.copy()

    if country != "All" and "country" in edited_df.columns:
        edited_df["country"] = edited_df["country"].fillna("")
        edited_df.loc[edited_df["country"].astype(str).str.strip() == "", "country"] = country

    if country == "All":
        return edited_df

    keep_df = full_df[full_df["country"].astype(str) != country].copy()
    return pd.concat([keep_df, edited_df], ignore_index=True)


if "loaded" not in st.session_state:
    inventory_df, orders_df, hardware_df, field_requests_df = load_all()
    st.session_state.inventory_df = inventory_df
    st.session_state.orders_df = orders_df
    st.session_state.hardware_df = hardware_df
    st.session_state.field_requests_df = field_requests_df
    st.session_state.loaded = True


st.title("📦 V2D Inventory & Orders")

st.sidebar.header("Controls")

if st.sidebar.button("Reload from Supabase"):
    inventory_df, orders_df, hardware_df, field_requests_df = load_all()
    st.session_state.inventory_df = inventory_df
    st.session_state.orders_df = orders_df
    st.session_state.hardware_df = hardware_df
    st.session_state.field_requests_df = field_requests_df
    st.sidebar.success("Reloaded")

if st.sidebar.button("Save Changes"):
    sync_table("inventory", st.session_state.inventory_df)
    sync_table("to_order", st.session_state.orders_df)
    sync_table("hardware_rollout", st.session_state.hardware_df)
    sync_table("field_requests", st.session_state.field_requests_df)

    inventory_df, orders_df, hardware_df, field_requests_df = load_all()
    st.session_state.inventory_df = inventory_df
    st.session_state.orders_df = orders_df
    st.session_state.hardware_df = hardware_df
    st.session_state.field_requests_df = field_requests_df

    st.sidebar.success("Saved to Supabase")

st.sidebar.info("Use the _delete checkbox to remove rows, then click Save Changes.")

inventory_df = st.session_state.inventory_df
orders_df = st.session_state.orders_df
hardware_df = st.session_state.hardware_df
field_requests_df = st.session_state.field_requests_df

country_options = get_country_options(inventory_df, orders_df)

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "Dashboard",
    "USA Inventory",
    "India Inventory",
    "Philippines Inventory",
    "Orders",
    "Hardware Rollout",
    "Field Requests"
])

with tab1:
    st.subheader("Dashboard")

    dashboard_country = st.selectbox(
        "Country",
        country_options,
        key="dashboard_country"
    )

    inv_filtered = filter_by_country(inventory_df, dashboard_country)
    orders_filtered = filter_by_country(orders_df, dashboard_country)

    inv_qty = int(inv_filtered["qty"].sum()) if not inv_filtered.empty else 0
    orders_qty = int(orders_filtered["qty"].sum()) if not orders_filtered.empty else 0

    hardware_us_qty = int(hardware_df["total_us"].sum()) if not hardware_df.empty and "total_us" in hardware_df.columns else 0
    hardware_ph_qty = int(hardware_df["total_ph"].sum()) if not hardware_df.empty and "total_ph" in hardware_df.columns else 0
    hardware_in_qty = int(hardware_df["total_in"].sum()) if not hardware_df.empty and "total_in" in hardware_df.columns else 0
    hardware_total_qty = hardware_us_qty + hardware_ph_qty + hardware_in_qty

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Inventory Lines", len(inv_filtered))
    c2.metric("Inventory Units", inv_qty)
    c3.metric("Order Lines", len(orders_filtered))
    c4.metric("Order Units", orders_qty)
    c5.metric("Hardware Rollout Units", hardware_total_qty)

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Inventory by Country")
        if not inventory_df.empty:
            chart = inventory_df.groupby("country", dropna=False)["qty"].sum().reset_index()
            fig = px.bar(chart, x="country", y="qty")
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Orders by Country")
        if not orders_df.empty:
            chart = orders_df.groupby("country", dropna=False)["qty"].sum().reset_index()
            fig = px.bar(chart, x="country", y="qty")
            st.plotly_chart(fig, use_container_width=True)

    st.subheader("Hardware Rollout Units by Country")
    if not hardware_df.empty:
        hardware_country_totals = pd.DataFrame({
            "country": ["USA", "Philippines", "India"],
            "qty": [
                hardware_df["total_us"].sum() if "total_us" in hardware_df.columns else 0,
                hardware_df["total_ph"].sum() if "total_ph" in hardware_df.columns else 0,
                hardware_df["total_in"].sum() if "total_in" in hardware_df.columns else 0,
            ]
        })
        fig = px.bar(hardware_country_totals, x="country", y="qty")
        st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        st.subheader("Inventory by Category")
        if not inv_filtered.empty:
            chart = (
                inv_filtered.groupby("category", dropna=False)["qty"]
                .sum()
                .reset_index()
                .sort_values("qty", ascending=True)
            )
            fig = px.bar(chart, x="qty", y="category", orientation="h")
            st.plotly_chart(fig, use_container_width=True)

    with col4:
        st.subheader("Orders by Category")
        if not orders_filtered.empty:
            chart = (
                orders_filtered.groupby("category", dropna=False)["qty"]
                .sum()
                .reset_index()
                .sort_values("qty", ascending=True)
            )
            fig = px.bar(chart, x="qty", y="category", orientation="h")
            st.plotly_chart(fig, use_container_width=True)

    col5, col6 = st.columns(2)

    with col5:
        st.subheader("Inventory Status")
        if not inv_filtered.empty:
            chart = inv_filtered.groupby("status", dropna=False).size().reset_index(name="count")
            fig = px.pie(chart, names="status", values="count")
            st.plotly_chart(fig, use_container_width=True)

    with col6:
        st.subheader("Hardware Status")
        if not hardware_df.empty:
            chart = hardware_df.groupby("item_status", dropna=False).size().reset_index(name="count")
            fig = px.pie(chart, names="item_status", values="count")
            st.plotly_chart(fig, use_container_width=True)

    st.divider()

    st.subheader("Action Items")

    action_parts = []

    if not orders_filtered.empty:
        action_parts.append(orders_filtered.assign(source="Orders"))

    if not hardware_df.empty:
        hw_action = hardware_df[
            ~hardware_df["item_status"].astype(str).str.lower().isin(
                ["arrived", "received", "available", "on hand"]
            )
        ].copy()

        if not hw_action.empty:
            hw_action["source"] = "Hardware Rollout"
            action_parts.append(hw_action)

    if action_parts:
        action_df = pd.concat(action_parts, ignore_index=True, sort=False)
        st.dataframe(action_df, use_container_width=True)
    else:
        st.success("No action items.")

def inventory_country_section(tab, country_name):
    with tab:
        st.subheader(f"{country_name} Inventory")

        country_df = st.session_state.inventory_df[
            st.session_state.inventory_df["country"].astype(str) == country_name
        ].copy()

        group_options = ["All"] + sorted([
            x for x in country_df["item_group"].dropna().astype(str).unique()
            if x.strip()
        ]) if not country_df.empty and "item_group" in country_df.columns else ["All"]

        selected_group = st.selectbox(
            "Item Group",
            group_options,
            key=f"{country_name}_item_group"
        )

        filtered_df = country_df.copy()

        if selected_group != "All":
            filtered_df = filtered_df[filtered_df["item_group"].astype(str) == selected_group]

        category_options = ["All"] + sorted([
            x for x in filtered_df["category"].dropna().astype(str).unique()
            if x.strip()
        ]) if not filtered_df.empty and "category" in filtered_df.columns else ["All"]

        selected_category = st.selectbox(
            "Category",
            category_options,
            key=f"{country_name}_category"
        )

        if selected_category != "All":
            filtered_df = filtered_df[filtered_df["category"].astype(str) == selected_category]

        filtered_df = add_delete_column(filtered_df)

        edited = st.data_editor(
            filtered_df,
            use_container_width=True,
            num_rows="dynamic",
            disabled=["id"],
            key=f"{country_name}_inventory_editor"
        )

        # Merge edited rows back by ID; append new rows
        full = st.session_state.inventory_df.copy()

        if "_delete" not in edited.columns:
            edited["_delete"] = False

        # Ensure country is set for new rows
        edited["country"] = edited["country"].fillna("")
        edited.loc[edited["country"].astype(str).str.strip() == "", "country"] = country_name

        edited_ids = set([
            int(x) for x in edited["id"].dropna()
            if str(x).strip() != ""
        ]) if "id" in edited.columns else set()

        # Remove rows from full that were edited in this filtered view
        if "id" in full.columns and edited_ids:
            full = full[~full["id"].isin(edited_ids)]

        st.session_state.inventory_df = pd.concat([full, edited], ignore_index=True)

        st.info("Use Item Group/Category filters. Add/edit rows here. Click Save Changes in the sidebar.")


inventory_country_section(tab2, "USA")
inventory_country_section(tab3, "India")
inventory_country_section(tab4, "Philippines")


with tab5:
    st.subheader("Orders")

    orders_country = st.selectbox(
        "Country",
        country_options,
        key="orders_country"
    )

    orders_view = filter_by_country(st.session_state.orders_df, orders_country)
    orders_view = add_delete_column(orders_view)

    edited_orders = st.data_editor(
        orders_view,
        use_container_width=True,
        num_rows="dynamic",
        disabled=["id"],
        key="orders_editor"
    )

    st.session_state.orders_df = merge_filtered_back(
        st.session_state.orders_df,
        edited_orders,
        orders_country
    )

    st.info("Add/edit order rows here. Use _delete to delete. Click Save Changes in the sidebar.")

with tab6:
    st.subheader("Hardware Rollout")

    hardware_view = add_delete_column(st.session_state.hardware_df)

    st.session_state.hardware_df = st.data_editor(
        hardware_view,
        use_container_width=True,
        num_rows="dynamic",
        disabled=["id"],
        key="hardware_editor"
    )

    st.info("Use _delete to delete. Click Save Changes in the sidebar.")

with tab7:
    st.subheader("Field Requests")

    st.caption("Use this when someone wants a new approved column or section.")

    field_view = add_delete_column(st.session_state.field_requests_df)

    st.session_state.field_requests_df = st.data_editor(
        field_view,
        use_container_width=True,
        num_rows="dynamic",
        disabled=["id"],
        key="field_requests_editor"
    )

    st.info("Add requested fields here. Use _delete to delete. Click Save Changes in the sidebar.")
