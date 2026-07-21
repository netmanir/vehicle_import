import re

import frappe
from frappe import _
from frappe.query_builder import DocType
from frappe.query_builder.functions import Count, Length


class VehicleHolderService:

    def assign_vins(
        self,
        holder_name,
        holder_detail_name,
        vins_text,
    ):

        errors = []

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
                    holder_name,
                    holder_detail_name,
                )

                self._update_vin(
                    holder_name,
                    holder_detail_name,
                    vin,
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
            "Vehicle Unit",
            {
                "vehicle_vin": vin,
            },
        ):
            raise frappe.ValidationError(
                _("Duplicate VIN.")
            )


    def _check_capacity(
        self,
        holder_name,
        holder_detail_name,
    ):

        VehicleHistory = DocType("Vehicle History")
        VehicleUnit = DocType("Vehicle Unit")

        remaining = (
            frappe.qb
            .from_(VehicleHistory)
            .inner_join(VehicleUnit)
            .on(
                VehicleHistory.vehicle_history_vehicle
                == VehicleUnit.name
            )
            .select(Count("*"))
            .where(
                (VehicleHistory.parent == holder_name)
                & (
                    VehicleHistory.vehicle_history_vehicle_holder_detail
                    == holder_detail_name
                )
                & (
                    VehicleUnit.vehicle_vin.isnull()
                    | (VehicleUnit.vehicle_vin == "")
                    | (Length(VehicleUnit.vehicle_vin) < 17)
                )
            )
        ).run()[0][0]

        if remaining <= 0:
            raise frappe.ValidationError(
                _("Unassigned VIN not found!")
            )

        return remaining


    def _update_vin(
        self,
        holder_name,
        holder_detail_name,
        vin,
    ):

        VehicleHistory = DocType("Vehicle History")
        VehicleUnit = DocType("Vehicle Unit")

        history = (
            frappe.qb
            .from_(VehicleHistory)
            .inner_join(VehicleUnit)
            .on(
                VehicleHistory.vehicle_history_vehicle
                == VehicleUnit.name
            )
            .select(
                VehicleHistory.vehicle_history_vehicle,
            )
            .where(
                (VehicleHistory.parent == holder_name)
                & (
                    VehicleHistory.vehicle_history_vehicle_holder_detail
                    == holder_detail_name
                )
                & (
                    VehicleUnit.vehicle_vin.isnull()
                    | (VehicleUnit.vehicle_vin == "")
                    | (Length(VehicleUnit.vehicle_vin) < 17)
                )
            )
            .orderby(VehicleHistory.idx)
            .limit(1)
        ).run(as_dict=True)

        if not history:
            raise frappe.ValidationError(
                _("Unassigned VIN not found!")
            )

        vehicle = frappe.get_doc(
            "Vehicle Unit",
            history[0].vehicle_history_vehicle,
        )

        vehicle.vehicle_vin = vin
        vehicle.save()

        return vehicle.name


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


    def cascade_cancel(self, holder):
        CostEntry = DocType("Cost Entry")
        VehicleHolderDetail = DocType("Vehicle Holder Detail")

        detail_names = (
            frappe.qb
            .from_(VehicleHolderDetail)
            .select(VehicleHolderDetail.name)
            .where(VehicleHolderDetail.parent == holder)
        ).run(pluck=True)

        cost_entries = (
            frappe.qb
            .from_(CostEntry)
            .select(CostEntry.name)
            .where(
                (CostEntry.docstatus == 1)
                &
                (
                    (
                        (CostEntry.cost_entry_reference_doctype == "Vehicle Holder")
                        &
                        (CostEntry.cost_entry_reference_name == holder)
                    )
                    |
                    (
                        (CostEntry.cost_entry_reference_doctype == "Vehicle Holder Detail")
                        &
                        (
                            CostEntry.cost_entry_reference_name.isin(
                                detail_names or [""]
                            )
                        )
                    )
                )
            )
        ).run(pluck=True)

        frappe.throw(f"Cost Entries: {cost_entries}")

        for name in cost_entries:
            frappe.get_doc("Cost Entry", name).cancel()

        frappe.get_doc("Vehicle Holder", holder).cancel()


    def do_submit(self, holder):
        frappe.get_doc("Vehicle Holder", holder).submit()


    @staticmethod
    def get_assigned_vin_counts(vehicle_holder):

        VehicleHistory = DocType("Vehicle History")
        VehicleUnit = DocType("Vehicle Unit")

        rows = (
            frappe.qb
            .from_(VehicleHistory)
            .inner_join(VehicleUnit)
            .on(VehicleHistory.vehicle_history_vehicle == VehicleUnit.name)
            .select(
                VehicleUnit.vehicle_item,
                Count("*").as_("count"),
            )
            .where(
                (VehicleHistory.parent == vehicle_holder)
                &
                (VehicleUnit.vehicle_vin != "")
                &
                (Length(VehicleUnit.vehicle_vin) == 17)
            )
            .groupby(
                VehicleUnit.vehicle_item
            )
        ).run(as_dict=True)

        return {
            row["vehicle_item"]: row["count"]
            for row in rows
        }