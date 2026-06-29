import frappe


class VINCostLedgerRepository:

    def delete_by_cost_entry(self, cost_entry_name):

        frappe.db.delete(
            "VIN Cost Ledger",
            {
                "vin_cost_ledger_cost_entry": cost_entry_name,
            },
        )

    def insert_many(self, rows):

        for row in rows:
            frappe.get_doc(row).insert(ignore_permissions=True)