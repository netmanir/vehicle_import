# Copyright (c) 2026, ACP and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.query_builder import DocType
from pypika.functions import Cast
from pypika import Case, Order

from frappe.model.delete_doc import (
    get_linked_docs,
    get_dynamic_linked_docs,
)

from vehicle_import.vehicle_import.services.vehicle_holder_service import VehicleHolderService


class VehicleHolder(Document):

    def validate(self):
        self._validate_not_finalized()
        if not getattr(self, "_is_importing", False):
            self._validate_duplicate_items()
            self._validate_vehicle_quantities()
            VehicleHolderService().validate_warehouse_rules(self)


    def before_update_after_submit(self):
        VehicleHolderService().validate_warehouse_rules(self)


    def before_save(self):
        if not getattr(self, "_is_importing", False):
            self._sync_vehicle_units()
            self._remove_orphan_histories()


    def before_cancel(self):
        self._validate_not_finalized()
        if not frappe.flags.vehicle_holder_cancel:
            frappe.throw(
                _("Please use the 'Cancel Vehicle Holder' action.")
            )


    def before_submit(self):
        self._validate_not_finalized()
        if not frappe.flags.vehicle_holder_submit:
            frappe.throw(
                _("Please use the 'Submit Vehicle Holder' action.")
            )


    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------
    def _validate_duplicate_items(self):
        seen = set()
        for detail in self.vehicle_holder_detail:
            item = detail.vehicle_holder_detail_item
            if item in seen:
                frappe.throw(
                    _("Item {0} is duplicated.").format(item),
                    title=_("Vehicle Holder Validation"),
                )
            seen.add(item)


    def _validate_vehicle_quantities(self):
        for detail in self.vehicle_holder_detail:
            vehicle_history_count = frappe.db.count(
                "Vehicle History",
                filters={
                    "vehicle_history_vehicle_holder_detail": detail.name,
                },
            )

            if detail.vehicle_holder_detail_quantity < vehicle_history_count:
                frappe.throw(
                    _("Quantity for item {0} cannot be less than assigned vehicles ({1}).").format(
                        detail.vehicle_holder_detail_item,
                        vehicle_history_count,
                    ),
                    title=_("Vehicle Holder Validation"),
                )


    def _validate_not_finalized(self):
        if self.is_new():
            return

        old = self.get_doc_before_save()
        if not old or not old.vehicle_holder_finalized:
            return

        # Only allow changing "Finalized" field
        if (
            self.has_value_changed("vehicle_holder_finalized")
            and self.get_dirty_fields() == {"vehicle_holder_finalized": 0}
        ):
            return

        frappe.throw(
            _("Vehicle Holder is finalized. Change is not allowed!")
        )


    # ---------------------------------------------------------
    # Synchronization
    # ---------------------------------------------------------
    def _sync_vehicle_units(self):

        for detail in self.vehicle_holder_detail:
            vehicle_history_count = frappe.db.count(
                "Vehicle History",
                filters={
                    "vehicle_history_vehicle_holder_detail": detail.name,
                },
            )

            missing_count = (
                detail.vehicle_holder_detail_quantity
                - vehicle_history_count
            )

            if missing_count <= 0:
                continue

            for _ in range(missing_count):

                vehicle = self._create_vehicle_unit(detail)

                self._create_vehicle_history(
                    vehicle=vehicle,
                    detail=detail,
                )


    # ---------------------------------------------------------
    # Helper Methodes
    # ---------------------------------------------------------
    def _create_vehicle_unit(self, detail):
        vehicle = frappe.get_doc({
            "doctype": "Vehicle Unit",
            "vehicle_item": detail.vehicle_holder_detail_item,
        })
        vehicle.insert()
        return vehicle


    def _create_vehicle_history(self, vehicle, detail):
        self.append("vehicle_holder_history", {
            "vehicle_history_vehicle": vehicle.name,
            "vehicle_history_vehicle_holder_detail": detail.name,
        })


    def _remove_orphan_histories(self):

        valid_details = {
            detail.name
            for detail in self.vehicle_holder_detail
        }

        self.vehicle_holder_history = [
            history
            for history in self.vehicle_holder_history
            if history.vehicle_history_vehicle_holder_detail in valid_details
        ]


    def _import_vehicle(self, vehicle, reference):

        detail = self._find_or_create_detail(
            vehicle["vehicle_item"]
        )

        self.append("vehicle_holder_history", {
            "vehicle_history_vehicle": vehicle["vehicle_history_vehicle"],
            "vehicle_history_vehicle_holder_detail": detail.name,
            "vehicle_history_reference": reference,
        })


    def _find_or_create_detail(self, vehicle_item):

        for detail in self.vehicle_holder_detail:
            if detail.vehicle_holder_detail_item == vehicle_item:
                return detail

        return self.append("vehicle_holder_detail", {
            "vehicle_holder_detail_item": vehicle_item,
            "vehicle_holder_detail_quantity": 0,
        })


    def _update_detail_quantities(self):

        for detail in self.vehicle_holder_detail:

            detail.vehicle_holder_detail_quantity = frappe.db.count(
                "Vehicle History",
                filters={
                    "vehicle_history_vehicle_holder_detail": detail.name,
                },
            )
            

