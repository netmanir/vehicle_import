import frappe


class StrategyFactory:

    def create(
        self,
        context,
    ):

        strategy_class = (
            context.allocation_rule
            .allocation_python_class
        )

        if not strategy_class:

            raise frappe.ValidationError(
                "Allocation Rule has no Python Class."
            )

        return frappe.get_attr(
            strategy_class
        )()