# Copyright (c) 2026, ACP and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.query_builder import DocType
from pypika import Case

class VehicleHolder(Document):

    def validate(self):
        if not getattr(self, "_is_importing", False):
            self._validate_duplicate_items()
            self._validate_vehicle_quantities()


    def before_save(self):
        if not getattr(self, "_is_importing", False):
            self._sync_vehicle_units()
            self._remove_orphan_histories()


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
            "vehicle_history_vehicle_holder": self.name,
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


    def _import_vehicle(self, vehicle):

        detail = self._find_or_create_detail(
            vehicle["vehicle_item"]
        )

        self.append("vehicle_holder_history", {
            "vehicle_history_vehicle": vehicle["vehicle_history_vehicle"],
            "vehicle_history_vehicle_holder_detail": detail.name,
            "vehicle_history_reference": vehicle["vehicle_history_vehicle_holder"],
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
def get_holder_histories(detail_name):

    VehicleHistory = frappe.qb.DocType("Vehicle History")
    VehicleUnit = frappe.qb.DocType("Vehicle Unit")

    return (
        frappe.qb
        .from_(VehicleHistory)
        .left_join(VehicleUnit)
        .on(VehicleHistory.vehicle_history_vehicle == VehicleUnit.name)
        .select(
            VehicleHistory.name,
            VehicleHistory.vehicle_history_vehicle,
            VehicleHistory.vehicle_history_vehicle_holder,
            VehicleHistory.vehicle_history_vehicle_holder_detail,
            VehicleHistory.vehicle_history_remark,
            VehicleUnit.vehicle_item,
            Case()
                .when(
                    (VehicleUnit.vehicle_vin.isnull()) |
                    (VehicleUnit.vehicle_vin == ""),
                    VehicleUnit.name
                )
                .else_(VehicleUnit.vehicle_vin)
                .as_("vehicle"),
        )
        .where(
            (VehicleHistory.vehicle_history_vehicle_holder_detail == detail_name)
        )
        .orderby(VehicleUnit.vehicle_vin)
        .run(as_dict=True)
    )


@frappe.whitelist()
def import_vehicles(holder, vehicles):

    doc = frappe.get_doc("Vehicle Holder", holder)

    vehicles = frappe.parse_json(vehicles)

    # Step 1: Create Details
    for vehicle in vehicles:
        doc._find_or_create_detail(vehicle["vehicle_item"])

    doc._is_importing = True
    doc.save()

    # Step 2: Create Histories
    doc = frappe.get_doc("Vehicle Holder", holder)    

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

        doc._import_vehicle(vehicle)

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

