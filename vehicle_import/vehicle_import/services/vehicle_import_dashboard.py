import frappe
from collections import defaultdict
from frappe.query_builder.functions import Sum
from frappe.query_builder import DocType


@frappe.whitelist()
def get_dashboard_data():

    Warehouse = DocType("Warehouse")
    VehicleHolder = DocType("Vehicle Holder")

    warehouses = (
        frappe.qb.from_(Warehouse)
        .select(
            Warehouse.name,
            Warehouse.warehouse_name,
        )
        .where(Warehouse.is_group == 0)
        .orderby(Warehouse.lft)
    ).run(as_dict=True)

    holders = (
        frappe.qb.from_(VehicleHolder)
        .select(
            VehicleHolder.name,
            VehicleHolder.vehicle_holder_title,
            VehicleHolder.vehicle_holder_doc_nr,
            VehicleHolder.vehicle_holder_type,
            VehicleHolder.vehicle_holder_warehouse,
        )
        .orderby(VehicleHolder.modified, order=frappe.qb.desc)
    ).run(as_dict=True)

    VehicleHolderDetail = DocType("Vehicle Holder Detail")
    item_summary = (
        frappe.qb.from_(VehicleHolderDetail)
        .select(
            VehicleHolderDetail.parent,
            Sum(VehicleHolderDetail.vehicle_holder_detail_quantity).as_("item_count")
        )
        .groupby(VehicleHolderDetail.parent)
    ).run(as_dict=True)
    item_map = {
        int(row["parent"]): row["item_count"]
        for row in item_summary
    }

    summary_map = defaultdict(lambda: {
        "item_count": 0,
        "total_cost": 0,
    })
    detail_to_holder = {
        int(row["name"]): int(row["parent"])
        for row in (
            frappe.qb.from_(VehicleHolderDetail)
            .select(
                VehicleHolderDetail.name,
                VehicleHolderDetail.parent,
            )
        ).run(as_dict=True)
    }
    CostEntry = DocType("Cost Entry")
    cost_entries = (
        frappe.qb.from_(CostEntry)
        .select(
            CostEntry.cost_entry_reference_doctype,
            CostEntry.cost_entry_reference_name,
            CostEntry.cost_entry_base_amount,
            CostEntry.cost_entry_base_currency,
        )
        .where(CostEntry.docstatus == 1)
    ).run(as_dict=True) 
    for row in cost_entries:
        holder = None
        ref = row["cost_entry_reference_name"]
        
        if not ref:
            continue
        
        if row["cost_entry_reference_doctype"] == "Vehicle Holder":
            holder = int(ref)
        elif row["cost_entry_reference_doctype"] == "Vehicle Holder Detail":
            holder = detail_to_holder.get(int(ref))
        
        if not holder:
            continue

        summary = summary_map[holder]
        summary["total_cost"] += row["cost_entry_base_amount"] or 0
        for holder_name, item_count in item_map.items():
            summary_map[holder_name]["item_count"] = item_count    

    holder_map = defaultdict(list)
    for holder in holders:
        holder["summary"] = summary_map[holder["name"]]
        holder_map[holder["vehicle_holder_warehouse"]].append(holder)


    for warehouse in warehouses:
        warehouse["holders"] = holder_map.get(warehouse["name"], [])

    return {
        "currency": frappe.defaults.get_global_default("currency"),
        "warehouses": warehouses,
    }

@frappe.whitelist()
def move_holder(holder, warehouse):
    holder_doc = frappe.get_doc("Vehicle Holder", holder)
    holder_doc.vehicle_holder_warehouse = warehouse
    holder_doc.save(ignore_permissions=False)
    return {
        "success": True
    }