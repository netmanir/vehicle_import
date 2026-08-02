import frappe
from frappe.query_builder import DocType
from frappe.query_builder.functions import Cast

def as_bool(value):
    if isinstance(value, bool):
        return value

    return str(value).lower() in (
        "1",
        "true",
        "yes",
        "on"
    )


@frappe.whitelist()
def get_warehouses():

    Warehouse = DocType("Warehouse")
    WarehouseRule = DocType("Warehouse Rule")

    #
    # Warehouses
    #
    warehouses = (
        frappe.qb
        .from_(Warehouse)
        .select(
            Warehouse.name,
            Warehouse.lft,
        )
        .where(Warehouse.is_group == 0)
        .orderby(Warehouse.lft)
    ).run(as_dict=True)

    #
    # Warehouse Rules
    #
    rules = (
        frappe.qb
        .from_(WarehouseRule)
        .select(
            WarehouseRule.warehouse,
            WarehouseRule.rule_type,
            WarehouseRule.direction,
            WarehouseRule.rule_value,
        )
    ).run(as_dict=True)

    #
    # Build Warehouse Map
    #
    warehouse_map = {}

    for warehouse in warehouses:
        warehouse_map[warehouse.name] = {
            "name": warehouse.name,
            "display_order": None,
            "valid_vin_required_for_input": False,
            "valid_vin_required_for_output": False,
            "input_cost_categories": [],
            "output_cost_categories": [],
            "lft": warehouse.lft,
        }

    #
    # Merge Rules
    #
    for rule in rules:

        warehouse = warehouse_map.get(
            rule.warehouse
        )

        if not warehouse:
            continue

        #
        # Display Order
        #
        if rule.rule_type == "Display Order":
            warehouse["display_order"] = (
                rule.rule_value
            )
            continue

        #
        # Valid VIN
        #
        if rule.rule_type == "Valid VIN":

            if rule.direction == "In":
                warehouse[
                    "valid_vin_required_for_input"
                ] = True

            elif rule.direction == "Out":
                warehouse[
                    "valid_vin_required_for_output"
                ] = True

            continue

        #
        # Cost Categories
        #
        if rule.rule_type == "Cost Category":

            if rule.direction == "In":
                warehouse[
                    "input_cost_categories"
                ].append(rule.rule_value)

            elif rule.direction == "Out":
                warehouse[
                    "output_cost_categories"
                ].append(rule.rule_value)

    #
    # Sort
    #
    rows = sorted(
        warehouse_map.values(),
        key=lambda row: (
            row["display_order"] is None,
            int(row["display_order"] or 0),
            row["lft"],
        ),
    )

    #
    # Cleanup
    #
    for row in rows:
        del row["lft"]

    return rows


@frappe.whitelist()
def get_warehouse_settings(warehouse):

    WarehouseRule = DocType("Warehouse Rule")
    CostCategory = DocType("Cost Category")

    rules = (
        frappe.qb
        .from_(WarehouseRule)
        .select(
            WarehouseRule.name,
            WarehouseRule.rule_type,
            WarehouseRule.direction,
            WarehouseRule.rule_value,
        )
        .where(WarehouseRule.warehouse == warehouse)
    ).run(as_dict=True)

    cost_categories = (
        frappe.qb
        .from_(CostCategory)
        .select(
            CostCategory.name,
            CostCategory.cost_category_title,
        )
        .orderby(CostCategory.cost_category_title)
    ).run(as_dict=True)

    return {
        "rules": rules,
        "cost_categories": cost_categories,
    }


@frappe.whitelist()
def save_warehouse_settings(
    warehouse,
    display_order,
    valid_vin_required_for_input,
    valid_vin_required_for_output,
    input_cost_categories,
    output_cost_categories
):
    import json

    if isinstance(input_cost_categories, str):
        input_cost_categories = json.loads(input_cost_categories)

    if isinstance(output_cost_categories, str):
        output_cost_categories = json.loads(output_cost_categories)

    frappe.db.delete(
        "Warehouse Rule",
        {
            "warehouse": warehouse
        }
    )

    def add_rule(rule_type, direction="", rule_value=""):
        doc = frappe.new_doc("Warehouse Rule")
        doc.warehouse = warehouse
        doc.rule_type = rule_type
        doc.direction = direction
        doc.rule_value = rule_value
        doc.insert()

    add_rule(
        "Display Order",
        rule_value=display_order
    )

    if as_bool(valid_vin_required_for_input):
        add_rule(
            "Valid VIN",
            direction="In"
        )

    if as_bool(valid_vin_required_for_output):
        add_rule(
            "Valid VIN",
            direction="Out"
        )

    for cost_category in input_cost_categories:
        add_rule(
            "Cost Category",
            direction="In",
            rule_value=cost_category
        )

    for cost_category in output_cost_categories:
        add_rule(
            "Cost Category",
            direction="Out",
            rule_value=cost_category
        )

    frappe.db.commit()
