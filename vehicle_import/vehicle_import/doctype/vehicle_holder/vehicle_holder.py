# Copyright (c) 2026, ACP and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class VehicleHolder(Document):

    def validate(self):
        self._validate_duplicate_items()
        self._validate_vehicle_quantities()


    def before_save(self):
        self._sync_vehicle_units()


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
