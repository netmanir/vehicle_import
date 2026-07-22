# Copyright (c) 2026, ACP and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from vehicle_import.vehicle_import.services.allocation import (
    AllocationEngine,
)


class CostEntry(Document):

    def before_save(self):
        self.validate_vehicle_holder_not_finalized()


    def on_submit(self):
        self.validate_vehicle_holder_not_finalized()
        AllocationEngine().submit(self)


    def on_cancel(self):
        self.validate_vehicle_holder_not_finalized()
        AllocationEngine().cancel(self)


    def on_trash(self):
        self.validate_vehicle_holder_not_finalized()
        AllocationEngine().delete(self)


    def get_vehicle_holder(self):
        if self.cost_entry_reference_doctype == "Vehicle Holder":
            return self.cost_entry_reference_name

        if self.cost_entry_reference_doctype == "Vehicle Holder Detail":
            return frappe.db.get_value(
                "Vehicle Holder Detail",
                self.cost_entry_reference_name,
                "parent",
            )

        frappe.throw(
            _("Unsupported reference doctype.")
        )


    def validate_vehicle_holder_not_finalized(self):
        holder = self.get_vehicle_holder()

        if frappe.db.get_value(
            "Vehicle Holder",
            holder,
            "vehicle_holder_finalized",
        ):
            frappe.throw(
                _("Vehicle Holder is finalized. Change is not allowed!")
            )

