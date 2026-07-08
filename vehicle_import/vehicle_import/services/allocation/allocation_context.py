import frappe
from frappe.query_builder import DocType


class AllocationContext:

    def __init__(
        self,
        cost_entry,
    ):
        if isinstance(
            cost_entry,
            str,
        ):
            cost_entry = frappe.get_doc(
                "Cost Entry",
                cost_entry,
            )

        self.cost_entry = cost_entry

        self.reference_doctype = (
            cost_entry.cost_entry_reference_doctype
        )

        self.reference_name = (
            cost_entry.cost_entry_reference_name
        )

        self.cost_category = frappe.get_doc(
            "Cost Category",
            cost_entry.cost_entry_cost_category,
        )

        self.allocation_rule = frappe.get_doc(
            "Allocation Rule",
            self.cost_category.cost_category_default_allocation_rule,
        )

        self.currency = (
            cost_entry.cost_entry_currency
        )

        self.exchange_rate = (
            cost_entry.cost_entry_exchange_rate
        )

        self.foreign_amount = (
            cost_entry.cost_entry_foreign_amount
        )

        self.base_currency = (
            cost_entry.cost_entry_base_currency
        )

        self.base_amount = (
            cost_entry.cost_entry_base_amount
        )

        self.vehicles = []

        self.load_vehicles()


    def load_vehicles(
        self,
    ):

        if self.reference_doctype == "Vehicle Holder":
            self.vehicles = self._load_holder_vehicles()
            return

        if self.reference_doctype == "Vehicle Holder Detail":
            self.vehicles = self._load_holder_detail_vehicles()
            return

        raise frappe.ValidationError(
            f"Unsupported reference doctype: {self.reference_doctype}"
        )


    def _load_holder_vehicles(
        self,
    ):
        VehicleHistory = DocType("Vehicle History")
        VehicleUnit = DocType("Vehicle Unit")

        rows = (
            frappe.qb
            .from_(VehicleHistory)

            .inner_join(VehicleUnit)
            .on( VehicleHistory.vehicle_history_vehicle == VehicleUnit.name )

            .select(
                VehicleUnit.name.as_("vehicle"),
                VehicleHistory.parent.as_("holder"),
                VehicleHistory.vehicle_history_vehicle_holder_detail.as_("holder_detail"),
                VehicleHistory.name.as_("history"),
                VehicleUnit.vehicle_item.as_("item"),
            )

            .where( VehicleHistory.parent == self.reference_name )

            .orderby( VehicleHistory.idx )

            .run(as_dict=True)
        )

        return rows


    def _load_holder_detail_vehicles(
        self,
    ):
        VehicleHistory = DocType("Vehicle History")
        VehicleUnit = DocType("Vehicle Unit")

        rows = (
            frappe.qb
            .from_(VehicleHistory)

            .inner_join(VehicleUnit)
            .on( VehicleHistory.vehicle_history_vehicle == VehicleUnit.name )

            .select(
                VehicleUnit.name.as_("vehicle"),
                VehicleHistory.parent.as_("holder"),
                VehicleHistory.vehicle_history_vehicle_holder_detail.as_("holder_detail"),
                VehicleHistory.name.as_("history"),
                VehicleUnit.vehicle_item.as_("item"),
            )

            .where( VehicleHistory.vehicle_history_vehicle_holder_detail == self.reference_name )

            .orderby( VehicleHistory.idx )

            .run(as_dict=True)
        )

        return rows