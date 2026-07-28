import frappe
from frappe.query_builder import DocType
from frappe.query_builder.functions import Cast

@frappe.whitelist()
def get_warehouses():

    Warehouse = DocType("Warehouse")
    WarehouseRule = DocType("Warehouse Rule")

    rows = (
        frappe.qb
        .from_(Warehouse)
        .left_join(WarehouseRule)
        .on(
            (Warehouse.name == WarehouseRule.warehouse)
            & (WarehouseRule.rule_type == "Display Order")
        )
        .select(
            Warehouse.name,
            WarehouseRule.rule_value.as_("display_order"),
        )
        .where(Warehouse.is_group == 0)
        .orderby(
            WarehouseRule.rule_value.isnull()
        )
        .orderby(
            Cast(WarehouseRule.rule_value, "SIGNED")
        )
        .orderby(
            Warehouse.lft
        )
    ).run(as_dict=True)

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

def as_bool(value):
    if isinstance(value, bool):
        return value

    return str(value).lower() in (
        "1",
        "true",
        "yes",
        "on"
    )