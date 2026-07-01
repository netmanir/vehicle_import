import frappe
from vehicle_import.vehicle_import.repositories.vin_cost_ledger_repository import (
    VINCostLedgerRepository,
)
from vehicle_import.vehicle_import.services.allocation_engine import (
    AllocationEngine,
)


class CostEntryService:

    def create(
        self,
        
        reference_doctype,
        reference_name,

        cost_date,
        cost_category,

        currency,
        exchange_rate,
        foreign_amount,

        description=None,
    ):

        doc = frappe.get_doc({

            "doctype": "Cost Entry",

            "cost_entry_reference_doctype":
                reference_doctype,
            "cost_entry_reference_name":
                reference_name,

            "cost_entry_date":
                cost_date,
            "cost_entry_cost_category":
                cost_category,

            "cost_entry_currency":
                currency,
            "cost_entry_exchange_rate":
                exchange_rate,
            "cost_entry_foreign_amount":
                foreign_amount,

            "cost_entry_description":
                description,
        })

        doc.insert()

        return doc.name


    def rebuild(self, cost_entry, vins):

        repository = VINCostLedgerRepository()

        repository.delete_by_cost_entry(
            cost_entry.name
        )

        rows = AllocationEngine().allocate(
            cost_entry,
            vins,
        )

        docs = []

        for row in rows:

            docs.append(
                {
                    "doctype": "VIN Cost Ledger",
                    "vin_cost_ledger_vin": row["vin"],
                    "vin_cost_ledger_cost_entry": cost_entry.name,
                    "vin_cost_ledger_currency": cost_entry.cost_entry_currency,
                    "vin_cost_ledger_exchange_rate": cost_entry.cost_entry_exchange_rate,
                    "vin_cost_ledger_foreign_amount": row["foreign_amount"],
                    "vin_cost_ledger_base_currency": cost_entry.cost_entry_base_currency,
                    "vin_cost_ledger_base_amount": row["base_amount"],
                }
            )

        repository.insert_many(docs)