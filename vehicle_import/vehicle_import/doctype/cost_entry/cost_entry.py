# Copyright (c) 2026, ACP and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document

from vehicle_import.vehicle_import.services.allocation import (
    AllocationEngine,
)

class CostEntry(Document):

    def on_submit(self):

        AllocationEngine().submit(
            self,
        )

    def on_cancel(self):

        AllocationEngine().cancel(
            self,
        )

    def on_trash(self):
        AllocationEngine().delete(self)