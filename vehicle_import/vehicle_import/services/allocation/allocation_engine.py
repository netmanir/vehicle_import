import frappe

from .allocation_context import AllocationContext
from .ledger_builder import LedgerBuilder
from .strategy_factory import StrategyFactory


class AllocationEngine:

    def submit(
        self,
        cost_entry,
    ):

        context = AllocationContext(
            cost_entry,
        )

        strategy = (
            StrategyFactory()
            .create(context)
        )

        result = strategy.allocate(
            context,
        )

        docs = LedgerBuilder().build(
            context,
            result,
        )

        for doc in docs:
            ledger = frappe.get_doc(doc)

            ledger.insert()

            ledger.submit()

        return docs


    def cancel(
        self,
        cost_entry,
    ):

        ledgers = frappe.get_all(
            "Cost Ledger",
            filters={
                "cost_ledger_cost_entry":
                    cost_entry.name,
                "docstatus":
                    1,
            },
            pluck="name",
        )

        for ledger_name in ledgers:

            ledger = frappe.get_doc(
                "Cost Ledger",
                ledger_name,
            )

            ledger.cancel()

        return ledgers


    def delete(self, cost_entry):
        ledger_names = (
            frappe.get_all(
                "Cost Ledger",
                filters={
                    "cost_ledger_cost_entry": cost_entry.name,
                },
                pluck="name",
            )
        )
        for name in ledger_names:
            frappe.get_doc("Cost Ledger", name).delete()