@frappe.whitelist()
def get_holders(search="", exclude_holder=None):

    filters = {
        "docstatus": 1,  
    }

    if exclude_holder:
        filters["name"] = ["!=", exclude_holder]

    kwargs = {
        "doctype": "Vehicle Holder",
        "fields": [
            "name",
            "vehicle_holder_type",
            "vehicle_holder_title",
            "vehicle_holder_doc_nr"
        ],
        "filters": filters,
        "order_by": "modified desc"
    }

    if search:
        kwargs["or_filters"] = [
            ["vehicle_holder_title", "like", f"%{search}%"],
            ["vehicle_holder_doc_nr", "like", f"%{search}%"]
        ]

    return frappe.get_all(**kwargs)


@frappe.whitelist()
def get_holder_details(holder_name):

    return frappe.get_all(
        "Vehicle Holder Detail",
        filters={
            "parent": holder_name
        },
        fields=[
            "name",
            "vehicle_holder_detail_item",
            "vehicle_holder_detail_quantity",
            "vehicle_holder_detail_remark"
        ],
        order_by="idx"
    )


@frappe.whitelist()
def get_holder_histories(
    current_holder,
    reference_detail_name,
):

    ReferenceHistory = DocType("Vehicle History")
    CurrentHistory = DocType("Vehicle History")
    VehicleUnit = DocType("Vehicle Unit")

    return (
        frappe.qb
        .from_(ReferenceHistory)

        .left_join(VehicleUnit)
        .on(
            ReferenceHistory.vehicle_history_vehicle == VehicleUnit.name
        )

        .left_join(CurrentHistory)
        .on(
            (CurrentHistory.parent == current_holder)
            &
            (CurrentHistory.vehicle_history_vehicle == ReferenceHistory.vehicle_history_vehicle)
        )

        .select(
            ReferenceHistory.name,
            ReferenceHistory.parent,
            ReferenceHistory.vehicle_history_vehicle,
            ReferenceHistory.vehicle_history_vehicle_holder_detail,
            ReferenceHistory.vehicle_history_remark,
            VehicleUnit.vehicle_item,

            Case()
                .when(
                    (VehicleUnit.vehicle_vin.isnull())
                    |
                    (VehicleUnit.vehicle_vin == ""),
                    VehicleUnit.name,
                )
                .else_(VehicleUnit.vehicle_vin)
                .as_("vehicle"),
        )

        .where(
            (ReferenceHistory.vehicle_history_vehicle_holder_detail == reference_detail_name)
            &
            CurrentHistory.name.isnull()
        )

        .orderby(VehicleUnit.vehicle_vin)

        .run(as_dict=True)
    )


@frappe.whitelist()
def import_vehicles(holder, vehicles, reference):

    doc = frappe.get_doc("Vehicle Holder", holder)

    vehicles = frappe.parse_json(vehicles)

    # Step 1: Create Details
    for vehicle in vehicles:
        doc._find_or_create_detail(vehicle["vehicle_item"])

    doc._is_importing = True
    doc.save()

    # Step 2: Create Histories
    duplicate_vehicles = []
    for vehicle in vehicles:
        if frappe.db.exists(
            "Vehicle History",
            {
                "vehicle_history_vehicle": vehicle["vehicle_history_vehicle"],
                "parent": doc.name,
            },
        ):
            duplicate_vehicles.append(vehicle["vehicle"])
            continue

        doc._import_vehicle(vehicle, reference)

    doc._is_importing = True
    doc.save()
    
    doc._update_detail_quantities()
    doc._is_importing = True
    doc.save()
    
    if duplicate_vehicles:

        frappe.msgprint(
            _("The following vehicles were duplicated and were skipped:{0}{1}")
            .format("<br><br>", "<br>".join(duplicate_vehicles)),
            title=_("Duplicate Vehicles"),
            indicator="orange",
        )    

    return doc.name


