from decimal import Decimal, ROUND_HALF_UP


PRECISION = Decimal("0.01")


def round_and_balance(total, raw_amounts):
    total = Decimal(str(total))

    rounded = []
    allocated = Decimal("0.00")

    for amount in raw_amounts[:-1]:
        value = Decimal(str(amount)).quantize(
            PRECISION,
            rounding=ROUND_HALF_UP,
        )

        rounded.append(value)
        allocated += value

    rounded.append(total - allocated)

    return rounded