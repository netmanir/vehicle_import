from vehicle_import.vehicle_import.repositories.vin_cost_ledger_repository import (
    VINCostLedgerRepository,
)
from vehicle_import.vehicle_import.services.allocation_engine import (
    AllocationEngine,
)


class CostEntryService:

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