# Copyright (c) 2026, ACP and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.desk.search import validate_and_sanitize_search_inputs
from vehicle_import.vehicle_import.services.quotage_service import QuotageService

class Quotage(Document):
    pass


@frappe.whitelist()
@validate_and_sanitize_search_inputs
def quotage_detail_query(
    doctype,
    txt,
    searchfield,
    start,
    page_len,
    filters,
):

    return frappe.db.sql(
        """
        SELECT
            qd.name,
            CONCAT(
                qd.quotage_detail_product,
                ' (',
                qd.quotage_detail_quantity,
                ')'
            )
        FROM `tabQuotage Detail` qd
        WHERE
            qd.parent = %(parent)s
            AND (
                qd.quotage_detail_product LIKE %(txt)s
                OR qd.name LIKE %(txt)s
            )
        ORDER BY qd.idx
        LIMIT %(start)s, %(page_len)s
        """,
        {
            "parent": filters.get("parent"),
            "txt": f"%{txt}%",
            "start": start,
            "page_len": page_len,
        },
    )


@frappe.whitelist()
def get_quotage_detail(name):

    doc = frappe.get_doc("Quotage Detail", name)

    return {
        "product": doc.quotage_detail_product,
        "qty": doc.quotage_detail_quantity,
    }

@frappe.whitelist()
def assign_vins(
    quotage,
    quotage_detail,
    vins,
):

    return QuotageService().assign_vins(
        quotage_name=quotage,
        quotage_detail_name=quotage_detail,
        vins_text=vins,
    )
