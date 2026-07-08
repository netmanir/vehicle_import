import frappe

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

