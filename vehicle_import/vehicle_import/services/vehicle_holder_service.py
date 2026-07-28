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
        if not vin:
            raise frappe.ValidationError(
                _("VIN is empty.")
            )

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

        cost_entries = self.get_related_cost_entries(holder)

        for name in cost_entries:
            frappe.get_doc("Cost Entry", name).cancel()

        frappe.get_doc("Vehicle Holder", holder).cancel()


    def do_submit(self, holder):
        frappe.get_doc("Vehicle Holder", holder).submit()


    def validate_warehouse_rules(
        self,
        doc,
    ):
        old_doc = doc.get_doc_before_save()
        old_warehouse = (
            old_doc.vehicle_holder_warehouse
            if old_doc
            else None
        )
        new_warehouse = (
            doc.vehicle_holder_warehouse
        )

        #
        # Warehouse not changed
        #
        if old_warehouse == new_warehouse:
            return

        #
        # Validate Output Rules
        #
        if old_warehouse:
            self._validate_warehouse_output_rules(
                doc=doc,
                warehouse=old_warehouse,
            )

        #
        # Validate Input Rules
        #
        if new_warehouse:
            self._validate_warehouse_input_rules(
                doc=doc,
                warehouse=new_warehouse,
            )


    def _validate_warehouse_output_rules(
        self,
        doc,
        warehouse,
    ):
        rules = self._get_warehouse_rules(
            warehouse=warehouse,
            direction="Out",
        )
        if not rules:
            return
        
        if any(
            rule["rule_type"] == "Valid VIN"
            for rule in rules
        ):
            self._validate_vins(
                doc,
                warehouse=warehouse,
                direction="Output",
            )

        if any(
            rule["rule_type"] == "Cost Category"
            for rule in rules
        ):
            self._validate_required_cost_categories(
                doc=doc,
                rules=rules,
                warehouse=warehouse,
                direction="Output",
            )


    def _validate_warehouse_input_rules(
        self,
        doc,
        warehouse,
    ):
        rules = self._get_warehouse_rules(
            warehouse=warehouse,
            direction="In",
        )
        if not rules:
            return

        if any(
            rule["rule_type"] == "Valid VIN"
            for rule in rules
        ):
            self._validate_vins(
                doc,
                warehouse=warehouse,
                direction="Input",
            )

        if any(
            rule["rule_type"] == "Cost Category"
            for rule in rules
        ):
            self._validate_required_cost_categories(
                doc=doc,
                rules=rules,
                warehouse=warehouse,
                direction="Input",
            )


    def _get_warehouse_rules(
        self,
        warehouse,
        direction,
    ):
        WarehouseRule = DocType("Warehouse Rule")
        return (
            frappe.qb
            .from_(WarehouseRule)
            .select(
                WarehouseRule.rule_type,
                WarehouseRule.rule_value,
            )
            .where(
                (WarehouseRule.warehouse == warehouse)
                & (WarehouseRule.direction == direction)
            )
        ).run(as_dict=True)


    def _validate_required_cost_categories(
        self,
        doc,
        rules,
        warehouse,
        direction,
    ):
        required_categories = {
            rule["rule_value"]
            for rule in rules
            if rule["rule_type"] == "Cost Category"
        }
        if not required_categories:
            return
        
        holder_detail = [
            d.name
            for d in doc.vehicle_holder_detail
        ]

        CostEntry = DocType("Cost Entry")
        existing_categories = set(
            frappe.qb
            .from_(CostEntry)
            .select(CostEntry.cost_entry_cost_category)
            .where(
                (CostEntry.docstatus == 1)
                & (
                    (
                        (CostEntry.cost_entry_reference_doctype == "Vehicle Holder")
                        & (CostEntry.cost_entry_reference_name == doc.name)
                    )
                    |
                    (
                        (CostEntry.cost_entry_reference_doctype == "Vehicle Holder Detail")
                        & (CostEntry.cost_entry_reference_name.isin(holder_detail))
                    )
                )
            )
            .run(pluck="cost_entry_cost_category")
        )
        missing_categories = (
            required_categories
            - existing_categories
        )
        if missing_categories:
            CostCategory = DocType("Cost Category")
            category_titles = dict(
                frappe.qb
                .from_(CostCategory)
                .select(
                    CostCategory.name,
                    CostCategory.cost_category_title,
                )
                .where(
                    CostCategory.name.isin(missing_categories)
                )
                .run()
            )

            frappe.throw(
                _(
                    "{0} warehouse '{1}' is missing required Cost Categories: {2}"
                ).format(
                    _(direction),
                    warehouse,
                    ", ".join(
                        category_titles.get(name, name)
                        for name in sorted(missing_categories)
                    ),
                ),
                title=_("Warehouse Rule Validation"),
            )


    def _validate_vins(
        self,
        doc,
        warehouse,
        direction,
    ):
        for history in doc.vehicle_holder_history:
            if history.vehicle_history_vehicle:
                vehicle_unit = frappe.get_doc(
                    "Vehicle Unit",
                    history.vehicle_history_vehicle,
                )
                try:
                    self._validate_vin(
                        vehicle_unit.vehicle_vin,
                    )
                except frappe.ValidationError:
                    frappe.throw(
                        _(
                            "{0} warehouse '{1}' contains invalid VIN: {2}"
                        ).format(
                            _(direction),
                            warehouse,
                            vehicle_unit.vehicle_vin or _("(Empty)"),
                        ),
                        title=_("Warehouse Rule Validation")
                    )


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


    @staticmethod
    def get_related_cost_entries(holder):

        CostEntry = DocType("Cost Entry")
        VehicleHolderDetail = DocType("Vehicle Holder Detail")

        detail_names = (
            frappe.qb
            .from_(VehicleHolderDetail)
            .select(VehicleHolderDetail.name)
            .where(
                VehicleHolderDetail.parent == holder
            )
        ).run(pluck=True)

        return (
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