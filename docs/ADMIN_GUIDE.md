# V2D Inventory & Orders Dashboard Guide

## What this dashboard does

This dashboard tracks:

- Inventory
- Orders
- Hardware Rollout
- Field Requests

Data is stored in Supabase. The dashboard is deployed with Streamlit.

---

## Main sections

### Dashboard
Shows summary metrics and charts.

### Inventory
Used for items already available or physically tracked.

Common fields:
- country
- location
- item_group
- category
- item_name
- model
- qty
- status
- owner
- asset_id
- serial_number
- condition
- storage_bin
- last_seen
- notes
- source_sheet

### Orders
Used for items that need to be ordered or are in procurement.

Common fields:
- country
- category
- item_name
- qty
- status
- source_link
- vendor
- po_number
- priority
- requested_by
- date_requested
- ordered_date
- eta
- received_date
- owner
- notes

### Hardware Rollout
Used for hardware rollout planning and ETA tracking.

Common fields:
- item
- total_us
- total_ph
- total_in
- total_to_order
- item_status
- hardware_eta_us
- hardware_eta_ph
- hardware_eta_in
- owner
- blocker
- notes

### Field Requests
Used when someone wants a new approved field/column or new section.

Common fields:
- section
- requested_field
- field_type
- reason
- requested_by
- status
- notes

---

## What users can do

Users can:

- View dashboard metrics
- Filter inventory/orders by country
- Add new rows
- Edit existing rows
- Mark rows for deletion using `_delete`
- Click `Save Changes` to save updates
- Click `Reload from Supabase` to refresh data
- Submit field requests

---

## How to add a new row

1. Go to the relevant tab:
   - Inventory
   - Orders
   - Hardware Rollout
   - Field Requests
2. Scroll to the bottom of the table.
3. Add a new row.
4. Fill in required fields.
5. Click `Save Changes`.

---

## How to delete a row

1. Find the row.
2. Check the `_delete` box.
3. Click `Save Changes`.

---

## How to request a new column

Users should not directly add random columns.

Instead:

1. Go to `Field Requests`.
2. Add a row.
3. Fill:
   - section
   - requested_field
   - field_type
   - reason
   - requested_by
   - status = Requested
4. Click `Save Changes`.

An admin can review and approve later.

---

# Admin Guide

## Add a new approved column

Example: add `cost` to Orders.

### 1. Add column in Supabase SQL Editor

```sql
alter table to_order add column if not exists cost numeric default 0;

docs/ADMIN_GUIDE.md

