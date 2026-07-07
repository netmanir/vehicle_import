# Copyright (c) 2026, ACP and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.desk.search import validate_and_sanitize_search_inputs
from vehicle_import.vehicle_import.services.quotage_service import QuotageService

class Quotage(Document):

    def validate(self):
        # قبل از هر ذخیره (Save / Submit) اجرا می‌شود.
        self.validate_quotage_details()
        self._validate_duplicate_vins()
        self._validate_packing_list_quantities()

    def validate_quotage_details(self):
        # اعتبارسنجی‌های Quotage
        self._validate_duplicate_products()
        # self._validate_quantities()

    def _validate_duplicate_products(self):
        seen = set()
        for row in self.quotage_products:
            product = row.quotage_detail_product
            if product in seen:
                frappe.throw(
                    f"{_('Product')} {product} {_('is duplicated')}.",
                    title=_("Quotage Validation"),
                )
            seen.add(product)

    def _validate_duplicate_vins(self):
        seen = set()
        for row in self.quotage_packing_list:
            vin = row.quotage_packing_list_vin
            if not vin:
                continue
            if vin in seen:
                frappe.throw(
                    f"{vin} {_('is duplicated')}.",
                    title=_("Quotage Validation"),
                )
            seen.add(vin)

    def _validate_packing_list_quantities(self):
        assigned = {}
        for row in self.quotage_packing_list:
            detail = row.quotage_packing_list_quotage_detail
            if not detail:
                continue
            assigned[detail] = assigned.get(detail, 0) + 1

        for detail in self.quotage_products:
            qty = int(detail.quotage_detail_quantity or 0)
            count = assigned.get(detail.name, 0)
            if count > qty:
                frappe.throw(
                    f"{_('Product')} {detail.quotage_detail_product}: "
                    f"{_('Assigned VINs exceed quantity')}.",
                    title=_("Quotage Validation"),
                )

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
    product, qty = frappe.db.get_value(
        "Quotage Detail",
        name,
        [
            "quotage_detail_product",
            "quotage_detail_quantity",
        ],
    )

    return {
        "product": product,
        "qty": qty,
    }


@frappe.whitelist()
def _assign_vins(
    quotage,
    quotage_detail,
    vins,
):

    return QuotageService().assign_vins(
        quotage_name=quotage,
        quotage_detail_name=quotage_detail,
        vins_text=vins,
    )

