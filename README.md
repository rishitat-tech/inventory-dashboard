# V2D Inventory & Orders Dashboard

A Streamlit dashboard for tracking inventory, orders, hardware rollout, and field requests.

App link: https://v2d-inventory.streamlit.app/

## Sections

- Dashboard
- USA Inventory
- India Inventory
- Philippines Inventory
- Orders
- Hardware Rollout
- Field Requests

## How to Access

1. Open the app link in a browser: https://v2d-inventory.streamlit.app/
2. Wait for the app to load.
3. If data does not appear, click `Reload from Supabase`.
4. Use the tabs to view or edit data.

Regular users do not need to install anything.

## What Users Can Do

Users can:

- View inventory and order summaries
- View inventory by country
- View orders by country
- Add new inventory rows
- Add new order rows
- Update hardware rollout status and ETAs
- Request new fields or columns
- Mark rows for deletion
- Save changes to Supabase

## Add a New Inventory Item

1. Go to `USA Inventory`, `India Inventory`, or `Philippines Inventory`.
2. Scroll to the bottom of the table.
3. Add a new row.
4. Fill in the item details:
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
5. Click `Save Changes`.
6. Click `Reload from Supabase` to confirm it saved.

## Add a New Order

1. Go to the `Orders` tab.
2. Scroll to the bottom of the table.
3. Add a new row.
4. Fill in the order details:
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
5. Click `Save Changes`.

## Update Hardware Rollout

1. Go to `Hardware Rollout`.
2. Update fields as needed:
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
3. Click `Save Changes`.

## Delete a Row

1. Find the row to delete.
2. Check the `_delete` box for that row.
3. Click `Save Changes`.
4. Click `Reload from Supabase` to confirm it was removed.

## Request a New Field or Column

Use the `Field Requests` tab instead of adding random columns.

1. Go to `Field Requests`.
2. Add a new row.
3. Fill in:
   - section
   - requested_field
   - field_type
   - reason
   - requested_by
   - status
   - notes
4. Click `Save Changes`.

An admin can review and add approved fields later.

## Data Storage

Live data is stored in Supabase.

Main Supabase tables:

- inventory
- to_order
- hardware_rollout
- field_requests

Supabase is the source of truth for live data.

## Local Development

Clone the repo:

```bash
git clone https://github.com/rishitat-tech/inventory-dashboard.git
cd inventory-dashboard