@frappe.whitelist()
def get_holder_detail(name):
    product, qty = frappe.db.get_value(
        "Vehicle Holder Detail",
        name,
        [
            "vehicle_holder_detail_item",
            "vehicle_holder_detail_quantity",
        ],
    )

    return {
        "product": product,
        "qty": qty,
    }


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def vehicle_holder_detail_query(
    doctype,
    txt,
    searchfield,
    start,
    page_len,
    filters,
):
    VehicleHolderDetail = DocType("Vehicle Holder Detail")
    result = (
        frappe.qb
        .from_(VehicleHolderDetail)
        .select(
            VehicleHolderDetail.name,
            VehicleHolderDetail.vehicle_holder_detail_item,
            VehicleHolderDetail.vehicle_holder_detail_quantity,
        )
        .where(
            (VehicleHolderDetail.parent == filters.get("parent"))
            & (
                VehicleHolderDetail.vehicle_holder_detail_item.like(f"%{txt}%")
            )
        )
        .orderby(VehicleHolderDetail.idx)
        .limit(page_len)
        .offset(start)
        .run(as_list=True)
    )

    return [
        [
            row[0],
            f"{row[1]} ({row[2]})",
        ]
        for row in result
    ]


@frappe.whitelist()
def assign_vins(
    vehicle_holder,
    vehicle_holder_detail,
    vins,
):

    return VehicleHolderService().assign_vins(
        holder_name=vehicle_holder,
        holder_detail_name=vehicle_holder_detail,
        vins_text=vins,
    )
    

@frappe.whitelist()
def get_cancel_preview(holder):
    doc = frappe.get_doc("Vehicle Holder", holder)
    links = (
        get_linked_docs(doc, "Cancel")
        + get_dynamic_linked_docs(doc, "Cancel")
    )

    cost_entries = VehicleHolderService.get_related_cost_entries(holder)

    existing = {
        row["reference_docname"]
        for row in links
        if row["reference_doctype"] == "Cost Entry"
    }
    
    for name in cost_entries:

        if name not in existing:

            links.append({
                "doc": doc.name,
                "reference_doctype": "Cost Entry",
                "reference_docname": name,
                "at_position": "",
            })

    return links


@frappe.whitelist()
def cancel_vehicle_holder(holder):

    frappe.flags.vehicle_holder_cancel = True

    try:
        VehicleHolderService().cascade_cancel(holder)

    finally:
        frappe.flags.cascade_cancel = False


@frappe.whitelist()
def submit_vehicle_holder(holder):

    frappe.flags.vehicle_holder_submit = True

    try:
        VehicleHolderService().do_submit(holder)

    finally:
        frappe.flags.vehicle_holder_submit = False


@frappe.whitelist()
def get_assigned_vin_counts(vehicle_holder):
    return VehicleHolderService.get_assigned_vin_counts(vehicle_holder)


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def warehouse_query(
    doctype,
    txt,
    searchfield,
    start,
    page_len,
    filters,
):
    Warehouse = DocType("Warehouse")
    WarehouseRule = DocType("Warehouse Rule")

    return (
        frappe.qb
        .from_(Warehouse)
        .left_join(WarehouseRule)
        .on(
            (Warehouse.name == WarehouseRule.warehouse)
            & (WarehouseRule.rule_type == "Display Order")
        )
        .select(
            Warehouse.name,
            Warehouse.name.as_('warehouse_name'),
        )
        .where(
            (Warehouse.is_group == 0)
            & (Warehouse.name.like(f"%{txt}%"))
        )
        .orderby(
            Cast(
                WarehouseRule.rule_value,
                "SIGNED",
            ),
            order=Order.asc,
        )
        .orderby(
            Warehouse.lft,
            order=Order.asc,
        )
        .limit(page_len)
        .offset(start)
    ).run()