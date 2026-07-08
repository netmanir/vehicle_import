import frappe
from frappe import _
from frappe.query_builder import DocType


class VehicleHolderCostReport:

    def execute(
        self,
        vehicle_holder,
    ):

        return {

            "columns": self.get_columns(),

            "rows": self.get_rows(
                vehicle_holder,
            ),
        }

    def get_columns(self):

        return [

            {
                "id": "vehicle",
                "name": _("Vehicle"),
                "width": 90,
            },

            {
                "id": "item",
                "name": _("Item"),
                "width": 120,
            },

            {
                "id": "status",
                "name": _("Status"),
                "width": 90,
            },

            {
                "id": "cost_date",
                "name": _("Cost Date"),
                "width": 110,
            },

            {
                "id": "cost_category",
                "name": _("Cost Category"),
                "width": 120,
            },

            {
                "id": "base_amount",
                "name": _("Base Amount"),
                "width": 130,
            },

            # {
            #     "id": "currency",
            #     "name": _("Foreign Currency"),
            #     "width": 90,
            # },

            # {
            #     "id": "foreign_amount",
            #     "name": _("Foreign Amount"),
            #     "width": 120,
            # },

            {
                "id": "holder",
                "name": _("Vehicle Holder"),
                "width": 120,
            },

            {
                "id": "holder_detail",
                "name": _("Holder Detail"),
                "width": 120,
            },

            {
                "id": "reference",
                "name": _("Reference"),
                "width": 120,
            },

        ]


    def get_rows(
        self,
        vehicle_holder,
    ):

        CostLedger = DocType("Cost Ledger")
        CostEntry = DocType("Cost Entry")
        VehicleUnit = DocType("Vehicle Unit")
        VehicleHistory = DocType("Vehicle History")
        VehicleHolderDetail = DocType("Vehicle Holder Detail")

        rows = (

            frappe.qb

            .from_(CostLedger)

            .inner_join(CostEntry)

            .on(
                CostLedger.cost_ledger_cost_entry
                ==
                CostEntry.name
            )

            .inner_join(VehicleUnit)

            .on(
                CostLedger.cost_ledger_vin
                ==
                VehicleUnit.name
            )

            .inner_join(VehicleHistory)

            .on(
                VehicleHistory.vehicle_history_vehicle
                ==
                VehicleUnit.name
            )

            .left_join(VehicleHolderDetail)

            .on(
                VehicleHolderDetail.name
                ==
                VehicleHistory.vehicle_history_vehicle_holder_detail
            )

            .select(

                VehicleUnit.name.as_("vehicle"),

                VehicleHolderDetail.vehicle_holder_detail_item.as_("item"),

                CostEntry.docstatus.as_("status"),

                CostEntry.cost_entry_date.as_("cost_date"),

                CostEntry.cost_entry_cost_category.as_("cost_category"),

                CostLedger.cost_ledger_base_amount.as_("base_amount"),

                CostLedger.cost_ledger_currency.as_("currency"),

                CostLedger.cost_ledger_foreign_amount.as_("foreign_amount"),

                VehicleHistory.parent.as_("holder"),

                VehicleHistory.vehicle_history_vehicle_holder_detail.as_("holder_detail"),

                CostEntry.cost_entry_reference_name.as_("reference"),

            )

            .where(
                VehicleHistory.parent == vehicle_holder
            )

            .orderby(
                CostEntry.cost_entry_date
            )

            .run(
                as_dict=True,
            )
        )

        for row in rows:

            row["status"] = {

                0: _("Draft"),
                1: _("Submitted"),
                2: _("Cancelled"),

            }.get(row["status"])

            row["base_amount"] = frappe.format_value(
                row["base_amount"],
                {
                    "fieldtype": "Currency",
                },
            )

        return rows


@frappe.whitelist()
def get_vehicle_holder_cost_report(
    vehicle_holder,
):

    return VehicleHolderCostReport().execute(
        vehicle_holder,
    )