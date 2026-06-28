from decimal import Decimal

from .base import AllocationStrategy
from vehicle_import.vehicle_import.utils.allocation import round_and_balance


class EqualAllocationStrategy(AllocationStrategy):

    def allocate(self, cost_entry, vins):

        if not vins:
            return []

        count = len(vins)

        foreign_total = Decimal(str(cost_entry.cost_entry_foreign_amount))
        base_total = Decimal(str(cost_entry.cost_entry_base_amount))

        foreign_raw = [foreign_total / count] * count
        base_raw = [base_total / count] * count

        foreign_amounts = round_and_balance(
            foreign_total,
            foreign_raw,
        )

        base_amounts = round_and_balance(
            base_total,
            base_raw,
        )

        rows = []

        for vin, foreign, base in zip(
            vins,
            foreign_amounts,
            base_amounts,
        ):
            rows.append(
                {
                    "vin": vin,
                    "foreign_amount": foreign,
                    "base_amount": base,
                }
            )

        return rows