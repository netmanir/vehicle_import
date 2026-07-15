import frappe
from collections import defaultdict
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

    holder_map = defaultdict(list)

    for holder in holders:
        holder_map[holder["vehicle_holder_warehouse"]].append(holder)

    for warehouse in warehouses:
        warehouse["holders"] = holder_map.get(warehouse["name"], [])

    return warehouses


@frappe.whitelist()
def move_holder(holder, warehouse):
    holder_doc = frappe.get_doc("Vehicle Holder", holder)
    holder_doc.vehicle_holder_warehouse = warehouse
    holder_doc.save(ignore_permissions=False)
    return {
        "success": True
    }