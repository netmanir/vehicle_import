import frappe

from vehicle_import.vehicle_import.services.cost_entry_service import (
    CostEntryService,
)


@frappe.whitelist()
def create_cost_entry(
    reference_doctype,
    reference_name,

    cost_date,
    cost_category,

    currency,
    exchange_rate,
    foreign_amount,

    description=None,
):

    return CostEntryService().create(
        reference_doctype=reference_doctype,
        reference_name=reference_name,

        cost_date=cost_date,
        cost_category=cost_category,

        currency=currency,
        exchange_rate=exchange_rate,
        foreign_amount=foreign_amount,

        description=description,
    )