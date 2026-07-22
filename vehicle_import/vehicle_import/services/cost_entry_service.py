from decimal import Decimal
from decimal import ROUND_HALF_UP

import frappe
from frappe import _

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

        company = self._get_company(
            reference_doctype,
            reference_name,
        )

        base_currency = frappe.db.get_value(
            "Company",
            company,
            "default_currency",
        )

        base_amount = (
            Decimal(
                str(foreign_amount)
            )
            *
            Decimal(
                str(exchange_rate)
            )
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

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

            "cost_entry_base_currency":
                base_currency,

            "cost_entry_base_amount":
                base_amount,

            "cost_entry_description":
                description,
        })

        doc.insert()
        doc.submit()
        
        return doc.name


    def _get_company(
        self,
        reference_doctype,
        reference_name,
    ):

        if reference_doctype == "Vehicle Holder":

            return frappe.db.get_value(
                "Vehicle Holder",
                reference_name,
                "vehicle_holder_company",
            )

        if reference_doctype == "Vehicle Holder Detail":

            parent = frappe.db.get_value(
                "Vehicle Holder Detail",
                reference_name,
                "parent",
            )

            return frappe.db.get_value(
                "Vehicle Holder",
                parent,
                "vehicle_holder_company",
            )

        raise frappe.ValidationError(
            f"Unsupported reference doctype: {reference_doctype}"
        )


    def add_delete_activity(
        self,
        holder,
        cost_entry,
    ):

        user = frappe.utils.get_fullname(frappe.session.user)

        frappe.get_doc({
            "doctype": "Comment",
            "comment_type": "Info",
            "reference_doctype": "Vehicle Holder",
            "reference_name": holder,
            "content": ("Deleted the Cost Entry {0}.").format(frappe.bold(cost_entry),),
        }).insert(ignore_permissions=True)


    def delete(
        self,
        cost_entry,
    ):
        doc = frappe.get_doc("Cost Entry", cost_entry)

        # Find holder
        if doc.cost_entry_reference_doctype == "Vehicle Holder":
            holder = doc.cost_entry_reference_name

        elif doc.cost_entry_reference_doctype == "Vehicle Holder Detail":
            holder = frappe.db.get_value(
                "Vehicle Holder Detail",
                doc.cost_entry_reference_name,
                "parent",
            )

        else:
            frappe.throw("Unsupported reference doctype")

        if doc.docstatus == 1:
            doc.cancel()

        doc.delete()

        self.add_delete_activity(
            holder=holder,
            cost_entry=cost_entry,
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


@frappe.whitelist()
def delete_cost_entry(
    cost_entry,
):
    return CostEntryService().delete(
        cost_entry=cost_entry,
    )