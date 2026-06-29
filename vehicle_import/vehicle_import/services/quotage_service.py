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

        for row_no, raw_vin in enumerate(
            vins_text.splitlines(),
            start=1,
        ):

            if not raw_vin.strip():
                continue

            vin = self._normalize_vin(raw_vin)

            try:

                self._validate_vin(vin)

                self._check_duplicate(vin)

            except Exception as ex:

                errors.append(
                    _("{0} {1}: {2}").format(
                        _("Row"),
                        row_no,
                        str(ex),
                    )
                )

        if errors:

            frappe.throw("<br>".join(errors))

        frappe.msgprint(
            _("Validation completed successfully.")
        )

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
