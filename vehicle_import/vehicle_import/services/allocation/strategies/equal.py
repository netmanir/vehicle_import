from decimal import Decimal
from decimal import ROUND_HALF_UP

from .base_strategy import BaseStrategy
from ..allocation_result import AllocationResult


class EqualStrategy(BaseStrategy):

    def allocate(
        self,
        context,
    ):

        result = AllocationResult()

        count = len(
            context.vehicles
        )

        if count == 0:
            return result

        foreign_total = Decimal(
            context.foreign_amount
        )

        base_total = Decimal(
            context.base_amount
        )

        foreign_share = (
            foreign_total / count
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

        base_share = (
            base_total / count
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

        foreign_sum = Decimal("0.00")
        base_sum = Decimal("0.00")

        for vehicle in context.vehicles[:-1]:

            result.add_row(

                vehicle=vehicle["vehicle"],

                currency=context.currency,
                foreign_amount=foreign_share,

                base_currency=context.base_currency,
                base_amount=base_share,

                remark=None,
            )

            foreign_sum += foreign_share
            base_sum += base_share

        last = context.vehicles[-1]

        result.add_row(

            vehicle=last["vehicle"],

            currency=context.currency,
            foreign_amount=foreign_total - foreign_sum,

            base_currency=context.base_currency,
            base_amount=base_total - base_sum,

            remark=None,
        )

        return result