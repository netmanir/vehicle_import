import re
import frappe
from frappe import _


class QuotageService:

    def assign_vins(
        self,
        quotage_name,
        quotage_detail_name,
        vins_text,
    ):

        errors = []

        product = frappe.db.get_value(
            "Quotage Detail",
            quotage_detail_name,
            "quotage_detail_product",
        )

        for row_no, raw_vin in enumerate(
            vins_text.splitlines(),
            start=1,
        ):

            raw_vin = raw_vin.strip()

            if not raw_vin:
                continue

            savepoint = self._create_savepoint()

            try:

                vin = self._normalize_vin(raw_vin)

                self._validate_vin(vin)

                self._check_duplicate(vin)

                self._check_capacity(
                    quotage_name,
                    quotage_detail_name,
                )

                vin_name = self._create_vin(
                    vin,
                    product,
                )

                self._create_packing_list_row(
                    quotage_name,
                    quotage_detail_name,
                    vin_name,
                )

                self._commit()

            except Exception as ex:

                self._rollback_savepoint(savepoint)

                errors.append(
                    _("{0} {1}: {2}").format(
                        _("Row"),
                        row_no,
                        str(ex),
                    )
                )

        return {
            "success": len(errors) == 0,
            "errors": errors,
        }


    def _normalize_vin(
        self,
        vin,
    ):
        vin = re.sub(
            r"[^A-Za-z0-9]",
            "",
            vin,
        )

        return vin.upper()


    def _validate_vin(
        self,
        vin,
    ):
        if len(vin) != 17:

            raise frappe.ValidationError(
                _("Invalid VIN.")
            )

        if not vin.startswith("VGA"):

            raise frappe.ValidationError(
                _("Invalid VIN.")
            )


    def _check_duplicate(
        self,
        vin,
    ):
        if frappe.db.exists(
            "VINs",
            {
                "vin": vin,
            },
        ):

            raise frappe.ValidationError(
                _("Duplicate VIN.")
            )


    def _check_capacity(
        self,
        quotage_name,
        quotage_detail_name,
    ):

        quantity = frappe.db.get_value(
            "Quotage Detail",
            quotage_detail_name,
            "quotage_detail_quantity",
        ) or 0

        quantity = int(quantity)

        assigned = frappe.db.count(
            "Quotage Packing List",
            {
                "parent": quotage_name,
                "quotage_packing_list_quotage_detail": quotage_detail_name,
            },
        )

        if assigned >= quantity:
            raise frappe.ValidationError(
                _("Packing List is already complete.")
            )

        return {
            "quantity": quantity,
            "assigned": assigned,
            "remaining": quantity - assigned,
        }


    def _create_vin(
        self,
        vin,
        product,
    ):
        doc = frappe.get_doc(
            {
                "doctype": "VINs",
                "vin": vin,
                "product": product,
            }
        )

        doc.insert()

        return doc.name


    def _create_packing_list_row(
        self,
        quotage_name,
        quotage_detail_name,
        vin_name,
    ):

        quotage = frappe.get_doc(
            "Quotage",
            quotage_name,
        )

        row = quotage.append(
            "quotage_packing_list",
            {
                "quotage_packing_list_quotage_detail": quotage_detail_name,
                "quotage_packing_list_vin": vin_name,
            },
        )

        quotage.save()

        return row.name


    def _create_savepoint(
        self,
    ):

        savepoint = "assign_vin"

        frappe.db.savepoint(savepoint)

        return savepoint



    def _rollback_savepoint(
        self,
        savepoint,
    ):

        frappe.db.rollback(save_point=savepoint)


    def _commit(
        self,
    ):

        frappe.db.commit()


